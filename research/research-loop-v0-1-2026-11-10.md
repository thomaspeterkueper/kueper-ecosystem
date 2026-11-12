# Research loop v0.1 — autonomous hypothesis and experiment workflow

Status: proposal, 2026-11-10. No production execution authorized.

## Motivation
Fraunhofer ZenBio (2026-11-02) combines cell-free synthesis, robotics and AI-guided enzyme design; the 1,500-variant throughput is a future target, not yet demonstrated routine throughput.
Nature AutoDNA (2026-11-04, DOI 10.1038/s41586-026-11228-6) reports an AI-native laboratory coordinating >20 instrument types and >11,000 steps, with human maintenance.
Sources: https://www.fraunhofer.de/de/presse/presseinformationen/2026/november-2026/neue-technologie-optimiert-enzyme-fuer-die-industrie.html ; https://www.nature.com/articles/s41586-026-11228-6

## Canonical roles
- KG/OTA: source provenance, canonical scientific objects and relations; do not mint IDs without registry review.
- Research agent: propose falsifiable hypothesis and test protocol; record predicted outcomes and uncertainty.
- NOXIA: scenario simulations only, never a source of experimental truth or automatic gameplay balancing.
- Human review: authorize any real-world action, external API write, expense, or physical experiment.

## Experiment record contract
Each record includes: question; hypothesis; null hypothesis; scope; evidence sources and dates; evidence tier (synthetic, simulation, lab, operational); variables and units; assumptions; preregistered evaluation metric; protocol and version; reproducibility seed; execution environment; observed results; confidence/uncertainty; adverse findings; review decision; provenance pointers. Never pool different evidence tiers or operating envelopes.

## First pilot: electricity and storage
Compare hourly demand and generation scenarios, battery capacity and round-trip efficiency, hydrogen conversion/storage and reconversion losses, dispatchable power, curtailment and unserved energy. Use synthetic inputs first; report energy balance, reliability and cost sensitivities. No invented empirical performance figures.

## Workflow gates
intake -> source verification -> hypothesis -> review -> isolated simulation -> invariant checks -> analysis -> evidence review -> KG/OTA candidate update -> NOXIA optional scenario transfer.

## Acceptance tests
1. Missing provenance blocks promotion.
2. Synthetic evidence cannot be presented as laboratory confirmation.
3. Units and energy balance must reconcile.
4. Contradictory observations remain preserved.
5. Agent cannot run external writes or incur costs without approval.
6. NOXIA balancing remains unchanged absent explicit gameplay decision.

## Next implementation
Inventory existing ecosystem coordination and registry conventions, then create a narrowly scoped pilot request rather than a duplicate task system.
