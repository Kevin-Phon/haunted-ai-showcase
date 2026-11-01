# Haunted AI backend

FastAPI runs the authoritative rules for **Haunted AI: Whispers of Blackthorn Manor**. It loads the canonical mystery, validates player actions and returns only the state the player may see. Local Ollama/Qwen provides constrained, evidence-aware dialogue. API/data format **1.0.0** remains the interface contract; the supplied content version is **1.0.1**.

Run a single backend worker. Sessions are held in memory; there is no database, account system or durable save. This setup is intended for local play.

## Fresh setup

Use Python **3.11+**, with `venv` and pip available. Run every command below from the repository root. The code expects `apps/`, `game-data/` and `contracts/` to retain their repository layout.

```sh
python3 -m venv apps/backend/.venv
apps/backend/.venv/bin/python -m pip install -r apps/backend/requirements.lock
apps/backend/.venv/bin/python -m pip install --no-deps -e apps/backend
```

[requirements.lock](requirements.lock) pins the reviewed development environment, including test and lint tools. [pyproject.toml](pyproject.toml) declares runtime dependencies and Python requirements. The editable install uses isolated setuptools build tooling. Initial dependency installation requires network access; running the installed game/model locally does not require a paid AI service or an external API key.

## Start the game API

```sh
HAUNTED_CONTENT_PATH="$PWD/game-data/blackthorn_manor.json" \
HAUNTED_OLLAMA_MODEL=qwen2.5:1.5b \
HAUNTED_OLLAMA_URL=http://127.0.0.1:11434 \
apps/backend/.venv/bin/python -m uvicorn haunted_backend.app:app \
  --host 127.0.0.1 --port 8000 --workers 1
```

Configuration:

| Variable | Meaning |
| --- | --- |
| `HAUNTED_CONTENT_PATH` | Optional trusted canonical JSON path. Defaults to `game-data/blackthorn_manor.json` in this repository. |
| `HAUNTED_OLLAMA_MODEL` | Exact installed model tag used for live attempts. Missing configuration produces labeled fallback. |
| `HAUNTED_OLLAMA_URL` | Local model-service URL; defaults to `http://127.0.0.1:11434`. |

[.env.example](.env.example) is a template. The backend **does not automatically load `.env` files**; export the variables or supply them on the launch command as above. Keep secrets out of source control, although this local provider configuration requires no external API key.

The canonical JSON is backend-only runtime input. It includes fictional puzzle answers, scoring support and hidden character knowledge. Those may be inspected in source, but must never be copied into the browser bundle or served as web assets. Missing or invalid content reports health `not_ready` and rejects session creation with `CONTENT_UNAVAILABLE`; no synthetic mystery is silently substituted.

The frontend normally connects from `http://localhost:5173` or `http://127.0.0.1:5173`. Mutating requests require JSON media and an approved or actual same-origin request. Local JSON tools without an Origin header remain supported. The application factory supports an explicit local-origin allowlist for integration.

