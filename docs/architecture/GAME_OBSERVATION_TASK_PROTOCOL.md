# Game Observation → Task Candidate Protocol

Status: architecture draft

## Purpose

This protocol allows simulations such as NOXIA to act as sensors for the KUEPER Ecosystem without allowing ordinary game events or LLM preferences to mutate repositories directly.

The boundary is:

```text
Game Action -> Observation -> Evidence -> TaskCandidate -> Gate -> Ecosystem Request
```

A Game Action MUST NOT directly create an implementation task.

## Observation envelope

```json
{
  "observation_id": "uuid-or-stable-id",
  "world_id": "noxia-test-001",
  "agent_id": "NOXIA_TESTER_INTELLIGENT_01",
  "kind": "DEAD_END",
  "system": "materials",
  "summary": "Required material has no obtainable acquisition path",
  "evidence": [],
  "reproduction": [],
  "expected": "at least one valid acquisition path",
  "actual": "none",
  "confidence": 0.96,
  "observed_at": "RFC3339"
}
```

Initial kinds:

- `BUG`
- `DEAD_END`
- `BALANCE_ANOMALY`
- `UX_FRICTION`
- `SCIENCE_GAP`
- `KNOWLEDGE_GAP`
- `CONTENT_GAP`
- `RESOURCE_UNUSED`
- `AI_BEHAVIOR`
- `PROPOSAL`

## Candidate gate

Observations are accumulated and deduplicated before becoming TaskCandidates. The gate evaluates:

- reproducibility;
- evidence quality;
- confidence;
- number of independent occurrences/agents/worlds;
- whether an existing open/parked/done request already covers the condition;
- cooldown since the last emitted candidate;
- target ownership;
- whether the condition is a defect/gap or merely a design preference.

A single subjective preference MUST NOT create an implementation task.

`BUG` and `DEAD_END` may pass after one high-confidence reproducible occurrence. `BALANCE_ANOMALY`, `RESOURCE_UNUSED`, `AI_BEHAVIOR` and `UX_FRICTION` SHOULD normally require aggregation. `PROPOSAL` MUST be parked for owner/design review and MUST NOT autonomously enter implementation.

## TaskCandidate

```json
{
  "candidate_id": "stable-fingerprint",
  "source": "NOXIA",
  "target": "NOXIA",
  "type": "BUG",
  "title": "NdFeB acquisition path missing",
  "reason": "Reproducible progression blocker in autonomous test world",
  "requested_change": "Investigate and repair the missing acquisition path without bypassing canonical game rules.",
  "expected_result": "A legal acquisition/production path exists when prerequisites are met.",
  "evidence_refs": ["..."],
  "occurrences": 3,
  "confidence": 0.97,
  "cost_policy": "immediate",
  "estimated_effort": "medium"
}
```

After the gate, the candidate is converted to the existing `.kueper/outbox` routing envelope. The existing router remains the only cross-project request boundary.

## Target examples

- Game defect or progression dead end -> `NOXIA`
- Missing canonical concept/data -> `KG`
- Missing science/learning investigation -> `SSF`
- Universe/canon inconsistency -> `NXU`

The observation producer may suggest a target. The gate/router MUST validate ownership against the Ecosystem registry.

## Cost policy

Default mapping:

- reproducible blocking `BUG` / `DEAD_END`: `immediate`
- `SCIENCE_GAP`, `KNOWLEDGE_GAP`, `CONTENT_GAP`: `prefer_off_peak`
- aggregated balance/AI/UX analysis: `prefer_off_peak`
- long simulation/session synthesis: `off_peak_only`
- `PROPOSAL`: no autonomous execution

Routine gameplay decisions SHOULD be deterministic/rule-based where practical. LLM use is reserved for planning, reflection, anomaly classification and complex synthesis.

## Safety and noise controls

- stable fingerprint/idempotency key per underlying condition;
- cooldown per fingerprint;
- bounded candidate emissions per world/session;
- evidence retained independently of generated prose;
- no source-code access required for the runtime tester;
- no direct repository mutation from the game process;
- no automatic merge;
- no canon/design/balance invention from a single agent observation;
- every emitted request retains world, agent and evidence provenance.

## NOXIA producer v0.1

The first NOXIA integration should implement:

1. a local observation sink used by the autonomous tester and deterministic game assertions;
2. stable fingerprints and occurrence aggregation;
3. `BUG` and `DEAD_END` gates first;
4. an outbox producer that emits valid KUEPER routing envelopes;
5. deterministic tests showing duplicate observations collapse into one candidate/request;
6. no direct GitHub/Supabase write from gameplay code; repository routing remains an Ecosystem responsibility.

Later versions may aggregate multiple autonomous tester personalities and long-lived worlds before promoting balance, AI-behavior or science-gap candidates.
