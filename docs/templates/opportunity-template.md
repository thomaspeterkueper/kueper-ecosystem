# Opportunity-Datensatz – Vorlage v0.1

> **Nicht** in `external-tasks/open/` speichern: das ist ausschließlich für kanonische projektübergreifende Entwicklungsanforderungen reserviert. Der operative Ablageort wird im Zuge von Issue #131 festgelegt.

```yaml
id: null                         # OPP-YYYY-NNNN erst nach Freigabe des ID-Raums (siehe docs/opportunities-governance.md, „ID-Vergabe“)
title: ""
type: prize                      # grant | prize | collaboration | publication
organizer: ""
official_url: ""
source_checked_at: null          # ISO-8601 inklusive Zeitzone; null nur solange eligibility: unclear
status: discovered               # discovered | screening | prioritized | preparing | submitted | awarded | rejected | archived
eligibility: unclear             # eligible | partner_required | ineligible | unclear
eligibility_reason: ""
eligibility_checked_at: null     # ISO-8601 inklusive Zeitzone; null nur solange eligibility: unclear
projects: []                     # IDs aus registry/projects.json (z. B. knowledge-graph, noxia)
topics: []
call_round: null                 # Ausschreibungsrunde/Ausgabejahr; Teil des Dedup-Schlüssels
owner: ""                        # interne Zuständigkeit für die nächste Entscheidung
effort: unknown                  # low | medium | high | unknown
effort_note: ""
assessment:                      # je Dimension rating: low | medium | high | unknown, plus reason
  research_fit: {rating: unknown, reason: ""}
  validation_level: {rating: unknown, reason: ""}
  benefit: {rating: unknown, reason: ""}
  visibility: {rating: unknown, reason: ""}
  collaboration_potential: {rating: unknown, reason: ""}
  ip_risk: {rating: unknown, reason: ""}
status_history: []               # je Eintrag: at, by, from, to, reason
deadline_at: null                # ISO-8601 mit Zeitzone; null wenn Uhrzeit/Zone nicht bestätigt
funding_amount: null
currency: null
country: null
language: null
contact: null                    # externer Ansprechpartner (dienstlich, aus offizieller Quelle)
degree_requirements: null
publication_requirements: null
institution_requirements: null
partner_requirements: null
residency_requirements: null
legal_form_requirements: null
allowed_ai_use: null
ip_terms: null
submission_url: null
evidence_refs: []
notes: ""
next_action: ""
last_reviewed_at: null
```

Prüfcheckliste: offizielle Quelle geprüft; formale Kriterien einzeln geprüft; KI- und IP-Regeln geprüft; Frist samt Zeitzone belegt; Forschungsstand korrekt eingeordnet; Entscheidung und Begründung dokumentiert.
