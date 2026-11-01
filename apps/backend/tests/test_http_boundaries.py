import json
from urllib.parse import urldefrag, urljoin

import httpx
from fastapi.testclient import TestClient
from test_foundation import start, uid

from haunted_backend.ai import DialogueAdapter
from haunted_backend.app import create_app
from haunted_backend.schemas import validate


def test_untrusted_origin_and_non_json_media_cannot_exhaust_capacity(content):
    c = TestClient(create_app(content=content))
    for _ in range(8):
        body = {"request_id": uid(), "content_id": "blackthorn_manor", "mode": "demo"}
        r = c.post(
            "/api/v1/sessions",
            content=json.dumps(body),
            headers={"Origin": "https://untrusted.example", "Content-Type": "text/plain"},
        )
        assert r.status_code == 422
        validate("Error", r.json())
        assert (
            r.json()["error"]["code"] == "VALIDATION_ERROR"
            and r.json()["error"]["request_id"] is None
        )
    assert c.get("/api/v1/health").json()["status"] == "ready"
    assert len(c.app.state.engine.sessions) == 0
    # Disallowed origin is also rejected when the body claims to be JSON.
    r = c.post("/api/v1/sessions", json=body, headers={"Origin": "https://untrusted.example"})
    assert r.status_code == 422
    # No-Origin local tools remain allowed, but must use JSON media.
    assert (
        c.post(
            "/api/v1/sessions", content=json.dumps(body), headers={"Content-Type": "text/plain"}
        ).status_code
        == 422
    )
    assert c.post("/api/v1/sessions", json=body).status_code == 201


def test_origin_guard_rejects_action_and_restart_before_ai_or_state_changes(content):
    calls = []

    def provider(request):
        calls.append(request)
        return httpx.Response(
            200, json={"response": json.dumps({"utterance": "I remember.", "cited_fact_ids": []})}
        )

    c = TestClient(
        create_app(
            content=content,
            adapter=DialogueAdapter(
                model="qwen-guard-test", transport=httpx.MockTransport(provider)
            ),
        )
    )
    state = start(c, "live")
    sid = state["session_id"]
    action = {
        "request_id": uid(),
        "expected_revision": 0,
        "action": {
            "type": "talk",
            "ghost_id": "eleanor",
            "message": "Where were you?",
            "tone": "respectful",
            "presented_evidence_ids": [],
        },
    }
    for suffix, body in [
        ("actions", action),
        ("restart", {"request_id": uid(), "expected_revision": 0}),
    ]:
        assert (
            c.post(
                f"/api/v1/sessions/{sid}/{suffix}",
                json=body,
                headers={"Origin": "https://untrusted.example"},
            ).status_code
            == 422
        )
        assert (
            c.post(
                f"/api/v1/sessions/{sid}/{suffix}",
                content=json.dumps(body),
                headers={"Content-Type": "text/plain"},
            ).status_code
            == 422
        )
    assert calls == []
    assert c.get(f"/api/v1/sessions/{sid}").json()["state"] == state


def test_allowed_local_frontend_and_same_origin_json_requests_work(content):
    c = TestClient(create_app(content=content))
    for origin in ["http://localhost:5173", "http://127.0.0.1:5173", "http://testserver"]:
        r = c.post(
            "/api/v1/sessions",
            json={"request_id": uid(), "content_id": "blackthorn_manor", "mode": "demo"},
            headers={"Origin": origin, "Content-Type": "application/json; charset=utf-8"},
        )
        assert r.status_code == 201


def test_all_served_public_openapi_refs_resolve_and_private_files_stay_hidden(client):
    document = client.get("/openapi.json").json()
    found = []

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "$ref" and not v.startswith("#"):
                    found.append(v)
                else:
                    walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(document)
    assert found
    for ref in found:
        path, fragment = urldefrag(urljoin("/openapi.json", ref))
        r = client.get(path)
        assert r.status_code == 200, ref
        target = r.json()
        for part in fragment.removeprefix("/").split("/"):
            target = target[part.replace("~1", "/").replace("~0", "~")]
        assert isinstance(target, dict)
    assert "game-data.schema.json" not in client.get("/api.schema.json").text
    for private in [
        "/game-data.schema.json",
        "/contracts/v1/game-data.schema.json",
        "/game-data/blackthorn_manor.json",
    ]:
        assert client.get(private).status_code == 404
