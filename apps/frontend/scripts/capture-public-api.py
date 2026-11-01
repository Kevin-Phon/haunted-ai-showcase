"""Optional F02 in-process audit; run with the existing backend test environment.

Only public API projections are written. No server, model, source edit or solution lookup.
"""
import argparse
import json
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from haunted_backend.app import create_app
from haunted_backend.schemas import validate

parser = argparse.ArgumentParser()
parser.add_argument("--content", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
receipts = {}
with TestClient(create_app(content_path=args.content)) as client:
    assert client.get("/api/v1/health").json()["status"] == "ready"
    result = client.post("/api/v1/sessions", json={"request_id": str(uuid4()), "content_id": "blackthorn_manor", "mode": "demo"})
    assert result.status_code == 201, result.text
    validate("SessionResponse", result.json())
    state = result.json()["state"]
    receipts["initial"] = state
    sid = state["session_id"]

    def action(payload):
        global state
        result = client.post("/api/v1/sessions/" + sid + "/actions", json={"request_id": str(uuid4()), "expected_revision": state["revision"], "action": payload})
        assert result.status_code == 200, result.text
        validate("ActionResponse", result.json())
        state = result.json()["state"]
        return result.json()

    action({"type": "navigate", "room_id": "library"})
    receipts["library"] = state
    action({"type": "inspect", "hotspot_id": state["scene"]["hotspots"][0]["id"]})
    receipts["inspected"] = state
    permitted = [(h, i) for h in state["scene"]["hotspots"] for i in h["interactions"] if i["enabled"]]
    assert permitted
    h, i = permitted[0]
    action({"type": "interact_object", "object_id": h["object_id"], "operation": i["operation"]})
    receipts["interacted"] = state
    ghost = next(g for g in state["ghosts"] if g["available"])
    reply = action({"type": "talk", "ghost_id": ghost["id"], "message": "What do you remember about that night?", "tone": "respectful", "presented_evidence_ids": []})
    assert reply["dialogue_turn"]["ai"]["source"] == "demo"
    receipts["dialogue"] = state
    action({"type": "navigate", "room_id": "entrance_hall"})
    action({"type": "navigate", "room_id": "study"})
    for hotspot in list(state["scene"]["hotspots"]):
        action({"type": "inspect", "hotspot_id": hotspot["id"]})
    assert state["evidence"] and state["accusation"]["eligible"]
    receipts["theory"] = state
    # This tests one public hypothesis, not the private rubric or a full solution.
    choice = state["accusation"]["options"][0]
    action({"type": "accuse", "claims": [{"claim_id": choice["id"], "evidence_ids": [state["evidence"][0]["id"]]}]})
    assert state["ending"]
    receipts["terminal"] = state
    prior = state["revision"]
    result = client.post("/api/v1/sessions/" + sid + "/restart", json={"request_id": str(uuid4()), "expected_revision": prior})
    assert result.status_code == 200, result.text
    validate("SessionResponse", result.json())
    receipts["restarted"] = result.json()["state"]
    assert receipts["restarted"]["revision"] == prior + 1 and not receipts["restarted"]["evidence"]
args.output.write_text(json.dumps(receipts))
print("PASS: schema-valid in-process canonical API smoke; one hypothesis produced " + receipts["terminal"]["ending"]["id"] + ". Public snapshots: " + str(args.output))
print("Not a browser/network/full-mystery/live-inference test; no servers started or changed.")
