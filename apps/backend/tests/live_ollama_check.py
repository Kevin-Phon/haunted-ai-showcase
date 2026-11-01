"""Explicit, opt-in real-provider check. No model installation, pull or timeout changes.

Run as a script with --content, --model and --receipt. Real model text/labels and
measured times are kept separate from the deliberate malformed-output simulation.
"""

import argparse
import copy
import hashlib
import json
import os
import time
from pathlib import Path

import httpx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--content", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()
    os.environ["HAUNTED_CANONICAL_CONTENT"] = args.content
    from test_canonical_integration import Journey

    from haunted_backend.ai import DialogueAdapter

    adapter = DialogueAdapter(model=args.model)
    j = Journey("live", adapter)
    # Prepare canonical evidence without making provider calls or judging the ending.
    j.go("study")
    j.inspect("hs_study_notebook")
    j.inspect("hs_study_servant_log")
    j.go("entrance_hall")
    j.go("grand_ballroom")
    j.inspect("hs_ballroom_photograph")
    j.connect(["servant_log", "gathering_photograph"])
    j.go("entrance_hall")
    j.open("hall_wall_panel")
    j.go("hidden_passage")
    j.open("passage_report_box")
    j.inspect("hs_passage_report_box")
    j.go("entrance_hall")
    j.go("library")
    j.letter()
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
            "solution": {"power_level": 2, "phase": "cyan", "stabilizer": "engaged"},
        }
    )
    rows = []
    with httpx.Client(base_url=adapter.base_url, timeout=10, trust_env=False) as api:
        version = api.get("/api/version").json()
        inventory = api.get("/api/tags").json()
        before = api.get("/api/ps").json()
        for ghost, room, evidence in [
            ("eleanor", "library", ["torn_letter", "sealed_report"]),
            ("thomas", "grand_ballroom", ["servant_log", "maintenance_record"]),
            ("clara", "laboratory", ["damaged_notebook", "sealed_report", "final_recording"]),
        ]:
            j.go("entrance_hall")
            j.go(room)
            for attempt in range(2):
                authoritative = {
                    k: copy.deepcopy(j.state[k])
                    for k in [
                        "evidence",
                        "insights",
                        "puzzles",
                        "events",
                        "ending",
                        "current_room_id",
                        "progress",
                    ]
                }
                started = time.monotonic()
                result = j.talk(ghost, evidence)
                elapsed = time.monotonic() - started
                assert all(j.state[k] == v for k, v in authoritative.items()), (
                    "Dialogue changed authoritative progression"
                )
                turn = result["dialogue_turn"]
                row = {
                    "ghost": ghost,
                    "attempt": attempt + 1,
                    "elapsed_seconds": round(elapsed, 3),
                    "ai": turn["ai"],
                    "response_text": turn["response_text"],
                    "authoritative_progression_unchanged": True,
                }
                rows.append(row)
                print("REAL_PROVIDER_RECEIPT", json.dumps(row), flush=True)
        after = api.get("/api/ps").json()

    def malformed(request):
        return httpx.Response(200, json={"response": "intentional malformed-output simulation"})

    fake = Journey(
        "live",
        DialogueAdapter(
            model="qwen-malformed-fixture-only", transport=httpx.MockTransport(malformed)
        ),
    )
    fake.go("library")
    bad = fake.talk("eleanor")["dialogue_turn"]
    assert bad["ai"]["source"] == "fallback" and bad["ai"]["reason"] == "invalid_output"
    receipt = {
        "contract_version": "1.0.0",
        "model": args.model,
        "runtime": version,
        "inventory": inventory,
        "loaded_before": before,
        "loaded_after": after,
        "content_sha256": hashlib.sha256(Path(args.content).read_bytes()).hexdigest(),
        "real_provider_turns": rows,
        "malformed_output_case": {"provider": "SIMULATED", "ai": bad["ai"]},
        "all_ghosts_have_successful_live_response": all(
            any(r["ghost"] == ghost and r["ai"]["source"] == "live" for r in rows)
            for ghost in ["eleanor", "thomas", "clara"]
        ),
    }
    path = Path(args.receipt)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2) + "\n")
    print("RECEIPT_PATH", str(path), flush=True)
    if not receipt["all_ghosts_have_successful_live_response"]:
        raise SystemExit("At least one ghost has no actual validated live response; see receipt.")


if __name__ == "__main__":
    main()
