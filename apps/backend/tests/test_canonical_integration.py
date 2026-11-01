"""Opt-in API integration against real private Data content (read-only).

HAUNTED_CANONICAL_CONTENT must identify the canonical JSON package. Provider-failure
transports below are explicitly synthetic; no successful live inference is implied.
"""

import json
import os
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from haunted_backend.ai import DialogueAdapter
from haunted_backend.app import create_app
from haunted_backend.schemas import validate

CONTENT_PATH = os.getenv("HAUNTED_CANONICAL_CONTENT")
pytestmark = pytest.mark.skipif(
    not CONTENT_PATH, reason="Set HAUNTED_CANONICAL_CONTENT to run canonical integration"
)

EVIDENCE = {
    "damaged_notebook",
    "torn_letter",
    "servant_log",
    "memory_crystal",
    "maintenance_record",
    "gathering_photograph",
    "sealed_report",
    "final_recording",
}
ROOMS = {"entrance_hall", "library", "study", "laboratory", "grand_ballroom", "hidden_passage"}
INSIGHTS = {
    "deduction_hidden_route",
    "deduction_protective_sabotage",
    "deduction_partial_restart",
    "deduction_fatal_instability",
}
LETTER = {
    "placements": [
        {"slot_id": f"letter_slot_{i}", "piece_id": f"letter_piece_{piece}"}
        for i, piece in enumerate("cadb", 1)
    ]
}
CLAIMS = [
    {
        "claim_id": "eleanor_disconnected_stabilizer",
        "evidence_ids": ["torn_letter", "maintenance_record"],
    },
    {"claim_id": "eleanor_protected_clara", "evidence_ids": ["torn_letter", "sealed_report"]},
    {"claim_id": "thomas_restored_power", "evidence_ids": ["servant_log", "maintenance_record"]},
    {"claim_id": "thomas_protected_reputation", "evidence_ids": ["maintenance_record"]},
    {
        "claim_id": "unstable_run_killed_elias",
        "evidence_ids": ["damaged_notebook", "final_recording"],
    },
]


class Journey:
    def __init__(self, mode="demo", adapter=None):
        self.client = TestClient(create_app(content_path=CONTENT_PATH, adapter=adapter))
        assert self.client.get("/api/v1/health").json()["status"] == "ready"
        response = self.client.post(
            "/api/v1/sessions",
            json={"request_id": str(uuid4()), "content_id": "blackthorn_manor", "mode": mode},
        )
        assert response.status_code == 201, response.text
        validate("SessionResponse", response.json())
        self.state = response.json()["state"]
        self.visited = {self.state["current_room_id"]}
        self.turns = []
        self.actions = 0

    def act(self, payload, outcome=None):
        r = self.client.post(
            f"/api/v1/sessions/{self.state['session_id']}/actions",
            json={
                "request_id": str(uuid4()),
                "expected_revision": self.state["revision"],
                "action": payload,
            },
        )
        assert r.status_code == 200, r.text
        result = r.json()
        validate("ActionResponse", result)
        assert result["state"]["revision"] == self.state["revision"] + 1
        if outcome is not None:
            assert result["outcome"] == outcome
        self.state = result["state"]
        self.visited.add(self.state["current_room_id"])
        if result["dialogue_turn"]:
            self.turns.append(result["dialogue_turn"])
        self.actions += 1
        return result

    def go(self, room):
        self.act({"type": "navigate", "room_id": room})

    def inspect(self, hotspot):
        self.act({"type": "inspect", "hotspot_id": hotspot})

    def open(self, object_id):
        self.act({"type": "interact_object", "object_id": object_id, "operation": "open"})

    def letter(self):
        self.open("library_letter_drawer")
        assert any(p["id"] == "letter_reconstruction" for p in self.state["puzzles"])
        self.act(
            {"type": "submit_puzzle", "puzzle_id": "letter_reconstruction", "solution": LETTER},
            "applied",
        )

    def connect(self, evidence):
        self.act({"type": "connect_evidence", "evidence_ids": evidence}, "applied")

    def talk(self, ghost, evidence=()):
        return self.act(
            {
                "type": "talk",
                "ghost_id": ghost,
                "message": "What do these records tell us about the midnight experiment?",
                "tone": "respectful",
                "presented_evidence_ids": list(evidence),
            }
        )

    def restart(self):
        old = self.state
        request = {"request_id": str(uuid4()), "expected_revision": old["revision"]}
        r = self.client.post(f"/api/v1/sessions/{old['session_id']}/restart", json=request)
        assert r.status_code == 200, r.text
        validate("SessionResponse", r.json())
        self.state = r.json()["state"]
        assert self.state["session_id"] == old["session_id"]
        assert self.state["revision"] == old["revision"] + 1
        assert self.state["current_room_id"] == "entrance_hall"
        assert self.state["phase"] == "investigating" and self.state["ending"] is None
        for field in ("evidence", "insights", "dialogue", "events"):
            assert self.state[field] == []
        assert all(g["trust"] == 30 and g["suspicion"] == 10 for g in self.state["ghosts"])
        assert all(p["status"] != "solved" for p in self.state["puzzles"])
        assert not next(r for r in self.state["rooms"] if r["id"] == "hidden_passage")["unlocked"]
        assert (
            self.client.post(f"/api/v1/sessions/{old['session_id']}/restart", json=request).json()
            == r.json()
        )


