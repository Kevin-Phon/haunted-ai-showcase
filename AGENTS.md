# Contributor instructions

Keep the game playable and preserve its required scope: six rooms, three ghosts, eight clues, two puzzles, four deductions and three evidence-supported endings.

Before editing, verify the repository root, current branch and working-tree status. Preserve unrelated changes. Use a feature branch and review changes before integration. Do not change another contributor's active checkout or commit credentials, local environments, model weights, recordings or build output.

## Safety

Batch deletion of files or directories is forbidden. Never run recursive or bulk deletion commands, including `rm -rf`, `del /s`, `rd /s`, `rmdir /s` or `Remove-Item -Recurse`. Delete an authorized file only by its explicit, precise path. If batch deletion is required, stop and ask the owner to perform it manually. Use fresh directories for dependency installs and release builds; do not silently clean existing work.

## Boundaries

Frontend owns presentation and controls. Backend owns authoritative state and AI validation. Game content must satisfy the versioned schema. Model output cannot directly change progress. Keep the canonical story JSON and private content schema out of the production frontend bundle. Published source and test fixtures can contain spoilers; mark spoiler-bearing documentation clearly.

Contract changes need an explicit compatibility and migration review across backend, frontend and content. Keep contract examples, generated public types and tests aligned. Validate text as data rather than injecting HTML. Label synthetic/demo/fallback output honestly.

Run the relevant [integration checks](docs/integration.md). Report what actually passed, failed or was not run; unit tests do not prove browser accessibility or live inference. Keep generated-image and audio provenance accurate. Public release, licensing and contest submission require the project owner's approval.
