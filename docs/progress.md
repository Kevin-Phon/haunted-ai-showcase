# Verification status

Prepared October 31, 2026 for the owner-approved public source snapshot. The [MIT license](../LICENSE) applies only to rights the owner can grant. Publication and contest submission require their own delivery receipts; test results alone do not establish them.

## Executed development checks

| Layer | Recorded result | Scope |
| --- | --- | --- |
| Fresh dependency installation | Passed on macOS with Python 3.14.7 and Node 24.22.1 | One reviewed product revision; 160 source hashes unchanged during checks |
| Data | 20 tests and content validation passed | Canonical content 1.0.1, format/contract 1.0.0 |
| Backend | 56 tests passed with canonical content enabled | No canonical cases skipped in the complete run; an upstream test-client warning remained |
| Frontend | 36 tests passed with actual in-process public API projections | Component/jsdom checks, separate from browser play |
| Tooling | Schema, lint, format, types, build and bundle checks passed | All eleven media references verified in fresh output |
| Demo browser | All three endings and restart exercised | Six rooms, eight clues, two puzzles and four deductions |
| Full live-mode browser | Truth Revealed at 14/14, followed by restart with empty journal and cleared dialogue | Two genuine live replies and one labeled timeout fallback; zero demo replies |
| Audio | Approved cue played after earned progress; turning sound off removed audio elements | Separate focused actual browser/media check |

The fresh-install suite did not repeat browser or live-model runs. Browser evidence was collected separately against identified matching product bytes. Recorded results are summarized here; raw private logs, local paths and development conversations are not distributed with this snapshot. These summaries are not a new test run of the eventual public snapshot or a published release receipt.

## Limits that remain

The local model can time out, repeat itself or choose broad permitted material. Small successful samples do not guarantee all-live replies or latency. Browser observation times included orchestration and are not inference benchmarks. Sessions are memory-only and local capacity is bounded.

Keyboard alternatives, focus behavior, reduced motion, narrow layout and optional audio received scoped checks. Physical touch devices, a complete screen-reader/contrast audit and broad network/device performance remain unverified. The latest dependency audit reported eleven moderate development-tool findings and zero high, critical or production-dependency findings; the development tree is not vulnerability-free.

After any source or dependency change, rerun the relevant [integration checks](integration.md). New publication packaging also needs its own link, privacy, license and clean-install review.
