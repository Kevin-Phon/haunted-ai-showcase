"""Offline contract validation: never retrieve schemas from the network."""

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = ROOT / "contracts" / "v1"
SCHEMAS = {
    name: json.loads((CONTRACTS / name).read_text())
    for name in ("api.schema.json", "game-data.schema.json")
}
REGISTRY = Registry().with_resources(
    (s["$id"], Resource.from_contents(s)) for s in SCHEMAS.values()
)


def validator(name):
    schema = (
        SCHEMAS["game-data.schema.json"]
        if name == "Content"
        else {"$ref": SCHEMAS["api.schema.json"]["$id"] + "#/$defs/" + name}
    )
    return Draft202012Validator(schema, registry=REGISTRY, format_checker=FormatChecker())


def validate(name, value):
    validator(name).validate(value)
