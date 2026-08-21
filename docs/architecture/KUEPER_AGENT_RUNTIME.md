# KUEPER Agent Runtime

Status: architecture draft

## Purpose

The KUEPER Agent Runtime is the common execution model for persistent autonomous agents across the ecosystem. It generalizes the existing project/worker loop so repository agents, NOXIA actors and persistent fictional characters can share one conceptual architecture without sharing inappropriate capabilities.

An agent is not defined by an LLM. It is defined by a persistent state, bounded perception, goals, memory, capabilities, allowed actions and a loop that turns observations into validated actions.

## Core loop

```text
PERCEIVE -> INTERPRET -> SELECT GOAL -> PLAN -> PROPOSE ACTION
    ^                                           |
    |                                           v
MEMORY <- REFLECT <- OBSERVE RESULT <- VALIDATE/EXECUTE
```

The runtime MUST separate reasoning from authority. An agent proposes actions; an authoritative adapter validates and executes them. An LLM MUST NOT directly mutate canonical world state, repository main branches, economic state or narrative canon.

## Agent state

Every persistent agent has at least:

- `agent_id` and `agent_type`
- `world_id` / execution domain
- current goals and priorities
- bounded working state
- persistent memories
- beliefs with provenance/confidence where applicable
- relationships where applicable
- commitments and unresolved intentions
- capability profile
- action budget / loop guards
- inbox of observable events
- audit trail of decisions and actions

World truth and agent belief are distinct. A character or game agent may be wrong. The authoritative world model is never overwritten merely because an agent believes something.

## Events and observations

The runtime is event-oriented. Agents receive observations derived from authoritative events. Visibility rules determine what an agent can know.

```text
WORLD EVENT -> VISIBILITY/PERCEPTION FILTER -> AGENT OBSERVATION -> BELIEF/MEMORY UPDATE
```

This maps naturally to the KUEPER Object-Relation-Event narrative model: objects have time-dependent state, relations connect objects, events change state, and agents only perceive a permitted projection of those events.

## Actions

Actions use typed envelopes. Example:

```json
{
  "action": "request_trade",
  "target": "supplier_2",
  "resource": "NdFeB",
  "amount": 12
}
```

The domain adapter checks existence, permissions, prerequisites, budgets and invariants before changing state. Rejected actions become observations and may cause replanning.

## Reflection and memory

Immediate action and slower reflection are separate loops. Reflection may consolidate memories, revise beliefs, change priorities and create bounded intentions. Reflection MUST NOT create unbounded recursive work.

Loop guards include:

- maximum actions per cycle
- maximum spawned intentions/follow-ups
- cooldowns
- attention/token/cost budgets
- importance thresholds
- maximum derivation depth
- deterministic deduplication keys

## Agent classes

### Project Agent

Domain: GitHub repositories and the KUEPER task bus.

May inspect repositories, execute bounded implementation tasks, run validation, create branches/PRs and emit concrete cross-project follow-ups. It may not merge autonomously unless policy explicitly grants that capability. The current V7.x Ecosystem Worker is the first implementation of this class.

### NOXIA Autonomous Tester

Domain: a dedicated NOXIA test world.

The tester MUST use the same public gameplay action surface as a human player wherever practical. It has no source-code access while playing. Its purpose is to pursue game goals continuously and discover failures through use rather than through static code inspection.

Initial profile: `NOXIA_TESTER_INTELLIGENT_01`.

It should be capable of:

- building, researching, trading and managing resources;
- selecting and revising long-term strategies;
- remembering prior attempts and outcomes;
- exploring alternative legal strategies when blocked;
- recording reproducible anomalies;
- continuing across long simulations rather than restarting after every session.

A later test population may contain scientist, economist, builder, ecological and exploratory strategies plus a legal-action chaos profile.

### Persistent Character Agent

Domain: a fictional world such as ENDIA.

Example: Sun. The character can maintain memories, beliefs, relationships, intentions and unresolved questions between conversations/scenes. It can act only through narrative/world capabilities exposed to it. It cannot rewrite canon or learn omniscient world facts that were not observable to the character.

## NOXIA anomaly pipeline

The autonomous tester is both player and sensor, but not developer.

```text
PLAY -> OBSERVE RESULT -> DETECT ANOMALY -> REPRODUCE/CHECK -> REPORT
                                                     |
                                                     v
                                             ECOSYSTEM TASK BUS
                                                     |
                              +----------------------+-------------------+
                              v                      v                   v
                           NOXIA BUG              KG GAP              SSF GAP
```

A report should contain at least:

```json
{
  "type": "GAMEPLAY_ANOMALY",
  "severity": "blocking",
  "system": "materials",
  "observation": "Required material has no obtainable acquisition path",
  "reproduction": ["..."],
  "expected": "at least one valid acquisition path",
  "actual": "none",
  "confidence": 0.96,
  "evidence": []
}
```

Triage distinguishes executable defects from design proposals.

- `BUG`: reproducible violation of an implemented rule/invariant; may create a development task.
- `DEAD_END`: no legal progression path; may create a bounded investigation task.
- `BALANCE`: systematic dominance/pathology; analysis first, no automatic design change.
- `UX_FRICTION`: required information/action is unreasonably inaccessible; analysis first.
- `KNOWLEDGE_GAP`: canonical concept/data missing; route to Knowledge Graph when evidenced.
- `CONTENT_GAP`: required learning/content layer missing; route to SSF when evidenced.
- `PROPOSAL`: optional new mechanic/idea; MUST NOT enter autonomous implementation. Park for owner/design review.

The tester MUST NOT convert subjective preference directly into a bug.

## Cross-domain task generation

The same derived-task rule used by the Ecosystem Loop applies to all agents:

1. A follow-up must be grounded in an observed state/result.
2. It must be necessary to complete or repair the current objective, not merely interesting.
3. Target ownership must be known.
4. Evidence and provenance must travel with the request.
5. Idempotency prevents repeated reports of the same unresolved condition.
6. Creative, strategic or canon-changing decisions are parked for human review.

Thus a NOXIA tester may autonomously report a reproducible broken production chain, but it may not decide that NOXIA should gain a new gameplay system merely because that would be interesting.

## Runtime boundary

The generic runtime owns:

- agent lifecycle
- event inbox
- state/memory interfaces
- goal/intention representation
- action envelopes
- budgets and loop guards
- provenance/audit records
- derived-request protocol

Domain adapters own:

- authoritative state
- visibility rules
- legal actions
- validation and execution
- domain-specific invariants

LLM/provider adapters own only interpretation, planning, reflection and language generation. Provider identity (DeepSeek, another model, deterministic planner) is therefore replaceable and is not part of agent identity.

## Implementation sequence

1. Extract the current Ecosystem worker concepts into generic `Agent`, `Event`, `Observation`, `Intent`, `Action`, `Result` and `MemoryRecord` contracts.
2. Keep the existing project worker behavior as the compatibility/reference adapter.
3. Define the NOXIA gameplay action API and a read-only observation/state projection.
4. Implement `NOXIA_TESTER_INTELLIGENT_01` in a disposable test world with persistent memory.
5. Add anomaly classification, evidence capture, deduplication and routing into `ecosystem.tasks`.
6. Run long-lived simulations and measure progression, repeated failures, action diversity, cost and false-positive request rate.
7. Only after the runtime is stable, implement a persistent ENDIA character such as Sun using character-specific perception and canon guards.

## Success criterion

The runtime succeeds when the same lifecycle and safety model can support a repository worker, a NOXIA test player and a persistent fictional character while each remains constrained by its own world, knowledge and capabilities.
