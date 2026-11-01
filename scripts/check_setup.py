"""Verify setup artifacts. Full JSON Schema validation is opt-in, never implied."""
from pathlib import Path
import argparse
import copy
import json
from urllib.parse import urldefrag

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "v1"

def resolve_ref(base, reference):
    filename, fragment = urldefrag(reference)
    path = (base.parent / filename).resolve() if filename else base
    assert path.is_relative_to(CONTRACT), f"Out-of-contract reference: {reference}"
    value = json.loads(path.read_text())
    for part in fragment.lstrip("/").split("/") if fragment else []:
        value = value[part.replace("~1", "/").replace("~0", "~")]
    return value

def walk_refs(node, base):
    if isinstance(node, dict):
        if "$ref" in node:
            resolve_ref(base, node["$ref"])
        if node.get("type") == "object":
            assert node.get("additionalProperties") is False
            assert set(node.get("required", [])) <= set(node.get("properties", {}))
        for value in node.values():
            walk_refs(value, base)
    elif isinstance(node, list):
        for value in node:
            walk_refs(value, base)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-schema", action="store_true")
    args = parser.parse_args()
    required = ["README.md", "AGENTS.md", "docs/architecture.md", "docs/game-design.md", "docs/progress.md", "docs/integration.md", "docs/submission.md", "docs/development.md", "contracts/README.md", "contracts/v1/semantics.md"]
    for name in required:
        assert (ROOT / name).read_text().strip(), name
    schemas = {}
    for name in ["api.schema.json", "game-data.schema.json"]:
        path = CONTRACT / name
        schema = json.loads(path.read_text())
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        walk_refs(schema, path)
        schemas[name] = schema
    api = schemas["api.schema.json"]["$defs"]
    assert len(api["Action"]["oneOf"]) == 8
    specification = json.loads((CONTRACT / "openapi.json").read_text())
    assert specification["openapi"] == "3.1.0" and len(specification["paths"]) == 5
    walk_refs(specification, CONTRACT / "openapi.json")
    index = json.loads((CONTRACT / "fixture-index.json").read_text())
    for fixture in index["fixtures"]:
        resolve_ref(CONTRACT / "fixture-index.json", fixture["schema"])
        value = json.loads((CONTRACT / fixture["path"]).read_text())
        assert isinstance(value, dict)
        if "state" in value:
            state = value["state"]
            assert state["scene"]["room_id"] == state["current_room_id"], fixture["path"]
            earned = len(state["evidence"]) + len(state["insights"]) + sum(p["status"] == "solved" for p in state["puzzles"])
            assert state["progress"]["earned"] == earned, fixture["path"]
            assert {e["id"] for e in value.get("new_events", [])} <= {e["id"] for e in state["events"]}
            if state["ending"] and state["ending"]["id"] == "truth_revealed":
                assert earned == 14 and len(state["ending"]["supported_claim_ids"]) == 5
    public = json.loads((CONTRACT / "examples/session.response.json").read_text())
    state = public["state"]
    assert len(state["rooms"]) == 6 and state["revision"] == 0
    assert not state["evidence"] and state["ending"] is None
    assert state["progress"]["total"] == 14
    for forbidden in ["solution", "canonical_timeline", "support_evidence_ids", "correct"]:
        assert f'"{forbidden}"' not in json.dumps(public), forbidden
    original = json.loads((CONTRACT / "examples/letter-solved.response.json").read_text())
    repeated = json.loads((CONTRACT / "examples/letter-duplicate.response.json").read_text())
    assert original["request_id"] != repeated["request_id"]
    assert repeated["state"]["revision"] > original["state"]["revision"]
    assert (CONTRACT / "examples/event-new.response.json").read_bytes() == (CONTRACT / "examples/event-replay.response.json").read_bytes()
    if args.full_schema:
        from jsonschema import Draft202012Validator, FormatChecker
        from referencing import Registry, Resource
        registry = Registry().with_resources((schema["$id"], Resource.from_contents(schema)) for schema in schemas.values())
        for schema in schemas.values():
            Draft202012Validator.check_schema(schema)
        for fixture in index["fixtures"]:
            schema = {"$ref": schemas[fixture["schema"].split("#")[0]]["$id"] + "#" + fixture["schema"].split("#")[1]}
            Draft202012Validator(schema, registry=registry, format_checker=FormatChecker()).validate(json.loads((CONTRACT / fixture["path"]).read_text()))
        action_schema = {"$ref": schemas["api.schema.json"]["$id"] + "#/$defs/ActionRequest"}
        validator = Draft202012Validator(action_schema, registry=registry, format_checker=FormatChecker())
        request = json.loads((CONTRACT / "examples/action.request.json").read_text())
        negative = []
        bad = copy.deepcopy(request); bad["expected_revision"] = -1; negative.append(bad)
        bad = copy.deepcopy(request); bad["action"]["type"] = "change_authoritative_state"; negative.append(bad)
        bad = copy.deepcopy(request); bad["action"]["secret_solution"] = True; negative.append(bad)
        bad = copy.deepcopy(request); bad["request_id"] = "not-a-uuid"; negative.append(bad)
        bad = copy.deepcopy(request); bad["action"] = {"type":"connect_evidence", "evidence_ids":["servant_log", "servant_log"]}; negative.append(bad)
        assert all(not validator.is_valid(value) for value in negative)
        ai_validator = Draft202012Validator({"$ref": schemas["api.schema.json"]["$id"] + "#/$defs/AI"}, registry=registry)
        assert not ai_validator.is_valid({"source":"live", "provider":None, "model":None, "reason":None})
        assert not ai_validator.is_valid({"source":"demo", "provider":"ollama", "model":"mock", "reason":None})
        assert not ai_validator.is_valid({"source":"fallback", "provider":"ollama", "model":"mock", "reason":None})
        print("PASS: full JSON Schema metaschema/indexed example validation and invalid-action/AI-metadata rejection checks")
    else:
        print("NOT RUN: full JSON Schema validation (use --full-schema with jsonschema installed)")
    print(f"PASS: setup documents, schema references, closed object declarations, endpoints and {len(index['fixtures'])} fixture structures")

if __name__ == "__main__":
    main()
