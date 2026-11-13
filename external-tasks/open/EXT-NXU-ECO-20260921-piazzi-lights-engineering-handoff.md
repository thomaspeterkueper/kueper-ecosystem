---
id: EXT-NXU-ECO-20260921-piazzi-lights-engineering-handoff
title: Piazzi-Lights engineering handoff
status: open
source: NXU
target: ECO
created: 2026-09-21
requested_by: NOXIA Universe (Autorenarbeit)
affects: [ECO, NXU, ENG, OTA, NOXIA]
supersedes: []
---

# EXT-NXU-ECO-20260921-piazzi-lights-engineering-handoff – Piazzi-Lights engineering handoff

## Anlass

Alt-Task ohne kanonisches Format, eingegangen am 2026-09-21 (Herkunft: NOXIA Universe (Autorenarbeit)). Am 13.11.2026 ins Format nach `docs/cross-repository-workflow.md` und ECO-ARC-0006 überführt (ECO-OPS-20261113-legacy-task-frontmatter); der ursprüngliche Auftragstext steht unverändert unter „Gewünschte Änderung“. Die `id` entspricht bewusst dem bisherigen Dateinamen, damit der Idempotenzschlüssel im Task-Bus gleich bleibt.

## Gewünschte Änderung

### Status

NOXIA authorial work has handed remaining technical closure for **Piazzi-Lights / Ceres 2091** to `kueper-engineering`.

### Engineering owner

Primary request:

`kueper-engineering/external-tasks/open/EXT-NXU-ENG-20260921-piazzi-lights-technical-closure.md`

Supporting engineering artifacts:

- `ENG-CAL-0015-ceres-piazzi-lights-2091-backcast-r0.1.md`
- `ENG-CAL-0016-piazzi-lights-180m-torus-r0.1.md`
- `ENG-CAL-0004-artificial-gravity-parameter-model.md`
- `gravity-human-environment-architecture-r1.md`
- reproductive/obstetric/neonatal low-g architecture

NOXIA source:

`noxia-universe/spaces/noxia/infrastructure/NXU-CERES-PIAZZI-LIGHTS-2091.md`

### Current authorial anchors

Until Engineering returns closure, the ecosystem should treat the following as **provisional-selected authorial parameters**, not closed technical facts:

- Piazzi-Lights permanent population 2091: ~120 (working band ~100–140)
- Belt/Ceres/other 2091: ~130–140
- child/youth cohort: ~8–15 under 18
- settlement is strongly automated, cargo-heavy and passenger-light
- existing `~180 m torus` retained provisionally
- preferred current geometry interpretation: 180 m major diameter / ~90 m major radius / ~18 m tube class
- provisional occupied floor radius ~99 m
- provisional 1 g-class reference ~3.0 rpm
- stationary local shielding around the rotating pressure habitat is preferred
- no biological claim that a particular g/rpm/exposure schedule is safe for pregnancy or lifelong development

### Ecosystem routing rule

- Technical questions about structure, bearings/suspension, artificial gravity, shielding, utilities, ECLSS, power, thermal control, ISRU, construction sequence and failure modes route to **KUEPER Engineering**.
- OTA may consume evidence questions where biological/radiation validation is needed.
- NOXIA authorial work consumes the returned engineering envelope but should not continue detailed technical optimization in parallel.
- Game/realtime implementations should not hard-code provisional torus parameters as final until engineering closure is returned.

### Authorial focus after handoff

The NOXIA authorial side is returning to:

- characters;
- relationships;
- society and culture;
- everyday life;
- institutions;
- scenes and plot;
- lived consequences of the established infrastructure.

Please propagate or reference this ownership boundary where cross-repo dependencies arise.

## Begründung

Die Zuständigkeitsgrenze zwischen NOXIA-Autorenarbeit und KUEPER Engineering betrifft mehrere Repositories; ihre Verankerung und Weitergabe ist Governance-Aufgabe von `kueper-ecosystem`.

## Betroffene Repositories

- `kueper-ecosystem`
- `noxia-universe`
- `kueper-engineering`
- `overtime-archive.org`
- `noxiagame`
- `noxia-realtime` (erst nach stabilen Verträgen)

## Erwartetes Ergebnis

- Zuständigkeitsgrenze Piazzi-Lights (NOXIA Universe ↔ Engineering) im Ecosystem dokumentiert bzw. dort referenziert, wo Cross-Repo-Abhängigkeiten entstehen.
- Vorläufige Autorenparameter sind als „provisional-selected“ gekennzeichnet, bis Engineering die technische Schließung zurückmeldet.
