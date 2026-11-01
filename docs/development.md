# Local development

Use a fresh checkout with Python 3.11+ and Node 24 (`node --version`). The frontend requires Node at least 22.13. Recorded fresh-install verification used Python 3.14.7 and Node 24.22.1; Python 3.11 also passed backend CI. Other environments need their own checks.

Run commands from the repository root. Create a new app-local environment and install locked dependencies:

```sh
python3 -m venv apps/backend/.venv
apps/backend/.venv/bin/python -m pip install -r apps/backend/requirements.lock
apps/backend/.venv/bin/python -m pip install --no-deps -e apps/backend
npm --prefix apps/frontend ci
```

These instructions assume `.venv` and `node_modules` do not already contain work. If they exist, use a fresh checkout or new isolated build directory. Do not bulk-delete existing dependencies; follow [contributor safety rules](../AGENTS.md). The backend editable install uses isolated build tooling; the checked-in locks record application/test dependency versions.

## Start the backend

Demo mode needs no model installation. For live mode, first follow [local AI setup](LOCAL_AI_SETUP.md). In terminal one at the repository root:

```sh
HAUNTED_CONTENT_PATH="$PWD/game-data/blackthorn_manor.json" HAUNTED_OLLAMA_MODEL=qwen2.5:1.5b HAUNTED_OLLAMA_URL=http://127.0.0.1:11434 apps/backend/.venv/bin/python -m uvicorn haunted_backend.app:app --host 127.0.0.1 --port 8000 --workers 1
```

Check `http://127.0.0.1:8000/api/v1/health`. Ready content permits session creation; health does not call the model or prove successful inference. `.env.example` is a template and is not automatically loaded. Run a single worker because sessions are process-local.

## Start the frontend

In terminal two at the repository root:

```sh
npm --prefix apps/frontend run dev -- --port 5173 --strictPort
```

Open `http://127.0.0.1:5173/`. Vite proxies `/api` to `http://127.0.0.1:8000`. Use the normal player interface; development-only fixture transport is a synthetic UI tool, not gameplay or live AI.

If the intended ports are occupied, do not stop an unrelated process. Select an unused backend port and set the frontend's `HAUNTED_API_PROXY` to that loopback URL; the default origin configuration is intended for the normal 5173 frontend. Reusing an existing correct server is preferable to creating a competing process.

Demo uses authored dialogue with no provider call. Live attempts local Qwen, and failed attempts are labeled fallback. Backend rules remain authoritative in either mode. A browser refresh can resume a surviving session, but restarting the backend loses it. There are eight process-lifetime session slots and a 500-mutation lifetime allowance per session. In-game restart clears investigation progress, not the allowance; use explicit new-investigation recovery at the limit.

Run [integration checks](integration.md) before proposing changes. Keep `.env`, credentials, model stores, virtual environments, dependencies, build output and recordings out of Git. No public hosting or multiuser deployment is configured by these local instructions.
