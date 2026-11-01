# Versioned contracts

Contract **1.0.0** defines the implemented boundary between the browser, FastAPI backend and structured story data. Canonical content version **1.0.1** uses format 1.0.0. Content and API versions are separate identifiers.

- [OpenAPI 3.1](v1/openapi.json): five HTTP endpoints and request/response references.
- [Public API schema](v1/api.schema.json): closed JSON Schema 2020-12 objects, action union, public state and AI source metadata.
- [Content schema](v1/game-data.schema.json): backend-only canonical content format; do not bundle it into the frontend.
- [Semantics](v1/semantics.md): action, revision, idempotency, progression, recovery and labeling rules.
- [Fixture index](v1/fixture-index.json): 39 indexed synthetic wire examples and their schema targets.

Fields are required unless the schema says otherwise; nullable fields remain present with null. Unknown fields are rejected. Stable content IDs use lowercase snake_case, while session/request identities use UUIDs. Exact schemas and implemented semantics take precedence over informal prose.

The examples include accepted, incorrect and duplicate puzzles/deductions; live/demo/fallback metadata; event replay; endings; revision conflicts and lost sessions. They are independent synthetic interface scenarios, not a chronological playthrough, actual gameplay receipts or proof of live inference. **Spoilers:** canonical content and some examples/tests expose fictional answers and endings even though normal runtime responses filter undiscovered truth.

Run `apps/backend/.venv/bin/python scripts/check_setup.py --full-schema` after [installing dependencies](../docs/development.md). Without `--full-schema`, the checker performs structure/reference checks and explicitly reports full validation as not run. The full command validates schemas, indexed examples and selected invalid-request/metadata cases. Frontend public TypeScript types are generated from the API schema; actual API projection component tests are a separate [integration layer](../docs/integration.md).

Propose contract changes with affected consumers, compatibility impact, migration, schema/example updates and relevant tests. Coordinate review before changing dependent backend, frontend or content code. Do not silently change schemas to accommodate an unreviewed feature. This source snapshot contains an implemented game; historical setup-only restrictions do not describe its current behavior.
