# Credits and third-party notices

**Owner-approved public source snapshot.** The [MIT license](LICENSE) applies to project contributions only to the extent the owner can grant those rights. No exclusive copyright in AI-generated outputs is asserted. Upstream licenses continue to govern their respective components; the project license does not relicense them.

## Project and assisted work

The game concept and creative direction are by Kevin-Phon. Implementation, fictional story material, testing and documentation were developed with Codex assistance. The specialist development roles were AI tools, not additional human teammates. No human-only authorship or guarantee of exclusive rights in AI outputs is asserted.

Six room backplates and three fictional ghost portraits were generated on October 31, 2026 with OpenAI's imagegen tool from original project prompts. Its underlying model/version was not exposed. No external reference images, downloaded stock or requested real-person likenesses were used. Room images were resampled to 1600×900 without cropping; portraits remain 1024×1536. Qwen did not generate this artwork. Full file-level provenance is in [ASSETS.md](apps/frontend/ASSETS.md), the [media manifest](apps/frontend/public/media/manifest-a01.json) and [content provenance](game-data/PROVENANCE.md).

Fog, object covers, evidence/puzzle controls, reaction lighting and ending treatments use project code/CSS. The ambience and discovery cue were synthesized by [project code](apps/frontend/scripts/generate-audio.py), without external samples or recordings. Fonts use system Georgia/Times and system-ui; no font files are bundled. No third-party stock-art license or CC0 status is claimed.

## Local model and runtime

- **Qwen2.5-1.5B-Instruct / Ollama tag `qwen2.5:1.5b`**: open-weight model from Qwen/Alibaba Cloud. The selected tag's metadata and [publisher license](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct/blob/main/LICENSE) identify Apache-2.0. See the [official tag](https://ollama.com/library/qwen2.5:1.5b). Model weights are not distributed in this repository.
- **Ollama runtime**: separate open-source software; tested version 0.40.13 has an [MIT license](https://github.com/ollama/ollama/blob/v0.40.13/LICENSE). The runtime is not distributed in this repository. Installing a newer release requires reviewing its own terms and behavior.

These terms apply to their respective upstream materials. They are separate from the MIT license for owner-controlled game contributions.

## Software dependencies

The source references packages installed through [frontend package metadata](apps/frontend/package.json), its [lockfile](apps/frontend/package-lock.json), [backend metadata](apps/backend/pyproject.toml) and its [lockfile](apps/backend/requirements.lock). Principal installed-package license metadata in the verified environment was:

| Components | License metadata |
| --- | --- |
| React, React DOM, Vite, Tailwind CSS, Motion | MIT |
| TypeScript | Apache-2.0 |
| FastAPI, jsonschema, referencing | MIT |
| Starlette, httpx, Uvicorn | BSD-3-Clause |

This is a summary, not a replacement for upstream license texts or a complete transitive dependency inventory. Retain applicable copyright/license notices when distributing dependencies or compiled bundles. Dependencies, model stores and development environments are not vendored in the source snapshot. System fonts remain governed by the user's operating-system terms.
