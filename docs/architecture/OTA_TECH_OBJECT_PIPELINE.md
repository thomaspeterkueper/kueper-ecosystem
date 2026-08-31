# OTA → NOXIA Technical Object Pipeline

Status: operational standard  
Control plane: `kueper-ecosystem`  
Research contract: `research/contracts/ota-tech-object-v1.json`

## Purpose

This pipeline defines how a canonical fictional technical object in the Overtime Archive can be consumed by NOXIA while keeping real-science evidence, canonical object identity and gameplay balancing in separate ownership layers.

It is deliberately not a second object registry and does not duplicate canonical document bodies.

## Ownership

| Layer | Owns | Must not own |
|---|---|---|
| `overtime-archive.org` | canonical fictional technical dossier/body and fictional technical state | shared identity registry; NOXIA balancing; real-science foundation as global SSOT |
| `kueper-knowledge-graph` | stable shared document/object identity, relations and mappings | OTA document body; gameplay balancing |
| `kueper.com/KUE-SCI` | real-science synthesis when a reusable scientific topic warrants publication | fictional object canon; gameplay values |
| `noxiagame` | derived buildable/game representation, costs, production rules, unlocks, UI, events and balancing | canonical OTA body; scientific SSOT |
| `kueper-ecosystem` | control-plane rules, audits, task routing and evidence contracts | domain content body |

## Technical-object selector

A document enters the OTA→NOXIA technical-object inventory only when all of the following are true:

1. `series: TEC`
2. `contexts` contains `noxia`
3. `mappings.noxia` exists

For a valid mapped object the audit additionally requires:

- top-level `objectId`;
- `mappings.noxia.objectId`;
- equality of both object IDs;
- `mappings.noxia.role`;
- uniqueness of `objectId` across mapped OTA-TEC documents.

The document signature remains the document identity. `objectId` is the stable machine-facing object key used to connect the fictional object to consumers and KG identity records.

## Evidence boundary

Research jobs for these objects use `ota-tech-object-v1` and may target only:

- `[R]` real claims;
- `[R-Anker]` real-world anchors;
- `[H]` externally testable hypotheses/constraints;
- `[T]` real premises and engineering constraints of a model.

`[F]`, `[W]`, expressly fictional performance values, narrative stipulations and NOXIA balancing are never treated as externally provable facts.

Every contract-bound research item must be source-pinned with `source_path` and `source_blob_sha` and must carry:

```json
{
  "consumer_impact_policy": {
    "flag_noxia_impact": true,
    "auto_update_noxia": false,
    "balancing_is_out_of_scope": true
  }
}
```

The targeted executor enforces this fail-closed before external research starts.

## Coverage audit

`tools/research/audit-ota-tech-objects.py` is the inventory layer above individual research jobs. It compares the current mapped OTA documents against the research queue and reports four states:

- **covered** — at least one safe `ota-tech-object-v1` research item matches the current exact document blob and the current `objectId`;
- **stale** — contract research exists for the same source path, but not for the current exact blob/object identity;
- **uncovered** — the mapped object has no contract-bound research item yet;
- **invalid** — required OTA→NOXIA mapping metadata is incomplete, inconsistent or duplicates an `objectId`.

`covered` means only that the current revision has contract-bound research coverage. It does not mean every claim is true, every gap has been researched, or any candidate has been canonicalized.

`stale` is expected after a source revision changes. It is a signal for review, not permission to rerun research automatically.

`uncovered` is also informational. The inventory does not create research jobs, consume an external provider, edit OTA, create KG records or modify NOXIA by itself.

## Scheduled audit

`.github/workflows/ota-tech-object-audit.yml` runs the inventory daily and can also be dispatched manually. It:

1. checks out the current ecosystem control plane;
2. checks out the current OTA source;
3. validates mapped-object metadata and contract safety;
4. calculates exact Git blob coverage;
5. publishes an artifact and job summary.

The workflow is read-only with respect to all domain repositories.

## Downstream behavior after evidence changes

A scientific correction may lead, after review, to:

- an OTA dossier revision;
- a KG identity/relation update;
- a KUE-SCI document or revision when the real-science synthesis is independently useful;
- a NOXIA impact task indicating that derived gameplay assumptions should be reviewed.

It must never directly overwrite NOXIA costs, production rates, unlock timing, resource yields or other balancing values.

## Instance/type rule

When an OTA dossier contains both a technical type and an individual instance, instance-only history, damage, modifications, behavior or emergent properties do not become type properties unless a separate canonical decision explicitly promotes them.

## Invariants

1. One canonical body, no duplicated document bodies in NOXIA.
2. Stable shared identity belongs in KG.
3. Real scientific foundations are separable from fictional technical canon.
4. Evidence research is exact-source-revision pinned.
5. Fictional/world stipulations are not scientifically validated by accident.
6. Scientific changes may create consumer impact signals, never automatic gameplay balancing changes.
7. Inventory/audit is read-only and does not imply automatic research or publication.
