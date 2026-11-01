"""Optional global presentation assets must not widen private asset disclosure."""

import pytest
from fastapi.testclient import TestClient
from test_foundation import start

from haunted_backend.app import create_app
from haunted_backend.schemas import validate


@pytest.mark.parametrize("variant", ["audio", "absent", "wrong_kind"])
def test_optional_discovery_sound_projection_is_exact_allowlist(content, variant):
    content["assets"] = [
        {
            "id": "unrevealed_story_image",
            "kind": "image",
            "src": "private-story-image.png",
            "alt": "Unrevealed story image",
            "attribution_id": "original",
            "width": 1600,
            "height": 900,
        },
        {
            "id": "other_unreferenced_audio",
            "kind": "audio",
            "src": "unreferenced.wav",
            "alt": "Unreferenced sound",
            "attribution_id": "original",
            "width": None,
            "height": None,
        },
    ]
    if variant != "absent":
        content["assets"].append(
            {
                "id": "audio_discovery",
                "kind": "audio" if variant == "audio" else "image",
                "src": "discovery.wav" if variant == "audio" else "misnamed-image.png",
                "alt": "Optional discovery sound",
                "attribution_id": "original",
                "width": None if variant == "audio" else 1600,
                "height": None if variant == "audio" else 900,
            }
        )
    client = TestClient(create_app(content=content))
    state = start(client)
    validate("State", state)
    assert [a["id"] for a in state["assets"]] == (["audio_discovery"] if variant == "audio" else [])
    if variant == "audio":
        assert state["assets"][0]["kind"] == "audio"
        assert state["assets"][0]["src"] == "discovery.wav"
    assert state["evidence"] == [] and state["insights"] == []
