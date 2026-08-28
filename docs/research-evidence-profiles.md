# KUEPER Research Evidence Profiles

The research loop uses project-specific evidence profiles from `research/policy.json`. The profile is selected during knowledge-gap discovery, stored on the queue item, passed to the Exa external-evidence scout and re-applied by the synthesis/validation stage.

## Profiles

- `science` — OTA and SSF. Strong bias toward peer-reviewed literature, original datasets, collaboration publications and official institutions.
- `avi-theoretical-cosmology` — AVI (Axiomatisches Vakuum Integral). Separates established cosmology, model postulate, derived consequence, interpretation and falsifiable prediction; metaphysical analogy is never physical evidence.
- `technical-scientific` — NOXIA. Standards, original technical documentation, engineering literature and official data take precedence over vendor/community claims.
- `historical-linguistic` — Mishkenaz. Separates attestation, archaeological/linguistic reconstruction, comparative inference and fictional extrapolation; relevant source languages are discovery channels.
- `worldbuilding-scientific` — NOXIA Universe, ENDIA and Zereya. Researches real-world constraints first and keeps them distinct from canon and narrative choice.
- `philosophy-comparative` — Omnizedenz and Contracomology. Uses primary philosophical/theological texts and serious scholarship while distinguishing textual fact, scholarly interpretation, comparison and KUEPER-system claims. Source count does not turn a metaphysical position into an empirical finding.
- `general` — fallback/editorial profile for projects without a stronger domain-specific profile.

## Eligible rotation

The research rotation now includes `avi-modell`, `omnizedenz` and `contracomology` in addition to the previously eligible projects. Their weights are deliberately below the most active NOXIA/Mishkenaz streams, so adding them broadens coverage without letting them dominate the daily queue.

## Safety boundary

Exa remains discovery/retrieval only. The selected evidence profile controls source preference and minimum evidence gates; successful search results still enter the Knowledge Graph only as non-canonical research candidates. `auto_canonicalize` remains disabled.
