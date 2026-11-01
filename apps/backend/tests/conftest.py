"""Private synthetic fixture, not canonical story content or live AI evidence."""

import copy
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


def predicate(**kw):
    return (
        dict(all_evidence=[], all_insights=[], all_puzzles=[], object_states=[], **kw)
        if not kw
        else {**predicate(), **kw}
    )


def effect(kind, target, state=None):
    return {"kind": kind, "target_id": target, "state": state}


@pytest.fixture
def content():
    examples = ROOT / "contracts/v1/examples"
    letter = json.loads((examples / "letter-available.response.json").read_text())["state"][
        "puzzles"
    ][0]["presentation"]
    machine = json.loads((examples / "calibration-available.response.json").read_text())["state"][
        "puzzles"
    ][0]["presentation"]
    rooms = ["entrance_hall", "library", "study", "laboratory", "grand_ballroom", "hidden_passage"]
    evidence = [
        "damaged_notebook",
        "torn_letter",
        "servant_log",
        "memory_crystal",
        "maintenance_record",
        "gathering_photograph",
        "sealed_report",
        "final_recording",
    ]
    d = {
        "format_version": "1.0.0",
        "content_version": "1.0.0",
        "content_id": "blackthorn_manor",
        "initial_room_id": "entrance_hall",
        "rooms": [],
        "objects": [],
        "evidence": [],
        "puzzles": [],
        "deductions": [],
        "ghosts": [],
        "knowledge": [],
        "rules": [],
        "claims": [],
        "endings": [],
        "timeline": [],
        "events": [],
        "assets": [],
        "attributions": [
            {
                "id": "original",
                "origin": "original",
                "creator": "Backend synthetic test author",
                "source_url": None,
                "license": "test fixture",
                "license_url": None,
                "notes": "Not final story",
                "generation_tool": None,
            }
        ],
    }
    for r in rooms:
        d["rooms"].append(
            {
                "id": r,
                "title": r,
                "description": "Public synthetic scene",
                "initially_unlocked": r != "hidden_passage",
                "adjacent_room_ids": [x for x in rooms if x != r],
                "layers": [],
                "ambient_audio_asset_id": None,
                "canvas": {"width": 1600, "height": 900},
            }
        )
    for i, e in enumerate(evidence):
        d["evidence"].append(
            {
                "id": e,
                "room_id": "entrance_hall",
                "title": e,
                "description": "Public collected clue",
                "asset_id": None,
                "annotations": [],
                "attribution_id": "original",
            }
        )
        obj = {
            "id": "object_" + e,
            "room_id": "entrance_hall",
            "initial_state": "closed",
            "initially_visible": True,
            "description": "Public object",
            "hotspot": {
                "id": "hotspot_" + e,
                "object_id": "object_" + e,
                "label": e,
                "focus_order": i,
                "bounds": {"x": 0, "y": 0, "width": 0.1, "height": 0.1},
                "interactions": [],
            },
        }
        d["objects"].append(obj)
        d["rules"].append(
            {
                "id": "discover_" + e,
                "trigger": {
                    "type": "inspect",
                    "target_id": obj["hotspot"]["id"],
                    "operation": None,
                },
                "requires": predicate(),
                "effects": [effect("grant_evidence", e)],
                "once": True,
            }
        )
    d["objects"].append(
        {
            "id": "secret_drawer",
            "room_id": "library",
            "initial_state": "closed",
            "initially_visible": False,
            "description": "Hidden drawer",
            "hotspot": {
                "id": "secret_hotspot",
                "object_id": "secret_drawer",
                "label": "Secret",
                "focus_order": 0,
                "bounds": {"x": 0, "y": 0, "width": 0.1, "height": 0.1},
                "interactions": [
                    {
                        "operation": "open",
                        "label": "Open",
                        "enabled": True,
                        "disabled_reason": None,
                    },
                    {
                        "operation": "close",
                        "label": "Close",
                        "enabled": True,
                        "disabled_reason": None,
                    },
                ],
            },
        }
    )
    d["rules"].append(
        {
            "id": "drawer_open",
            "trigger": {
                "type": "interact_object",
                "target_id": "secret_drawer",
                "operation": "open",
            },
            "requires": predicate(all_evidence=["torn_letter"]),
            "effects": [effect("set_object_state", "secret_drawer", "open")],
            "once": False,
        }
    )
    d["rules"].append(
        {
            "id": "drawer_close",
            "trigger": {
                "type": "interact_object",
                "target_id": "secret_drawer",
                "operation": "close",
            },
            "requires": predicate(),
            "effects": [effect("set_object_state", "secret_drawer", "closed")],
            "once": False,
        }
    )
    d["puzzles"] = [
        {
            "id": "letter_reconstruction",
            "room_id": "entrance_hall",
            "requires": predicate(),
            "presentation": letter,
            "solution": {
                "placements": [
                    {"slot_id": "letter_slot_" + str(i), "piece_id": "letter_piece_" + p}
                    for i, p in enumerate("dcba", 1)
                ]
            },
            "effects": [effect("reveal_object", "secret_drawer"), effect("emit_event", "whisper")],
        },
        {
            "id": "machine_calibration",
            "room_id": "entrance_hall",
            "requires": predicate(all_evidence=["damaged_notebook"]),
            "presentation": machine,
            "solution": {"power_level": 2, "phase": "violet", "stabilizer": "engaged"},
            "effects": [],
        },
    ]
    pairs = [
        ("deduction_hidden_route", ["servant_log", "gathering_photograph"]),
        ("deduction_protective_sabotage", ["torn_letter", "sealed_report"]),
        ("deduction_partial_restart", ["servant_log", "maintenance_record"]),
        ("deduction_fatal_instability", ["damaged_notebook", "final_recording"]),
    ]
    for id, pair in pairs:
        d["deductions"].append(
            {
                "id": id,
                "evidence_ids": pair,
                "title": id,
                "description": "Earned insight",
                "requires": predicate(),
                "effects": [effect("unlock_room", "hidden_passage")]
                if id == "deduction_hidden_route"
                else [],
            }
        )
    for ghost in ["eleanor", "thomas", "clara"]:
        d["ghosts"].append(
            {
                "id": ghost,
                "room_id": "entrance_hall",
                "name": ghost,
                "personality": "Guarded",
                "initial_trust": 30,
                "initial_suspicion": 10,
                "portrait_asset_id": None,
                "relevant_evidence_ids": ["torn_letter"],
                "generic_fallback": "I cannot yet speak of it.",
            }
        )
        d["knowledge"].append(
            {
                "id": ghost + "_secret",
                "ghost_id": ghost,
                "kind": "observation",
                "text": "HIDDEN_CANARY_" + ghost,
                "requires": predicate(all_evidence=["torn_letter"]),
                "minimum_trust": None,
                "maximum_suspicion": None,
                "critical": True,
                "supersedes_ids": [],
                "fallback_text": "The letter permits this disclosure.",
            }
        )
    claims = [
        (
            "eleanor_action",
            "eleanor_disconnected_stabilizer",
            ["torn_letter", "maintenance_record"],
        ),
        ("eleanor_motive", "eleanor_protected_clara", ["torn_letter", "sealed_report"]),
        ("thomas_action", "thomas_restored_power", ["servant_log", "maintenance_record"]),
        ("thomas_motive", "thomas_protected_reputation", ["maintenance_record"]),
        ("cause", "unstable_run_killed_elias", ["damaged_notebook", "final_recording"]),
    ]
    for group, id, support in claims:
        d["claims"].extend(
            [
                {
                    "id": id,
                    "group": group,
                    "label": "Neutral hypothesis",
                    "correct": True,
                    "support_evidence_ids": support,
                },
                {
                    "id": "wrong_" + group,
                    "group": group,
                    "label": "Alternative",
                    "correct": False,
                    "support_evidence_ids": [],
                },
            ]
        )
    for id in ["truth_revealed", "partial_truth", "false_accusation"]:
        d["endings"].append({"id": id, "title": id, "explanation": "Authored synthetic ending"})
    d["events"] = [{"id": "whisper", "cue_id": "letter_whisper", "summary": "A readable whisper"}]
    return copy.deepcopy(d)


@pytest.fixture
def client(content):
    from fastapi.testclient import TestClient

    from haunted_backend.app import create_app

    return TestClient(create_app(content=content))
