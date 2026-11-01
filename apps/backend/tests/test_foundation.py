import copy
import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from haunted_backend.app import create_app
from haunted_backend.content import Content, ContentError


def uid():
    return str(uuid4())


def start(client, mode="demo"):
    body = {"request_id": uid(), "content_id": "blackthorn_manor", "mode": mode}
    r = client.post("/api/v1/sessions", json=body)
    assert r.status_code == 201, r.text
    return r.json()["state"]


def action(client, state, payload, request_id=None):
    return client.post(
        "/api/v1/sessions/" + state["session_id"] + "/actions",
        json={
            "request_id": request_id or uid(),
            "expected_revision": state["revision"],
            "action": payload,
        },
    )


def inspect(client, state, evidence):
    r = action(client, state, {"type": "inspect", "hotspot_id": "hotspot_" + evidence})
    assert r.status_code == 200, r.text
    return r.json()["state"]


def test_private_projection_and_closed_validation(client):
    s = start(client)
    assert "HIDDEN_CANARY" not in json.dumps(s)
    assert "secret_drawer" not in json.dumps(s)
    assert s["revision"] == 0 and s["evidence"] == []
    bad = action(client, s, {"type": "navigate", "room_id": "library", "injected": True})
    assert bad.status_code == 422
    assert bad.json()["error"]["code"] == "VALIDATION_ERROR"
    assert (
        action(
            client,
            s,
            {"type": "interact_object", "object_id": "secret_drawer", "operation": "open"},
        ).status_code
        == 409
    )
    assert action(client, s, {"type": "navigate", "room_id": "hidden_passage"}).status_code == 409
    assert client.get("/api/v1/sessions/" + s["session_id"]).json()["state"]["revision"] == 0


def test_retry_revision_restart_and_creation_idempotency(client):
    body = {"request_id": uid(), "content_id": "blackthorn_manor", "mode": "demo"}
    first = client.post("/api/v1/sessions", json=body)
    assert client.post("/api/v1/sessions", json=body).json() == first.json()
    s = first.json()["state"]
    key = uid()
    p = {"type": "inspect", "hotspot_id": "hotspot_servant_log"}
    r = action(client, s, p, key)
    assert r.status_code == 200
    assert action(client, s, p, key).json() == r.json()
    assert action(client, s, p).json()["error"]["code"] == "REVISION_CONFLICT"
    assert (
        action(client, s, {"type": "navigate", "room_id": "study"}, key).json()["error"]["code"]
        == "IDEMPOTENCY_CONFLICT"
    )
    later = r.json()["state"]
    restarted = client.post(
        "/api/v1/sessions/" + s["session_id"] + "/restart",
        json={"request_id": uid(), "expected_revision": later["revision"]},
    )
    assert restarted.status_code == 200
    assert restarted.json()["state"]["revision"] == 2
    assert restarted.json()["state"]["evidence"] == []
    assert action(client, s, p, key).json() == r.json()
    assert client.get("/api/v1/sessions/" + s["session_id"]).json()["state"]["revision"] == 2


def test_puzzles_deductions_objects_and_events(client, content):
    s = start(client)
    wrong = {
        "type": "submit_puzzle",
        "puzzle_id": "letter_reconstruction",
        "solution": {
            "placements": [
                {"slot_id": "letter_slot_" + str(i), "piece_id": "letter_piece_" + p}
                for i, p in enumerate("abcd", 1)
            ]
        },
    }
    r = action(client, s, wrong)
    assert r.json()["outcome"] == "incorrect"
    s = r.json()["state"]
    malformed = copy.deepcopy(wrong)
    malformed["solution"]["placements"][0]["piece_id"] = "letter_piece_b"
    assert action(client, s, malformed).status_code == 422
    good = {
        "type": "submit_puzzle",
        "puzzle_id": "letter_reconstruction",
        "solution": content["puzzles"][0]["solution"],
    }
    r = action(client, s, good)
    assert len(r.json()["new_events"]) == 1
    s = r.json()["state"]
    r = action(client, s, good)
    assert r.json()["outcome"] == "no_change" and r.json()["new_events"] == []
    s = r.json()["state"]
    s = inspect(client, s, "torn_letter")
    r = action(client, s, {"type": "navigate", "room_id": "library"})
    s = r.json()["state"]
    assert any(o["id"] == "secret_drawer" for o in s["scene"]["objects"])
    r = action(
        client, s, {"type": "interact_object", "object_id": "secret_drawer", "operation": "open"}
    )
    assert r.status_code == 200
    assert (
        next(o for o in r.json()["state"]["scene"]["objects"] if o["id"] == "secret_drawer")[
            "state"
        ]
        == "open"
    )
    s = action(client, r.json()["state"], {"type": "navigate", "room_id": "entrance_hall"}).json()[
        "state"
    ]
    s = inspect(client, s, "servant_log")
    s = inspect(client, s, "gathering_photograph")
    r = action(
        client,
        s,
        {"type": "connect_evidence", "evidence_ids": ["gathering_photograph", "servant_log"]},
    )
    s = r.json()["state"]
    assert [i["id"] for i in s["insights"]] == ["deduction_hidden_route"]
    assert next(x for x in s["rooms"] if x["id"] == "hidden_passage")["unlocked"]
    r = action(
        client, s, {"type": "connect_evidence", "evidence_ids": ["servant_log", "torn_letter"]}
    )
    assert r.json()["outcome"] == "incorrect"