@pytest.mark.parametrize("ending", ["truth_revealed", "partial_truth", "false_accusation"])
def test_canonical_endings_via_api_and_restart(ending):
    j = Journey()
    if ending == "false_accusation":
        j.go("study")
        j.inspect("hs_study_notebook")
        claims = [{"claim_id": "ordinary_accident", "evidence_ids": ["damaged_notebook"]}]
    elif ending == "partial_truth":
        j.go("library")
        j.letter()
        j.go("entrance_hall")
        j.go("study")
        j.open("study_desk_compartment")
        claims = CLAIMS[:1]
    else:
        j.go("study")
        j.inspect("hs_study_notebook")
        j.inspect("hs_study_servant_log")
        j.go("entrance_hall")
        j.go("grand_ballroom")
        j.inspect("hs_ballroom_photograph")
        j.talk("thomas", ["servant_log", "gathering_photograph"])
        j.connect(["servant_log", "gathering_photograph"])
        j.go("entrance_hall")
        j.open("hall_wall_panel")
        j.go("hidden_passage")
        j.open("passage_report_box")
        j.inspect("hs_passage_report_box")
        j.go("entrance_hall")
        j.go("library")
        j.letter()
        j.talk("eleanor", ["torn_letter", "sealed_report"])
        j.go("entrance_hall")
        j.go("study")
        j.open("study_desk_compartment")
        j.go("entrance_hall")
        j.go("laboratory")
        j.inspect("hs_lab_crystal_cradle")
        j.inspect("hs_lab_memory_machine")
        j.act(
            {
                "type": "submit_puzzle",
                "puzzle_id": "machine_calibration",
                "solution": {"power_level": 0, "phase": "amber", "stabilizer": "bypass"},
            },
            "incorrect",
        )
        j.act(
            {
                "type": "submit_puzzle",
                "puzzle_id": "machine_calibration",
                "solution": {"power_level": 2, "phase": "cyan", "stabilizer": "engaged"},
            },
            "applied",
        )
        j.talk("clara", ["damaged_notebook", "sealed_report", "final_recording"])
        j.connect(["torn_letter", "sealed_report"])
        j.connect(["servant_log", "maintenance_record"])
        j.connect(["damaged_notebook", "final_recording"])
        assert j.visited == ROOMS
        assert {e["id"] for e in j.state["evidence"]} == EVIDENCE
        assert {i["id"] for i in j.state["insights"]} == INSIGHTS
        assert {p["id"] for p in j.state["puzzles"] if p["status"] == "solved"} == {
            "letter_reconstruction",
            "machine_calibration",
        }
        assert j.state["progress"]["earned"] == j.state["progress"]["total"] == 14
        assert len(j.state["events"]) == 4 and len({e["id"] for e in j.state["events"]}) == 4
        assert {t["ghost_id"] for t in j.turns} == {"eleanor", "thomas", "clara"}
        assert all(t["ai"]["source"] == "demo" for t in j.turns)
        claims = CLAIMS
    j.act({"type": "accuse", "claims": claims}, "applied")
    assert j.state["ending"]["id"] == ending and j.state["phase"] == "ended"
    summary = {
        "ending": ending,
        "actions_to_ending": j.actions,
        "visited_rooms": len(j.visited),
        "evidence": len(j.state["evidence"]),
        "puzzles_solved": sum(p["status"] == "solved" for p in j.state["puzzles"]),
        "insights": len(j.state["insights"]),
        "dialogue_sources": [t["ai"]["source"] for t in j.turns],
    }
    j.restart()
    print("CANONICAL_RECEIPT", json.dumps(summary, sort_keys=True), "restart=passed")


@pytest.mark.parametrize(
    "ghost, room", [("eleanor", "library"), ("thomas", "grand_ballroom"), ("clara", "laboratory")]
)
@pytest.mark.parametrize("failure", ["timeout", "unavailable", "invalid_output"])
def test_canonical_ai_failure_paths_via_adapter_and_api(failure, ghost, room):
    calls = []

    def provider(request):
        calls.append(request)
        if failure == "timeout":
            raise httpx.ReadTimeout("Simulated B02 provider timeout")
        if failure == "unavailable":
            raise httpx.ConnectError("Simulated B02 provider unavailable")
        return httpx.Response(200, json={"response": "not valid JSON"})

    adapter = DialogueAdapter(
        model="qwen-b02-fixture-only", transport=httpx.MockTransport(provider)
    )
    j = Journey("live", adapter)
    j.go(room)
    result = j.talk(ghost)
    turn = result["dialogue_turn"]
    assert (
        turn["response_text"]
        and turn["ai"]["source"] == "fallback"
        and turn["ai"]["reason"] == failure
    )
    assert all(t["ai"]["source"] != "live" for t in j.turns)
    assert j.state["evidence"] == [] and j.state["insights"] == []
    assert len(calls) == 1
    j.restart()
    print(
        "CANONICAL_FAILURE_RECEIPT",
        ghost,
        failure,
        "fallback=passed; provider=SIMULATED; actual_inference=NOT_RUN; restart=passed",
    )
