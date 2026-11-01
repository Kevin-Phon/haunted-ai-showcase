import asyncio
import json

import httpx
import pytest

from haunted_backend.ai import DialogueAdapter

CONTEXT = {
    "personality": "Guarded",
    "emotion": "guarded",
    "message": "What did you see?",
    "history": [],
    "facts": [
        {"id": "permitted", "text": "The door was open.", "fallback_text": "The door was open."}
    ],
    "fallback": "I cannot speak yet.",
}


@pytest.mark.parametrize(
    "failure",
    ["timeout", "unavailable", "invalid_output", "provider_error", "oversize", "paraphrase"],
)
def test_provider_failure_and_secret_prose_cannot_escape(failure):
    def respond(request):
        if failure == "timeout":
            raise httpx.ReadTimeout("private stack")
        if failure == "unavailable":
            raise httpx.ConnectError("private stack")
        if failure == "provider_error":
            return httpx.Response(500, text="private provider error")
        if failure == "oversize":
            return httpx.Response(200, content=b"x" * 17000)
        output = (
            "not json"
            if failure == "invalid_output"
            else json.dumps(
                {
                    "utterance": "Eleanor secretly sabotaged everything.",
                    "cited_fact_ids": ["permitted"],
                }
            )
        )
        return httpx.Response(200, json={"response": output})

    adapter = DialogueAdapter(model="qwen-test", transport=httpx.MockTransport(respond))
    text, ai = asyncio.run(adapter.respond(CONTEXT, "live"))
    assert ai["source"] == "fallback" and ai["reason"] is not None
    assert "sabotaged" not in text and "private stack" not in text


def test_valid_live_selection_renders_only_authored_facts():
    def respond(request):
        body = json.loads(request.content)
        assert "tools" not in body
        return httpx.Response(
            200,
            json={
                "response": json.dumps(
                    {"utterance": "The air grows cold.", "cited_fact_ids": ["permitted"]}
                )
            },
        )

    adapter = DialogueAdapter(model="qwen-test", transport=httpx.MockTransport(respond))
    text, ai = asyncio.run(adapter.respond(CONTEXT, "live"))
    assert text == "The air grows cold. The door was open."
    assert ai == {"source": "live", "provider": "ollama", "model": "qwen-test", "reason": None}


def test_demo_does_not_connect_to_provider():
    def unexpected(request):
        raise AssertionError("Demo attempted provider")

    adapter = DialogueAdapter(model="qwen-test", transport=httpx.MockTransport(unexpected))
    text, ai = asyncio.run(adapter.respond(CONTEXT, "demo"))
    assert text == "The door was open." and ai["source"] == "demo"


def test_adapter_total_deadline_bounds_a_stalled_provider():
    async def stall(request):
        await asyncio.sleep(0.1)
        return httpx.Response(200, json={})

    adapter = DialogueAdapter(
        model="qwen-test", transport=httpx.MockTransport(stall), deadline=0.01
    )
    _, ai = asyncio.run(adapter.respond(CONTEXT, "live"))
    assert ai["reason"] == "timeout"


def test_provider_receives_schema_for_allowed_reactions_and_fact_ids():
    def provider(request):
        body = json.loads(request.content)
        assert isinstance(body["format"], dict), (
            "Unconstrained JSON mode allows invalid reaction prose"
        )
        output = body["format"]
        assert output["additionalProperties"] is False
        assert output["properties"]["cited_fact_ids"]["items"]["enum"] == ["permitted"]
        assert "The air grows cold." in output["properties"]["utterance"]["enum"]
        return httpx.Response(
            200,
            json={
                "response": json.dumps(
                    {"utterance": "The air grows cold.", "cited_fact_ids": ["permitted"]}
                )
            },
        )

    adapter = DialogueAdapter(model="qwen-test", transport=httpx.MockTransport(provider))
    text, ai = asyncio.run(adapter.respond(CONTEXT, "live"))
    assert ai["source"] == "live" and "The door was open." in text
