# OTA discovery benchmark

## Baseline — full-repository discovery

Run `33239602596` scanned the OTA repository through the discovery agent before selecting topics.

- Discovery start: 2026-08-29T06:55:03Z
- Discovery finish: 2026-08-29T07:04:32Z
- Wall time: about 569 s (9 min 29 s)
- Queued topics: 3
- Downstream research was limited to 2 topics.

## Deterministic document scope v1

Run `33241159028` used `discover-ota-scoped.py` in discovery-only mode.

- Deterministic source selection: 1.176 s
- Discovery-agent analysis: 75.939 s
- Combined scoped discovery: about 77.1 s
- Selected source: `src/content/documents/OTA-SCI-0042-2026-DE.md`
- Explicit context documents: 3
- Proposed gaps: 2
- Exa / AI Gateway stage: skipped

Relative to the baseline discovery-agent step, the scoped design reduces discovery time by about 86.4% and is about 7.4x faster.

## Benchmark hygiene

Discovery-only runs are non-mutating. They use `discover-ota-scoped-dryrun.py`, which executes the production scoped discovery implementation while suppressing research-queue writes. The report marks findings as dry-run proposals. Full and scheduled sweeps continue to use the production writer and normal evidence pipeline.
