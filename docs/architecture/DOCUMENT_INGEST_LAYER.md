# KUEPER Document Ingest Layer

Status: architecture draft

## Purpose

The Document Ingest Layer is the common source boundary for narrative, research, educational and system documents. Agents must not each invent their own interpretation/storage path for repository files.

Core principle:

> Document content is a source, not automatically canonical truth.

```text
Document Source -> Registry -> Ingest -> Passage/Chunk -> Assertion
 -> Interpretation Candidates -> Review/Acceptance -> Canonical State
```

## Source levels

The system distinguishes:

- `SOURCE_DOCUMENT`: immutable/versioned source identity and content provenance.
- `PASSAGE`: addressable source span/chunk.
- `EXTRACTED_ASSERTION`: what a passage states or presents.
- `INTERPRETATION_CANDIDATE`: structured Object/Relation/Event/Claim/Belief interpretation.
- `CANONICAL_STATE`: accepted project truth/state under the owning project's rules.

Extraction MUST NOT directly create canonical state.

## Authority lifecycle

- `A0_RAW`: registered source, not interpreted.
- `A1_EXTRACTED`: machine-readable assertion/candidate exists.
- `A2_ACCEPTED`: accepted by project rules/review for use.
- `A3_CANONICAL`: binding canonical state where the domain supports canon.

Agents may normally perform A0 -> A1. A1 -> A2 is policy-dependent. Creative/scientific A2 -> A3 changes require the owning project's canon/evidence gate unless explicitly deterministic.

## Document types

Initial types:

- `MANUSCRIPT`
- `PUBLISHED_TEXT`
- `CANON_NOTE`
- `WORLD_BIBLE`
- `DRAFT`
- `RESEARCH_NOTE`
- `EXTERNAL_SOURCE`
- `GAME_EVENT_LOG`
- `AGENT_OBSERVATION`
- `LEARNING_CONTENT`
- `TECHNICAL_SPEC`

Type and status are separate. A manuscript may be draft or published; a research note may be provisional or accepted.

## Ingest channels

### Repository source

Registered repository/path patterns are the primary channel. Only configured paths are watched. Git commit/blob identity supplies version provenance.

### Manual inbox

A future upload/inbox adapter may register user-provided documents with explicit project, type, status and authority metadata.

### Agent/system source

Structured outputs such as SSF evidence records, KG findings and NOXIA game observations may be registered as sources. They retain their original provenance and do not gain authority merely by entering the ingest layer.

## Source registry

A registry entry should identify:

```json
{
  "source_id": "stable-id",
  "project": "ENDIA",
  "channel": "github",
  "repository": "owner/repo",
  "path": "manuscript/book-1.md",
  "document_type": "MANUSCRIPT",
  "status": "draft",
  "authority": "A0_RAW",
  "version_ref": "commit/blob-sha"
}
```

Repository/path registration is configuration. An agent must not silently expand its source scope.

## Provenance

Every extracted assertion and interpretation candidate must retain a resolvable source location:

```text
source_id + version_ref + section/chapter + passage/span
```

Where exact character offsets are unstable, use stable passage identifiers plus source hashes. Generated summaries are never provenance substitutes.

## Assertions and epistemic role

An assertion must record how the text presents information. Initial roles:

- `NARRATOR_ASSERTION`
- `CHARACTER_SPEECH`
- `CHARACTER_BELIEF`
- `CHARACTER_PERCEPTION`
- `DOCUMENT_CLAIM`
- `EDITORIAL_NOTE`
- `SYSTEM_OBSERVATION`

Character speech or belief MUST NOT automatically become world truth. Scientific/source claims MUST NOT automatically become accepted evidence/canon.

## Interpretation candidates

Candidates may reference or propose:

- Object
- Relation
- Event
- Claim
- Belief
- Evidence
- temporal state
- character knowledge state
- reader knowledge state

Candidate identity should be stable enough for re-ingest/deduplication. Confidence in extraction is distinct from authority/truth status.

## Incremental ingest

The layer is version-aware. On source change it should:

1. identify changed/added/removed passages;
2. preserve provenance to previous versions;
3. re-extract only affected passages where practical;
4. mark dependent candidates as changed/stale rather than silently deleting accepted state;
5. produce review candidates when accepted/canonical information may be affected.

## Canon boundary

The Canon/Continuity Agent consumes accepted canonical state plus candidate assertions/provenance. It should not parse arbitrary files independently.

This permits findings such as:

```text
candidate extends canon
candidate contradicts canon
candidate changes temporal state
candidate affects character knowledge
candidate duplicates an existing object/relation/event
```

with direct traceability to the source passages.

## Formats

V0.1 should prioritize text-native repository formats:

- Markdown
- plain text
- JSON/YAML structured records where already authoritative

DOCX/PDF and other binary/document formats should enter later through dedicated adapters that preserve document identity and source locations. OCR is not a default ingest mechanism.

## V0.1 implementation target

Implement the common contract and a minimal repository ingest foundation:

1. source registry schema with project/path/type/status/authority/version metadata;
2. source document and passage records with stable provenance;
3. assertion and interpretation-candidate schemas;
4. epistemic-role field separating narrator/world assertions from speech, belief, perception and document claims;
5. A0/A1/A2/A3 lifecycle metadata;
6. Markdown/plain-text repository adapter with deterministic passage segmentation;
7. version-aware fingerprints and duplicate-safe re-ingest;
8. fixtures/tests showing a repeated unchanged ingest is idempotent, a changed passage is detected, and character speech does not become world truth;
9. no direct canon mutation;
10. a bounded TaskCandidate/outbox path for ingest conflicts requiring project review.

V0.1 creates the shared source/provenance substrate. Object–Relation–Event extraction and Canon/Continuity reasoning can then build on one common representation.