## API and session behavior

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v1/health` | Content/capacity readiness and configured model information. |
| POST | `/api/v1/sessions` | Create a `demo` or `live` investigation. |
| GET | `/api/v1/sessions/{session_id}` | Retrieve the latest public session snapshot. |
| POST | `/api/v1/sessions/{session_id}/actions` | Submit a typed, revision-checked player action. |
| POST | `/api/v1/sessions/{session_id}/restart` | Reset gameplay in the same session. |

Running-server documentation is at `/docs`, with `/openapi.json` and the resolvable public `/api.schema.json`. Source references: [OpenAPI](../../contracts/v1/openapi.json), [public API schema](../../contracts/v1/api.schema.json) and [shared contract semantics](../../contracts/v1/semantics.md). The server does not expose the private game-data schema or canonical content file.

A process retains at most **8 sessions** and each session accepts at most **500 mutations, including restart**, for that process lifetime. There is no automatic eviction. Exact cached request replays return their original result before revision/cap checks, without repeating rewards or model calls. Stale revisions or conflicting request-ID reuse are rejected.

Restart clears clues, puzzles, relationships, conversation, events and ending; it keeps the session ID, increments revision and retains retry records and the lifetime mutation allowance. It **does not reset the 500-mutation cap**. After `SESSION_ACTION_LIMIT`, explicitly create a new session. If all 8 process-lifetime slots are occupied, a backend process restart is needed to release capacity and will lose every in-memory session. Browser refresh can reconnect while the process/session survives; `SESSION_NOT_FOUND` requires an explicit new investigation.

Room gates, object transitions, puzzle solutions, clue-pair deductions, trust/suspicion changes and all three endings are deterministic backend rules. Effects run atomically through a FIFO semantic-event queue; repeated accepted rewards/events are idempotent. The model cannot award evidence or decide an ending. Partial puzzle manipulation and board positions are frontend presentation state.

## Local Ollama and Qwen

Install and start Ollama using the [official download](https://ollama.com/download) and [official documentation](https://docs.ollama.com/). The tested configuration used **Ollama 0.40.13** and **qwen2.5:1.5b**, Q4_K_M. The [official model page](https://ollama.com/library/qwen2.5:1.5b) lists a download of about 986 MB; resident memory and runtime overhead are additional.

If Ollama is not already serving locally, run `ollama serve` in a separate terminal. Download the model only if it is not already installed:

```sh
ollama pull qwen2.5:1.5b
ollama list
```

Keep model weights in Ollama's model store, outside the repository. The application does not install/start Ollama or download models automatically. Start the backend with the exact installed tag in `HAUNTED_OLLAMA_MODEL`.

For dialogue, the backend selects ghost-specific facts that current evidence and relationship rules permit, removes superseded beliefs and bounds recent history. Ollama runs Qwen against that permitted subset. The model returns allowed fact IDs and a reaction from a fixed vocabulary under a JSON-schema output constraint. The backend validates the result again and renders factual clauses from authored character text. Unrestricted model prose and model-proposed state changes are not accepted.

Labels have distinct meanings:

- **live:** an actual provider response was received and validated.
- **demo:** authored dialogue, with no model call.
- **fallback:** an attempted live turn could not use the provider result, with timeout/unavailable/invalid-output/provider-error metadata. Missing model configuration also produces labeled fallback.

The provider deadline is **10 seconds**, with no automatic request retry. Requests/history/output are bounded. Health reports model inference status `unknown`; a ready backend or configured model is not proof of successful inference. Earlier real checks produced validated replies for all three ghosts, but cold-start timeouts and invalid-output fallbacks also occurred. Responses can be broad or repetitive; no latency, unrestricted-conversation or general secrecy guarantee is implied.

## Tests and validation

The reviewed implementation has **56 backend tests** and **20 Data tests**. They are separate suites; simulated provider responses are not live inference. Run them after fresh setup:

```sh
HAUNTED_CANONICAL_CONTENT="$PWD/game-data/blackthorn_manor.json" \
apps/backend/.venv/bin/python -m pytest apps/backend/tests -q
apps/backend/.venv/bin/ruff check apps/backend
apps/backend/.venv/bin/ruff format --check apps/backend
apps/backend/.venv/bin/python -m unittest discover -s game-data/tests -v
apps/backend/.venv/bin/python game-data/validate_content.py
```

`HAUNTED_CANONICAL_CONTENT` enables the opt-in canonical API cases, including the complete mystery, all three endings, restart and labeled failure handling. Without it, those cases are skipped. Other backend tests use explicitly synthetic fixtures. Data tests independently check schema/references/reachability. The locked FastAPI/Starlette TestClient currently emits an upstream httpx deprecation warning; do not mistake the warning or simulated fixtures for model results.

A separate opt-in check makes six real model calls through actual in-process FastAPI routes and the production adapter. It requires the already running Ollama service and installed model. Choose a new local receipt filename; the output can contain fictional mystery spoilers and should not enter frontend/public web assets.

```sh
HAUNTED_CONTENT_PATH="$PWD/game-data/blackthorn_manor.json" \
apps/backend/.venv/bin/python apps/backend/tests/live_ollama_check.py \
  --content "$PWD/game-data/blackthorn_manor.json" \
  --model qwen2.5:1.5b \
  --receipt "${TMPDIR:-/tmp}/haunted-ai-local-check.json"
```

Only that check's real-provider turns establish actual inference. Its deliberate malformed-output case remains explicitly simulated. This check does not certify browser accessibility, final media/audio behavior or deployment readiness.
