# Document Ingest Impact & Continuity Report

Status: architecture extension

## Scope

Extends the common Document Ingest Layer for private book/manuscript storage, replaceable/versioned editions, KUE/OTA knowledge impact and cross-novel continuity validation.

A book upload is not complete until an `INGEST_IMPACT_REPORT` has been produced.

## Privacy boundary

Full manuscripts, uploaded originals, extracted passages and non-public working versions are PRIVATE by default. They MUST NOT be stored in public repositories or public website paths.

Separate storage domains:

- `PRIVATE_SOURCE_STORAGE`: original book/manuscript files and versions.
- `PRIVATE_INGEST_STORE`: passages, assertions, extraction state and source provenance.
- `CANON/KG/KUE/OTA`: only accepted structured derivatives according to project policy.
- `PUBLIC`: only explicitly published/released material.

No derivative becomes public merely because its source was ingested.

## Book and version model

A logical book has stable identity independent of uploaded files.

```text
Book
  -> Version v1 [SUPERSEDED]
  -> Version v2 [PUBLISHED]
  -> Version v3 [ACTIVE working revision]
```

Initial version states:

- `ACTIVE`
- `SUPERSEDED`
- `ARCHIVED`
- `PUBLISHED`

Uploading a replacement creates a new version. Previous versions and their provenance remain addressable. A published edition is not overwritten by a later working revision.

Each version records at least book_id, version_id, source hash, edition/status, uploaded_at, replaces_version_id, continuity_scope, authority/canon_weight and whether it is current for working analysis.

## Incremental replacement ingest

For a replacement version:

1. compare against the previous selected version;
2. identify added/changed/removed passages;
3. re-extract affected passages only where practical;
4. mark old derived assertions/candidates `SUPERSEDED` or stale rather than deleting provenance;
5. calculate affected Objects/Relations/Events/Claims/Beliefs;
6. re-run continuity checks for impacted graph/time/knowledge neighborhoods;
7. calculate KUE/OTA follow-document impact;
8. produce a version delta in the report.

## Continuity domains

Related novels may belong to an explicit shared continuity domain. Initial intended domain includes the Baumeister, Zereya and NOXIA narrative universe repositories/content sets; exact registry identifiers are configuration and must be validated against existing project registry names.

A document in a shared domain is checked against relevant accepted/canonical states from all member works, not only its own book.

## Continuity dimensions

At minimum:

- temporal ordering and dated states/events;
- character age, location and presence;
- object/location/organization state over time;
- relationships and membership;
- technology/science availability at a point in time;
- explicit world rules/canon claims;
- character knowledge and belief at time X;
- reader knowledge/revelation ordering;
- contradictions between source editions and accepted canonical state.

A changed state is not automatically a contradiction. Checks operate on Object -> temporal State -> Event -> State transitions where available.

World truth, character knowledge, character belief and reader knowledge remain distinct.

## Finding lifecycle

Continuity findings are persistent and fingerprinted:

- `OPEN`
- `CONFIRMED`
- `FALSE_POSITIVE`
- `EXPLAINED`
- `RESOLVED`
- `SUPERSEDED`

An `EXPLAINED` finding stores the accepted explanation so the same intentional distinction is not repeatedly reported. A new version may resolve, supersede or regress a prior finding.

## Finding record

Each report finding includes:

- stable finding id/fingerprint;
- class/severity/confidence;
- new source passage and exact version provenance;
- conflicting/relevant existing source passage(s);
- affected objects/events/claims/knowledge states;
- interpretation of the possible problem;
- possible resolutions, clearly marked as proposals rather than decisions;
- lifecycle status;
- whether owner review is required.

Example classes include `POSSIBLE_TEMPORAL_CONFLICT`, `CHARACTER_KNOWLEDGE_CONFLICT`, `STATE_CONFLICT`, `TECHNOLOGY_AVAILABILITY_CONFLICT`, `RELATION_CONFLICT`, `CANON_CLAIM_CONFLICT` and `SOURCE_EDITION_DIVERGENCE`.

## KUE/OTA knowledge impact

Ingest compares extracted accepted candidates against existing KUE/OTA/KG records before creating follow-documents.

Actions are explicit:

- `CREATE`: a new follow-document was actually created under allowed policy.
- `UPDATE`: an existing follow-document received a proposed/applied update under allowed policy.
- `PROPOSE`: a new document/update appears warranted but requires review.
- `NO_CHANGE`: existing record already covers the information.

The system must prefer linking/updating an existing suitable document over proliferating small duplicates.

## Generated Document Manifest

Every created/updated/proposed follow-document is listed with:

- document identifier/type;
- title;
- action (`CREATE`/`UPDATE`/`PROPOSE`);
- reason;
- affected existing document if any;
- source passages and source versions;
- ingest_run_id;
- authority/review state;
- downstream target (KUE/OTA/KG/etc.).

No generated follow-document silently becomes canonical.

## Mandatory Ingest Impact Report

Each completed ingest run has a stable `ingest_run_id` and emits a report containing:

1. **Document & version**: book, project/domain, version, replacement relationship, status, source id/hash.
2. **Processing summary**: passages read/changed, assertions and structured candidates added/changed/superseded.
3. **Version delta**: additions, changes, removals and affected canonical neighborhoods.
4. **Continuity results**: passed checks plus all open/changed/resolved findings with direct source counterparts.
5. **KUE/OTA/KG impact**: create/update/propose/no-change decisions.
6. **Generated Document Manifest**: every follow-document and its provenance.
7. **Finding delta**: new, resolved, explained, unchanged and regressed findings.
8. **Review decisions required**: concise owner decisions still needed.

All generated records carry `ingest_run_id`, allowing reverse traceability from a KUE/OTA/KG derivative to the exact upload/version/passages that caused it.

## V0.1 acceptance requirements

The implementation of the Document Ingest Layer should be extended so that it can support, at minimum:

1. private-by-default source/storage contracts and explicit public-release boundary;
2. stable Book + immutable Version identities and replacement/supersession semantics;
3. published-edition preservation alongside newer working versions;
4. version delta and incremental re-ingest;
5. continuity-domain registry and cross-work validation contract;
6. persistent finding lifecycle including EXPLAINED and RESOLVED;
7. KUE/OTA follow-document impact actions and manifest;
8. mandatory structured + human-readable Ingest Impact Report;
9. reverse provenance via ingest_run_id;
10. deterministic fixtures showing: unchanged replacement is idempotent; changed passage affects only its dependency neighborhood; an intentional explained discrepancy stays suppressed; a corrected new version resolves a prior finding; a proposed follow-document is visible in the manifest without silently becoming canon.
