"""FastAPI transport using the frozen JSON Schemas without coercion or private errors."""

import json
import logging
import os
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jsonschema import ValidationError

from .ai import DialogueAdapter
from .content import Content, ContentError
from .engine import Engine
from .errors import GameError
from .schemas import CONTRACTS, ROOT, validate

LOGGER = logging.getLogger(__name__)


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


async def request_body(request, schema):
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > 16384:
            raise GameError("REQUEST_TOO_LARGE", 413, "Request exceeds 16 KiB.")
    try:
        body = json.loads(
            raw,
            object_pairs_hook=reject_duplicates,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
        )
        validate(schema, body)
        return body
    except (ValueError, UnicodeError, ValidationError) as exc:
        raise GameError("VALIDATION_ERROR", 422, "Request does not match contract 1.0.0.") from exc


def create_app(content=None, content_path=None, adapter=None, allowed_origins=None):
    app = FastAPI(title="Haunted AI", version="1.0.0", openapi_url="/openapi.json")
    provider = adapter or DialogueAdapter()
    try:
        loaded = (
            Content(content)
            if content is not None
            else Content.load(
                content_path
                or os.getenv("HAUNTED_CONTENT_PATH", str(ROOT / "game-data/blackthorn_manor.json"))
            )
        )
        engine = Engine(loaded, provider)
    except ContentError:
        engine = None
        LOGGER.warning(
            "Content readiness failed; check the private content file with the validator."
        )
    app.state.engine = engine
    origins = (
        allowed_origins
        if allowed_origins is not None
        else ["http://localhost:5173", "http://127.0.0.1:5173"]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
        allow_credentials=False,
    )

    @app.middleware("http")
    async def mutation_boundary(request, call_next):
        # CORS alone protects response access; it cannot prevent simple POST side effects.
        if request.method == "POST":
            origin = request.headers.get("origin")
            same_origin = f"{request.url.scheme}://{request.url.netloc}"
            media = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
            if (
                origin is not None and origin not in origins and origin != same_origin
            ) or media != "application/json":
                error = GameError(
                    "VALIDATION_ERROR", 422, "Mutation requires an approved origin and JSON media."
                )
                return JSONResponse(error.response(None), status_code=422)
        return await call_next(request)

    @app.get("/api.schema.json", include_in_schema=False)
    async def public_api_schema():
        # Exact allowlist: never route a filename supplied by the caller to the filesystem.
        return json.loads((CONTRACTS / "api.schema.json").read_text())

    # The published interface is the reviewed contract, not inferred permissive dict bodies.
    app.openapi = lambda: json.loads((CONTRACTS / "openapi.json").read_text())

    @app.exception_handler(GameError)
    async def game_error(request, exc):
        return JSONResponse(
            exc.response(getattr(request.state, "request_id", None)), status_code=exc.status
        )

    @app.exception_handler(Exception)
    async def internal_error(request, exc):
        # Deliberately omit raw exception/prompt/body values from logs and responses.
        LOGGER.error("Atomic request failed: %s", getattr(request.state, "request_id", None))
        return JSONResponse(
            GameError("INTERNAL_ERROR", 500, "Request failed without committing changes.").response(
                getattr(request.state, "request_id", None)
            ),
            status_code=500,
        )

    def ready():
        if engine is None:
            raise GameError("CONTENT_UNAVAILABLE", 503, "Game content is unavailable.")
        return engine

    def session_id(value):
        try:
            if str(UUID(value)) != value.lower():
                raise ValueError("Noncanonical UUID format")
        except ValueError as exc:
            raise GameError("VALIDATION_ERROR", 422, "Invalid session identifier.") from exc
        return value

    @app.get("/api/v1/health")
    async def health():
        return {
            "contract_version": "1.0.0",
            "status": "ready" if engine and len(engine.sessions) < 8 else "not_ready",
            "content_version": engine.content.data["content_version"] if engine else None,
            "ai": {"provider": "ollama", "model": provider.model, "status": "unknown"},
        }

    @app.post("/api/v1/sessions", status_code=201)
    async def create(request: Request):
        body = await request_body(request, "CreateRequest")
        request.state.request_id = body["request_id"]
        return await ready().create(body)

    @app.get("/api/v1/sessions/{id}")
    async def get(id: str):
        return await ready().get(session_id(id))

    @app.post("/api/v1/sessions/{id}/actions")
    async def act(id: str, request: Request):
        body = await request_body(request, "ActionRequest")
        request.state.request_id = body["request_id"]
        return await ready().mutate(session_id(id), body)

    @app.post("/api/v1/sessions/{id}/restart")
    async def restart(id: str, request: Request):
        body = await request_body(request, "RestartRequest")
        request.state.request_id = body["request_id"]
        return await ready().mutate(session_id(id), body, restart=True)

    return app


app = create_app()
