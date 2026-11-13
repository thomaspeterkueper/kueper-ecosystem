# Heartbeats und Erreichbarkeits-Monitore

```
Stand:   13.11.2026 – Skript vorhanden, Einbau in Workflows wartet auf Freigabe
Task:    ECO-OPS-20261028-heartbeats
```

## Baustein

`tools/ops/heartbeat.sh <VARIABLENNAME> [success|fail]` ruft die URL aus der genannten Umgebungsvariablen auf. Fehlt sie, passiert nichts (Exit 0). Die URL wird nie ausgegeben; ein nicht erreichbarer Dienst bricht keinen Workflow ab. Tests: `tools/ops/test_heartbeat.py`.

Einbau als letzter Schritt eines Jobs (Vorlage, **noch nicht eingebaut**):

```yaml
      - name: Heartbeat
        if: success()
        env:
          HEARTBEAT_GOVERNANCE_SWEEP: ${{ secrets.HEARTBEAT_GOVERNANCE_SWEEP }}
        run: tools/ops/heartbeat.sh HEARTBEAT_GOVERNANCE_SWEEP
      - name: Heartbeat (Fehler)
        if: failure()
        env:
          HEARTBEAT_GOVERNANCE_SWEEP: ${{ secrets.HEARTBEAT_GOVERNANCE_SWEEP }}
        run: tools/ops/heartbeat.sh HEARTBEAT_GOVERNANCE_SWEEP fail
```

## Intervalle (Stand 13.11.2026)

Die Task nannte Agent Worker, PR Review und Knowledge Research Loop. Diese drei Workflows sind seit 13.11.2026 abgeschaltet und durch Claude-Läufe ersetzt (`claude-laeufe.md`). Sinnvolle Heartbeats sind deshalb jetzt:

| Heartbeat-Secret | Lauf | Takt | Grace-Zeit beim Dienst |
| --- | --- | --- | --- |
| `HEARTBEAT_GOVERNANCE_SWEEP` | `governance-sweep.yml` | täglich 06:05 UTC | 2 h |
| `HEARTBEAT_AUTONOMOUS_LOOP` | `autonomous-loop.yml` (nur noch Routing) | alle 15 Min. | 30 Min. |
| `HEARTBEAT_OTA_AUDIT` | `ota-tech-object-audit.yml` | täglich 04:47 UTC | 2 h |
| – | Claude-Lauf „Ökosystem-Kreislauf“ | alle 3 h | Heartbeat nur möglich, wenn der Lauf eine URL kennen darf (siehe Rückfrage in der Task) |
| – | Claude-Lauf „Ökosystem-Recherche“ | täglich 06:11 | wie oben |

Erreichbarkeits-Monitore (beim Dienst, ohne Code): noxiagame (Produktion), thomas-kueper.de, kueper.com, ecosystem-Dashboard, solarsciencefoundation (`https://solarsciencefoundation.vercel.app`).

## Status-Collector

`status/snapshot.json` trägt `generated_at: 2026-07-19`. Grund: `tools/collector/collect.py` wird von **keinem** Workflow aufgerufen; der Snapshot entstand einmalig von Hand. Der Live-Zustand kommt seither aus `app/api/status/route.ts`, das dieselben Prüfungen (Erreichbarkeit, Pflichtpfade, offene Tasks, Integrationen) bei jedem Aufruf direkt gegen die GitHub-API rechnet. `snapshot.json` ist damit ein historisches Artefakt; siehe Vermerk in `status/README.md`.
