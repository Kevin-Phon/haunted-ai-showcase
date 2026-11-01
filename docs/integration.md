# Integration checks

Use one checkout containing backend, frontend, canonical content and contracts. Install dependencies using [development setup](development.md). Run checks from the repository root unless stated otherwise.

```sh
apps/backend/.venv/bin/python scripts/check_setup.py --full-schema
apps/backend/.venv/bin/python game-data/validate_content.py
apps/backend/.venv/bin/python -m unittest discover -s game-data/tests -v
HAUNTED_CANONICAL_CONTENT="$PWD/game-data/blackthorn_manor.json" apps/backend/.venv/bin/python -m pytest apps/backend/tests -q -p no:cacheprovider
apps/backend/.venv/bin/ruff check apps/backend
apps/backend/.venv/bin/ruff format --check apps/backend
apps/backend/.venv/bin/python -m pip check
```

Capture actual public API projections in a new temporary directory, then supply the capture to frontend component tests:

```sh
haunted_audit_dir=$(mktemp -d)
apps/backend/.venv/bin/python apps/frontend/scripts/capture-public-api.py --content "$PWD/game-data/blackthorn_manor.json" --output "$haunted_audit_dir/public-api.json"
HAUNTED_PUBLIC_AUDIT="$haunted_audit_dir/public-api.json" npm --prefix apps/frontend test
npm --prefix apps/frontend run typecheck
npm --prefix apps/frontend run lint
npm --prefix apps/frontend run format:check
npm --prefix apps/frontend run build
npm --prefix apps/frontend run check:bundle
```

The capture uses an in-process test client. It does not contact a listening game server or exercise the full mystery. Without `HAUNTED_PUBLIC_AUDIT`, six optional frontend projection cases skip; without `HAUNTED_CANONICAL_CONTENT`, canonical backend integration coverage skips. Report skips rather than calling them passes. Expected recorded complete-suite counts are 20 Data, 56 Backend and 36 Frontend; a later source revision can change those counts.

`check_setup.py` without `--full-schema` performs structural checks only. Indexed synthetic contract examples are not live-inference receipts. To regenerate public TypeScript definitions after an approved contract change, use `npm --prefix apps/frontend run generate:types` and inspect the diff.

## Separate practical review

Browser-check movement, object states, both puzzle control routes, deductions, theory, three endings, restart and recovery. Inspect narrow layouts, keyboard focus, reduced motion and audio opt-in/off. Live-model checks need the actual local provider, visible per-reply source labels and retained failures. Keep raw spoiler-bearing/private test receipts outside production assets.

Do not import canonical truth or private schemas into the browser. Review fresh build output for hidden story JSON, development fixtures and stale artifacts. `emptyOutDir` is false: use a fresh build directory for release packaging, not bulk cleanup. A passing source test suite does not establish public deployment, full accessibility, model reliability or contest submission.
