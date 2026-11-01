# Haunted AI: Whispers of Blackthorn Manor

A single-player supernatural detective browser game. Explore six mansion rooms, collect eight clues, solve two puzzles, connect evidence and question three ghosts before submitting an evidence-supported theory.

**Owner-approved public source snapshot.** This package is prepared for `Kevin-Phon/haunted-ai-showcase`. Public repository access, video upload and contest submission require their own delivery receipts; this documentation alone does not establish those outcomes.

## Play locally

Use Python 3.11+ and Node 24. Follow [development setup](docs/development.md), then open the frontend at `http://127.0.0.1:5173/`. Start with **Deterministic demo** to play without installing a model. Choose **Live local model** after completing [Ollama setup](docs/LOCAL_AI_SETUP.md). Every reply labels its actual source: live, demo or fallback.

Read the [spoiler-free player guide](game-data/PLAYER_GUIDE.md) for movement, puzzles, conversations and keyboard alternatives. Room hotspots and the object list offer the same inspection actions. Audio begins off; reduced motion is available.

## How it works

React, TypeScript, Vite, Tailwind CSS and Motion for React render public state. Python/FastAPI owns rules, sessions, evidence, puzzles, deductions and endings. Structured JSON supplies the story. The local Ollama/Qwen adapter selects permitted authored fact IDs and a bounded reaction; the backend validates that selection and renders factual clauses. AI cannot grant clues or decide an ending.

- [Architecture](docs/architecture.md) and [versioned contracts](contracts/README.md)
- [Game design](docs/game-design.md) and [verification status](docs/progress.md)
- [Integration checks](docs/integration.md) and [contributor rules](AGENTS.md)
- [Challenge and submission context](docs/submission.md)
- [Credits and third-party notices](THIRD_PARTY_NOTICES.md)

## Verified scope and limits

A fresh macOS install passed 20 Data, 56 Backend and 36 Frontend tests with actual public API projections, plus schema, lint, format, type, build and bundle checks. Separate browser runs reached all three demo endings. One complete live-mode browser run reached Truth Revealed and restarted successfully with two genuine live replies and one explicitly labeled timeout fallback. These are bounded development results, not a reliability benchmark.

Sessions live in one backend process and are lost when it restarts. Physical touch devices, comprehensive screen-reader/contrast checks and broad performance testing remain unverified. Eleven moderate development-tool audit findings remained; no high, critical or production-dependency findings were reported in that audit.

**Spoilers:** the player guide avoids the solution, but canonical story JSON, tests and contract examples contain fictional answers and endings. Read source after playing if you want to preserve the mystery. Runtime API filtering keeps undiscovered truth out of normal browser responses; it does not make published source secret.

Owner-controlled project contributions are available under the [MIT license](LICENSE), to the extent the owner can grant those rights. Upstream software/model terms remain separate, and no exclusive copyright in AI-generated outputs is asserted; see [notices](THIRD_PARTY_NOTICES.md).
