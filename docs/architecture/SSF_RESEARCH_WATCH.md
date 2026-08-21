# SSF Research Watch

Status: architecture draft

## Purpose

SSF Research Watch is the real-world science sensor of the KUEPER Agent Runtime. It continuously discovers potentially relevant scientific publications and data releases, records evidence, compares them with the current SSF/KG knowledge state, and emits bounded review/update candidates.

It MUST NOT treat publication as truth and MUST NOT rewrite curriculum or canonical knowledge merely because a new paper appeared.

```text
Sources -> Discovery -> Deduplication -> Relevance -> Evidence Record
       -> Current-state comparison -> Impact classification -> TaskCandidate
       -> SSF/KG/NOXIA routing -> reviewed change
```

## Three-layer boundary

1. **Discovery**: a source reports a new or newly indexed work.
2. **Evidence**: normalized bibliographic and scientific claims with provenance and quality metadata.
3. **Curriculum/Canon Impact**: an explicit assessment of whether existing material is confirmed, extended, revised, contradicted or deprecated.

Discovery alone MUST NOT update learning content.

## Identity and deduplication

Prefer stable identifiers in this order where available:

- DOI
- arXiv identifier + version
- PubMed/other registry identifier
- dataset/release identifier
- normalized source URL + title fingerprint as fallback

The same work discovered through multiple sources becomes one evidence object with multiple discovery provenance records.

## Impact classification

- `NEW`: relevant knowledge not represented in the current scoped state.
- `CONFIRMS`: materially strengthens an existing claim without requiring a conceptual change.
- `REVISES`: changes scope, parameters, mechanism, confidence or explanation of an existing claim.
- `CONTRADICTS`: materially conflicts with an existing claim or learning statement.
- `DEPRECATES`: stronger evidence or consensus makes an existing statement/source obsolete or misleading.
- `NO_IMPACT`: relevant publication, but no current SSF/KG learning/canon change is justified.
- `UNCERTAIN`: insufficient evidence/context for automated impact classification; park for review.

## Evidence record

Minimum fields:

```json
{
  "evidence_id": "doi:10.xxxx/xxxx",
  "title": "...",
  "published_at": "RFC3339/date",
  "identifiers": {"doi": "...", "arxiv": null},
  "source_refs": [],
  "topics": [],
  "claims": [],
  "evidence_type": "primary-study",
  "review_status": "unreviewed",
  "relevance": 0.0,
  "confidence": 0.0,
  "discovered_at": "RFC3339"
}
```

Claims MUST retain provenance to the source. Generated summaries are not evidence themselves.

## Source registry

Sources are configuration, not hard-coded agent knowledge. The registry should support source classes such as:

- primary literature indexes/APIs;
- preprint services;
- journals/publishers where legally/API-accessible;
- authoritative scientific agencies and observatories;
- dataset/release feeds;
- later, curated specialist feeds.

Each source entry carries scope, query/filter rules, cadence, authority/type metadata and access method. Source coverage must be explicit so absence from the watch is never interpreted as absence from science.

## Relevance

Relevance is evaluated against an explicit SSF watch-topic registry derived from active modules, learning paths and KG concepts. It should combine deterministic identifiers/keywords with semantic classification. New topic proposals may be suggested but MUST NOT silently expand the monitored curriculum scope.

## Promotion gate

A discovery may become a task only when it has sufficient provenance and relevance. The gate considers:

- stable identity and deduplication;
- source/evidence type;
- whether the result is primary, review, meta-analysis, dataset/release, correction/retraction, etc.;
- current SSF/KG statements affected;
- strength and independence of supporting evidence;
- impact class;
- confidence and uncertainty;
- existing open/done task fingerprints.

`CONTRADICTS`, `REVISES` and `DEPRECATES` SHOULD normally trigger validation/review before content mutation. A single preprint MUST NOT silently rewrite canonical educational content.

## Task types and routing

Suggested task classes:

- `RESEARCH_DISCOVERY`: assess a new relevant result.
- `CANON_VALIDATION`: compare evidence against KG/source-of-truth statements.
- `CURRICULUM_UPDATE`: update SSF explanation/path after evidence is accepted.
- `SOURCE_REFRESH`: replace/update references without conceptual change.
- `CROSS_PROJECT_IMPACT`: investigate consequences for NOXIA/NXU/other domains.

Routing examples:

```text
new science, pedagogical consequence -> SSF
canonical concept/claim consequence  -> KG
validated simulation consequence     -> NOXIA
fictional-universe consequence        -> NXU (review-gated)
```

## Cost-aware scheduling

Discovery and deterministic deduplication should be cheap and periodic. Semantic relevance classification may use a low-cost model. Expensive synthesis, cross-source comparison and curriculum impact analysis should default to `prefer_off_peak`; broad review synthesis may use `off_peak_only`. Urgent corrections/retractions affecting published SSF content may override cost deferral.

## Cadence

The architecture supports different cadences by source. Fast feeds may be checked daily; slower review sources less frequently. Discovery cadence and synthesis cadence are independent: many discoveries can be accumulated and synthesized in one off-peak batch.

## Noise and epistemic guards

- publication != established knowledge;
- preprint status is preserved and visible;
- retractions/corrections update evidence status rather than deleting provenance;
- negative/no-impact classifications are retained to avoid repeated work;
- no LLM-generated citation may be accepted without a resolvable source identifier/reference;
- every curriculum change must be traceable to evidence records and a task/review decision;
- contradictory evidence is represented, not prematurely reconciled by generated prose;
- confidence in a claim is separate from confidence that a paper was correctly identified/classified.

## V0.1 implementation target

SSF v0.1 should implement:

1. a configurable watch-topic registry derived from current SSF scope;
2. a configurable source registry with at least one primary-literature/preprint discovery adapter and one authoritative agency/data adapter where practical;
3. normalized evidence records and DOI/arXiv/registry deduplication;
4. relevance scoring and the impact classes above;
5. persistent discovery/evidence state so the same work is not repeatedly processed;
6. `RESEARCH_DISCOVERY` and `CANON_VALIDATION` TaskCandidates only; no direct curriculum mutation;
7. KUEPER outbox emission through the existing cross-project protocol;
8. deterministic fixtures/tests for duplicate discovery, no-impact, and a candidate requiring validation;
9. cost-policy metadata so expensive synthesis can be deferred to off-peak execution.

V0.1 is a watch-and-triage system, not an autonomous scientific authority.