@pytest.mark.parametrize("ending", ["truth_revealed", "partial_truth", "false_accusation"])
def test_deterministic_endings_and_terminal_restart(client, content, ending):
    s = start(client)
    for e in content["evidence"]:
        s = inspect(client, s, e["id"])
    if ending == "truth_revealed":
        for p in content["puzzles"]:
            s = action(
                client,
                s,
                {"type": "submit_puzzle", "puzzle_id": p["id"], "solution": p["solution"]},
            ).json()["state"]
        for d in content["deductions"]:
            s = action(
                client, s, {"type": "connect_evidence", "evidence_ids": d["evidence_ids"]}
            ).json()["state"]
    cs = [
        {"claim_id": c["id"], "evidence_ids": c["support_evidence_ids"]}
        for c in content["claims"]
        if c["correct"]
    ]
    claims = (
        cs
        if ending == "truth_revealed"
        else cs[:1]
        if ending == "partial_truth"
        else [{"claim_id": "wrong_cause", "evidence_ids": []}]
    )
    r = action(client, s, {"type": "accuse", "claims": claims})
    assert r.status_code == 200, r.text
    s = r.json()["state"]
    assert s["ending"]["id"] == ending
    assert s["available_actions"] == []
    assert (
        action(client, s, {"type": "navigate", "room_id": "study"}).json()["error"]["code"]
        == "SESSION_ENDED"
    )
    r = client.post(
        "/api/v1/sessions/" + s["session_id"] + "/restart",
        json={"request_id": uid(), "expected_revision": s["revision"]},
    )
    assert r.json()["state"]["ending"] is None and r.json()["state"]["events"] == []


@pytest.mark.parametrize("mutation", ["duplicate", "unknown_ref", "bounds", "cycle", "bad_path"])
def test_content_rejects_invalid_semantic_data(content, mutation):
    if mutation == "duplicate":
        content["rooms"][1]["id"] = "entrance_hall"
    if mutation == "unknown_ref":
        content["rules"][0]["effects"][0]["target_id"] = "missing"
    if mutation == "bounds":
        content["objects"][0]["hotspot"]["bounds"]["width"] = 0
    if mutation == "cycle":
        d = content["deductions"][0]
        content["rules"].append(
            {
                "id": "cycle",
                "trigger": {"type": "insight_earned", "target_id": d["id"], "operation": None},
                "requires": content["puzzles"][0]["requires"],
                "effects": [{"kind": "grant_insight", "target_id": d["id"], "state": None}],
                "once": False,
            }
        )
    if mutation == "bad_path":
        content["assets"] = [
            {
                "id": "evil",
                "kind": "image",
                "src": "../secret.json",
                "alt": "x",
                "attribution_id": "original",
                "width": 1600,
                "height": 900,
            }
        ]
    with pytest.raises(ContentError):
        Content(content)


def test_missing_content_is_not_ready():
    c = TestClient(create_app(content_path="/definitely/missing/private-content.json"))
    assert c.get("/api/v1/health").json()["status"] == "not_ready"
    r = c.post(
        "/api/v1/sessions",
        json={"request_id": uid(), "content_id": "blackthorn_manor", "mode": "demo"},
    )
    assert r.status_code == 503 and r.json()["error"]["code"] == "CONTENT_UNAVAILABLE"


def test_path_identifier_uses_contract_uuid_format(client):
    r = client.get("/api/v1/sessions/12345678123412341234123456789abc")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"
