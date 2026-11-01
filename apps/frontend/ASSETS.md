# Frontend assets and provenance

This inventory covers nine raster images, two synthesized sounds and original interface artwork. Files are under `public/media/`; the runtime receives their approved references through public API state. The inventory manifest is provenance metadata, not a source of game rules.

Owner-approved public source snapshot for `Kevin-Phon/haunted-ai-showcase`. The [MIT license](../../LICENSE) applies only to rights the owner can grant. No third-party asset license, CC0 status, exclusive copyright or rights guarantee is asserted here. Preserve the generation and modification provenance below.

## Generated images

The six room images and three fictional ghost portraits were generated on October 31, 2026 with OpenAI's built-in imagegen tool, using original project prompts. The tool did not expose its underlying model identifier or version. No external reference image, downloaded stock, real-person likeness request or font file was used. The runtime Ollama/Qwen model did not create these images.

Room outputs were 1672 × 941 pixels. macOS sips 316 resampled them to exact 1600 × 900 using `sips -z 900 1600`, without cropping. The aspect ratio changes slightly; source inspection found no visible composition loss. Original outputs were preserved separately and are not part of the served asset payload. Portraits remain unchanged 1024 × 1536 PNGs.

| Stable asset ID | Served relative path | Dimensions / duration | Bytes | Attribution ID |
| --- | --- | --- | ---: | --- |
| `art_entrance_hall` | `media/entrance_hall-scene-v1.png` | 1600 × 900 | 2,568,564 | `generated_entrance_hall_20261031` |
| `art_library` | `media/library-scene-v1.png` | 1600 × 900 | 2,328,938 | `generated_library_20261031` |
| `art_study` | `media/study-scene-v1.png` | 1600 × 900 | 2,175,572 | `generated_study_20261031` |
| `art_laboratory` | `media/laboratory-scene-v1.png` | 1600 × 900 | 2,323,654 | `generated_laboratory_20261031` |
| `art_grand_ballroom` | `media/grand_ballroom-scene-v1.png` | 1600 × 900 | 2,401,090 | `generated_grand_ballroom_20261031` |
| `art_hidden_passage` | `media/hidden_passage-scene-v1.png` | 1600 × 900 | 2,149,684 | `generated_hidden_passage_20261031` |
| `art_eleanor` | `media/eleanor-v1.png` | 1024 × 1536 | 2,327,444 | `generated_eleanor_20261031` |
| `art_thomas` | `media/thomas-v1.png` | 1024 × 1536 | 2,210,956 | `generated_thomas_20261031` |
| `art_clara` | `media/clara-v1.png` | 1024 × 1536 | 2,533,330 | `generated_clara_20261031` |
| `audio_manor_ambience` | `media/manor-ambience-v1.wav` | 8 s PCM | 352,844 | `original_synth_audio_20261031` |
| `audio_discovery` | `media/discovery-v1.wav` | 1.5 s PCM | 66,194 | `original_synth_audio_20261031` |

PNG files total 21,019,232 bytes; the full listed media payload is 21,438,270 bytes. Only current room layers are rendered, with reserved dimensions, and portraits use native lazy loading. This describes loading behavior, not a guarantee of bandwidth or device performance.

## Prompt direction

The common direction was a cinematic, painterly 2D gothic manor in 1926: charcoal, midnight blue, muted violet, antique gold and spectral cyan; readable objects; no UI, logos, watermarks or answer hints. Rooms use fixed eye-level wide compositions with foreground depth. Portraits use upper-body framing and spectral edges, with no supplied likeness.

- Entrance Hall: rain-streaked windows, vaulted architecture, central stairs, chandelier and family crest.
- Library: shelves, writing desk, gold lamp and brass-handled letter drawer.
- Study: researcher desk, scorched notebook, household ledger and blotter.
- Laboratory: cyan crystal in a brass cradle and an experimental copper-and-glass memory machine with unlabeled controls.
- Grand Ballroom: empty moonlit dance floor, chandeliers, draped windows and an indistinct gathering photograph.
- Hidden Passage: narrow service corridor and archival box, without visible document contents.
- Eleanor: a guarded adult aristocratic woman in violet period dress, with pinned dark hair and an antique brooch.
- Thomas: a nervous, observant adult butler in formal waistcoat and jacket.
- Clara: a thoughtful adult researcher in an ivory blouse and dark waistcoat, with cyan spectral light.

The generated Library backplate depicts an open drawer. An opaque original wood-front overlay covers it while the public object state is closed; the cover is removed only after the backend accepts opening it. The laboratory's decorative glow does not prove calibration. Current public object availability, bounds and accepted puzzle state remain authoritative.

## Original interface work and fonts

Original CSS supplies fog, vignette/light, restrained pointer depth, focus markers, object-state treatments, paper fragments, calibration instrument, evidence illustrations/cards, event glow and ending framing. These are code-based presentation elements. Portrait lighting follows public emotion cues; the frontend does not infer truth or state from response prose.

Typography uses system Georgia/Times and system-ui. No external font file is shipped, and no rights to redistribute system fonts are claimed. Unicode marks are text presentation.

## Synthesized sound

`scripts/generate-audio.py` creates both WAV files from mathematical sine functions, with no recordings, samples, model inference or downloaded audio:

- Ambience: an eight-second loop using 55, 82.5 and 110 Hz tones.
- Discovery: a 1.5-second bell using 440 and 660 Hz tones with an envelope.
- Encoding: 22050 Hz, mono, 16-bit PCM.

The generator refuses to overwrite existing files. Sound starts off and exposes native pause/mute/volume controls after opt-in. Playback refusal has a readable recovery message. Ambience pauses when its player unmounts. The discovery cue plays only after accepted server progress increases, and only when a safe public audio asset with ID `audio_discovery` exists. There is no independently assumed fallback path. Switching sound off removes both players. Every story/progress cue also has visible feedback.

## Verification scope

The recorded frontend run passed 36 tests with optional public API projection input, plus type, lint, formatting, build and bundle checks. Actual production browser checks covered room/portrait rendering, the closed/open drawer treatment, a complete 14/14 mystery, all three endings and restart. Keyboard inspection/focus, reduced motion, a 390-pixel layout and opt-in sound were checked. A focused playback check observed initial cue silence, playback after an accepted discovery, and no audio elements after sound was switched off. Playback refusal was exercised in component tests.

A full live-mode journey included two actual live Qwen replies and one explicit timeout fallback. It still reached Truth Revealed and restarted successfully. This is mixed-source runtime evidence, not an all-live guarantee. No full assistive-technology, contrast, physical touch-device or broad performance audit is claimed.
