# KUEPER Knowledge Graph Curator Agent

Status: architecture draft

## Purpose

The KG Curator is the coherence sensor for the KUEPER Ecosystem. It observes accepted or proposed changes from participating projects and detects graph-level inconsistencies, duplicates, missing relations, provenance gaps and stale knowledge. It does not invent canon and does not directly rewrite source-of-truth repositories.

```text
Project changes / evidence / external tasks
        -> normalized change observations
        -> graph checks
        -> findings
        -> evidence + ownership gate
        -> TaskCandidate
        -> existing KUEPER routing
```

## Initial finding classes

- `DUPLICATE_ENTITY`: two records likely represent the same canonical object.
- `CONFLICTING_CLAIM`: incompatible claims exist for the same scoped subject/property/time.
- `MISSING_RELATION`: an expected relation required by an accepted schema/path is absent.
- `BROKEN_REFERENCE`: referenced object/identifier cannot be resolved.
- `PROVENANCE_GAP`: a canonical/scientific claim lacks required source/evidence provenance.
- `STALE_CLAIM`: accepted evidence or source refresh indicates a claim needs validation.
- `SCHEMA_DRIFT`: producer/export no longer conforms to the canonical KG contract.
- `ORPHAN_ENTITY`: object is unreachable from required canonical structures where reachability is an invariant.
- `TEMPORAL_INCONSISTENCY`: time-scoped states/relations violate explicit temporal constraints.
- `POSSIBLE_CROSS_PROJECT_IMPACT`: an accepted change may affect another registered project.

A finding is not automatically an error. The agent must preserve uncertainty.

## Inputs

V0.1 should consume bounded, explicit inputs rather than arbitrary repository contents:

- KG canonical exports/validation surfaces;
- KXF records and schema validation results;
- accepted KUEPER external-task outcomes where available;
- SSF evidence/canon-validation outcomes when they affect KG concepts;
- later, Object–Relation–Event exports from narrative repositories.

Repository ownership and source-of-truth rules remain authoritative.

## Finding record

```json
{
  "finding_id": "stable-fingerprint",
  "kind": "CONFLICTING_CLAIM",
  "subject_refs": ["..."],
  "claim_refs": ["..."],
  "evidence_refs": ["..."],
  "summary": "...",
  "confidence": 0.91,
  "severity": "medium",
  "owner_target": "KG",
  "detected_at": "RFC3339"
}
```

Stable fingerprints must be based on the underlying condition, not generated prose.

## Promotion gate

Before emitting a task candidate, the curator checks:

- whether the condition is reproducible from current canonical inputs;
- whether an existing open/parked/done task already covers the fingerprint;
- ownership/source-of-truth target;
- confidence and severity;
- whether the finding can be resolved deterministically by validation or requires human/domain review;
- cooldown and recurrence count.

Low-confidence semantic duplicate/conflict findings are parked for review. Deterministic broken references/schema violations may promote automatically.

## Autonomy boundaries

The Curator MUST NOT:

- create new scientific facts or fictional canon to close a gap;
- choose between contradictory scientific claims merely for graph neatness;
- silently merge entities based only on semantic similarity;
- rewrite narrative continuity;
- mutate another repository directly;
- automatically merge pull requests.

It may propose a minimal corrective task and attach evidence/reproduction.

## Cross-project behavior

Examples:

```text
SSF accepts revised scientific concept
 -> Curator sees KG claim now stale
 -> CANON_VALIDATION -> KG

NOXIA requests concept that already exists under another identifier
 -> DUPLICATE_ENTITY / mapping candidate -> KG

KG schema changes and SSF export fails validation
 -> SCHEMA_DRIFT -> owning project

Later: narrative ORE model contains two incompatible time-scoped states
 -> TEMPORAL_INCONSISTENCY -> narrative/canon owner
```

## Cost-aware execution

Deterministic graph/schema checks should run cheaply and frequently. Semantic duplicate detection, cross-project impact analysis and large consistency sweeps should use `prefer_off_peak`; broad full-graph synthesis may use `off_peak_only`. Blocking schema/reference failures may run `immediate`.

## V0.1 implementation target

Implement the smallest useful curator in the Knowledge Graph repository:

1. persistent finding/fingerprint state;
2. adapters over existing canonical KG/KXF validation surfaces rather than a parallel graph;
3. deterministic checks for broken references and schema drift where supported by current structures;
4. bounded duplicate/conflicting-claim candidate detection only where identity/property semantics are explicit enough;
5. provenance-gap detection for claim types that already require provenance;
6. deduplication/cooldown and existing-task checks;
7. conversion of promoted findings to valid KUEPER outbox envelopes;
8. deterministic fixtures/tests for one valid graph, one broken-reference/schema case and duplicate finding collapse;
9. no direct canon mutation.

V0.1 is a curator and anomaly detector, not an autonomous ontology designer.
