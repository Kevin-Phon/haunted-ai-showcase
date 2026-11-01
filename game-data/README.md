# Blackthorn Manor game data

Start with the [spoiler-free player guide](PLAYER_GUIDE.md) for the premise,
controls and investigation flow. **Spoiler warning:** `blackthorn_manor.json` and
the content tests include the complete story, puzzle answers and ending criteria.
They are backend source data; they must not be bundled into browser assets.

The package uses contract format **1.0.0**, content version **1.0.1**. It contains
six rooms, three ghosts, eight evidence items, two puzzles, four deductions and
three deterministic endings. The backend owns discoveries, relationships and
outcomes. AI dialogue selects permitted character material; it cannot rewrite
rules or the mystery. Demo and fallback responses are labeled separately from
accepted live model responses.

## Validate from the repository root

Use Python 3.11+ and a new isolated environment. These commands validate the data;
they do not start a model or establish live AI/browser acceptance.

```sh
python3 -m venv .venv-data
.venv-data/bin/python -m pip install -r game-data/requirements-validation.txt
.venv-data/bin/python game-data/validate_content.py
.venv-data/bin/python -m unittest discover -s game-data/tests -v
```

If you already installed the backend using the repository setup instructions,
its environment can run these same checks. No user-specific paths or hidden
workspace imports are needed.

The validator checks schema, unique IDs, typed references, object prerequisites,
geometry and a concrete legal traversal through the required rooms and milestones.
It includes inputs for all three endings without depending on model availability
or relationship gains. This is constructive reachability, not an exhaustive search
of every possible play order. Schema validity alone does not prove dialogue secrecy
or visual/accessibility quality. Backend API and frontend integration checks are
separate parts of the project test suite.

## Media and provenance

[Provenance and rights status](PROVENANCE.md) distinguishes assisted story text,
generated images, original procedural audio and third-party components.
The [media inventory](MEDIA_AUDIT.json) records relative paths, dimensions, byte
sizes and file hashes. Media files live in `apps/frontend/public/media/`; a file's
presence does not grant rights beyond its applicable terms.

Six room backplates use a 1600x900 canvas; three portraits use 1024x1536 images.
Public hotspot geometry is aligned to those scenes. Only the backend's permitted
scene/evidence/portrait/audio references should enter a browser state snapshot.
Optional audio and presentation effects never award progress. The fictional
content, puzzle keys, authoritative rules and scoring remain backend-controlled.

The owner-approved [MIT license](../LICENSE) applies only to project rights the
owner can grant. It does not override dependency/model/media terms or assert
exclusive copyright in AI-generated outputs.
