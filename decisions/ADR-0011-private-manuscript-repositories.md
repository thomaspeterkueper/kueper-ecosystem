# ADR-0011 — Private manuscript repositories

Status: Proposed
Date: 2026-08-24

## Context

The ecosystem now has access to `thomaspeterkueper/buecherwelten`, a private repository intended for manuscripts, scenes, chapter states and cross-book continuity material. Existing project-registry roles do not distinguish confidential authoring sources from public archives, websites or knowledge platforms.

Private manuscript material must be useful to Document Ingest and continuity analysis without silently becoming public, canonical, or reusable as a publication source.

## Decision

Introduce the logical repository class `private-manuscript-source`.

The first repository in this class is:

- repository: `thomaspeterkueper/buecherwelten`
- owner: author-controlled
- visibility: private
- trust: trusted source for manuscript analysis, but not a canonical publication source
- ingest: allowed
- continuity/findings: allowed
- automatic canonization: forbidden
- automatic publication/export to public repositories: forbidden
- automatic KG/OTA promotion: forbidden

Document Ingest may read supported documents from this class and create private analysis artifacts. Findings, continuity candidates, entity candidates and relation candidates must remain non-canonical until an explicit promotion decision exists.

No agent may copy manuscript prose or derived private content into `kueper-knowledge-graph`, `overtime-archive.org`, `kueper.com`, `thomas-kueper.de`, or another public repository merely because an integration exists.

Cross-repository tasks originating from a private manuscript source must carry provenance and confidentiality metadata. Public-target tasks must default to blocked/manual-approval unless their payload contains no manuscript text and no private derived content.

## Registry implementation

The project registry schema must be extended in a backward-compatible schema revision before `buecherwelten` is enabled as a monitored project. The revision should model at least:

- repository class / data sensitivity
- ingest permission
- canonization permission
- public-export permission
- derived-analysis permission

Until that schema revision is implemented, this ADR is the governing policy and `buecherwelten` must not be forced into an inaccurate existing role.

## Operational expectation

Document Ingest should treat changes in `buecherwelten` as input events for private analysis. It may produce non-canonical continuity findings and structured candidates. Promotion into canonical or public stores always requires an explicit later decision.

## Security invariant

`private source -> public target` is deny-by-default.

A workflow that cannot prove the target is private/non-public must not export content from this repository class.
