# Haunted AI frontend

Whispers of Blackthorn Manor is a supernatural detective game. Explore six rooms, inspect objects, reconstruct a letter, calibrate a memory machine, connect evidence and question three spirits before submitting a final account.

This React and TypeScript frontend presents the investigation. FastAPI owns the rules, progress, evidence, puzzle validation and endings. Local Ollama/Qwen helps select permitted authored facts and a reaction for a ghost reply; the model cannot award progress or change the case. Each reply labels its actual source as live, deterministic demo or fallback.

Owner-approved public source snapshot for `Kevin-Phon/haunted-ai-showcase`. The [MIT license](../../LICENSE) applies only to project rights the owner can grant, without asserting exclusive copyright in AI-generated outputs. Publication and submission require their own delivery receipts.

## Run locally

Use Node 22.13 or later. Verification used Node 24.22.1. First follow the [backend setup instructions](../backend/README.md) to install its environment and start FastAPI on port 8000. The backend can use an existing local Ollama model; deterministic demo mode does not require model inference.

From the repository root, use the reviewed lockfile in a fresh checkout where `apps/frontend/node_modules` does not exist:

```sh
npm --prefix apps/frontend ci
npm --prefix apps/frontend run dev
```

`npm ci` removes an existing dependency directory. Do not run it over an existing `node_modules` directory or bulk-delete that directory; use a fresh checkout or dependency directory for this installation.

Open `http://127.0.0.1:5173`. Choose live local model or deterministic demo, then enter the manor. The development server binds to localhost and proxies `/api` to `http://127.0.0.1:8000`. The backend accepts the localhost/127.0.0.1 port-5173 origins by default.

To point development at a separate backend, set `HAUNTED_API_PROXY` and use an unused frontend port:

```sh
HAUNTED_API_PROXY=http://127.0.0.1:8001 npm --prefix apps/frontend run dev -- --port 5174 --strictPort
```

That backend instance must also be configured with the matching frontend URL through its supported `create_app(allowed_origins=...)` setting. Changing the proxy alone does not authorize a new origin. Use separate sessions for independent checks.

## How to play

Select an illuminated object or use the always-visible object list. Inspect it, then choose an available operation such as Open. Return to the Entrance Hall to travel between rooms; only routes allowed by the server are enabled.

The journal contains collected records and readable transcripts. Letter fragments can be dragged or placed with labeled selectors. Machine settings use labeled controls. On the board, arrange cards and select two collected clues to test a deduction. Presentation changes do not solve puzzles or award evidence.

In Spirits, choose an available character, enter a question, select a tone and optionally present up to three earned records. Review the evidence supporting each claim before submitting a final theory. A valid final submission ends the investigation; restart requires confirmation.

See the [player guide](../../game-data/PLAYER_GUIDE.md) for spoiler-free instructions. The canonical content and tests contain puzzle solutions and ending criteria; reading them can spoil the mystery.

## State, recovery and accessibility

The browser renders public API state; server-only game content and solution rules are not imported into the production frontend. Object operations, puzzle domains, available routes and collected evidence come from that public state. Room images, portraits and sound use server-supplied asset references and safe local paths. The optional discovery cue is resolved from the public `audio_discovery` audio record; missing, unsafe or wrong-kind references omit the cue.

An uncertain mutation preserves its exact request ID and body for an explicit same-request retry. Reading newer state does not authorize a different mutation while that outcome is unresolved. Older snapshots cannot replace newer accepted revisions. Lost or exhausted sessions offer explicit new-investigation confirmation; capacity errors remain visible.

Sessions are held in backend memory. Browser storage saves only an opaque session reference, so refresh can resume a session while that backend still holds it. Restart clears gameplay and drafts after acceptance, but does not replenish process or session lifetime limits.

Keyboard alternatives accompany drag controls. Inspection supports Escape and restores focus. Zoom applies to artwork and targets together, with an object list available independently. System and explicit reduced-motion settings reduce movement without removing information. Sound begins off, has native pause/mute/volume controls, handles playback refusal and stops when its player is unmounted. Progress and story cues remain visible with sound off.

## Build and checks

From the repository root:

```sh
npm --prefix apps/frontend run typecheck
npm --prefix apps/frontend run lint
npm --prefix apps/frontend test
npm --prefix apps/frontend run format:check
npm --prefix apps/frontend run build
npm --prefix apps/frontend run check:bundle
npm --prefix apps/frontend run preview
```

The build writes `apps/frontend/dist`. `check:bundle` inspects that output for development fixture chunks and known private-answer markers; it is not a comprehensive security audit. Build cleanup is disabled (`emptyOutDir: false`). Prefer a fresh output directory for release packaging; stale files can remain in an existing output directory.

Production hosting must serve public assets at their supplied paths and route `/api` to FastAPI. Never put server credentials into Vite environment variables or serve the server-only content JSON as a static frontend file. No public hosting or deployment is established by these commands.

`npm --prefix apps/frontend run generate:types` regenerates public TypeScript API types from the versioned schema in `contracts/v1/`. Keep the app-local lockfile with dependency changes.

## Development fixtures and public API capture

Development-only `http://127.0.0.1:5173/?transport=fixtures` opens a labeled synthetic response viewer. It replays independent public contract fixtures; it does not run the mystery or prove model inference. Production uses the real API and excludes that development transport.

The optional capture script uses the installed backend test environment and an explicit content file. It starts a separate in-process FastAPI TestClient, exercises a small deterministic-demo API smoke and writes public response states. It does not start or stop a listening server, call the model, solve the complete mystery or verify every ending.

From the repository root, after backend setup:

```sh
HAUNTED_AUDIT_DIR="$(mktemp -d)"
PYTHONPATH="$PWD/apps/backend" PYTHONDONTWRITEBYTECODE=1 \
  apps/backend/.venv/bin/python apps/frontend/scripts/capture-public-api.py \
  --content game-data/blackthorn_manor.json \
  --output "$HAUNTED_AUDIT_DIR/public-api.json"
HAUNTED_PUBLIC_AUDIT="$HAUNTED_AUDIT_DIR/public-api.json" \
  npm --prefix apps/frontend test
```

Six optional component tests consume that public projection file. Without `HAUNTED_PUBLIC_AUDIT`, those six cases skip explicitly. Keep generated captures out of the production bundle.

## Verified behavior and limits

The recorded frontend check ran 36 tests successfully with the optional projection input, plus type, lint, formatting, build and bundle checks. Production browser checks covered all six rooms, eight evidence records, both puzzles, four deductions, all three endings and confirmed restart. Keyboard inspection/focus, a 390-pixel layout without horizontal overflow, reduced motion and opt-in sound were checked. Playback denial was tested in the component suite.

A complete live-mode browser investigation reached Truth Revealed at 14/14 and restarted to an empty journal and cleared dialogue. Clara and Thomas returned live Qwen replies; Eleanor used the explicit timeout fallback. This proves that the observed journey continued through a provider timeout, not that every future reply will be live or timely. Live factual clauses remain authored and model-selected; unrestricted generated conversation is not established.

These checks are not a full screen-reader, contrast, physical touch-device, browser-compatibility or low-end performance audit. Images total about 21 MB and load as scenes/portraits are needed; local transfer measurements do not establish slow-network performance. See [asset provenance and rights notes](ASSETS.md).
