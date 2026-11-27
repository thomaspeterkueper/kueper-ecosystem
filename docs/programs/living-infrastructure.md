# Living Infrastructure – Programmregistrierung

Status: registriert (2026-11-14)  
Repository: `kueper-ecosystem`  
Registrierung: [`EXT-NOXIA-ECO-20260925-living-infrastructure-integration`](../../external-tasks/done/EXT-NOXIA-ECO-20260925-living-infrastructure-integration.md)  
Betroffene Codes: `ECO`, `ENG`, `KG`, `NXU`, `NOXIA`, `OTA`  
Ausdrücklich zurückgestellt: `noxia-realtime`

## 1. Zweck

Living Infrastructure ist die Integrationsschicht, die Mykologie/Bodenökologie,
geschlossene Lebenserhaltung, Landwirtschaft, Abfall/Recycling, Planetare Evolution
und künftige Ecopoiesis verbindet.

Die Schicht koordiniert gemeinsame Begriffe, konservierte Flüsse und Übergaben
zwischen diesen Domänen. Sie ist keine eigene fachliche Source of Truth und
ersetzt keine der beteiligten Domänen.

## 2. Geltungsbereich

| Baustein | Bedeutung im Programm |
|---|---|
| Mykologie / Bodenökologie | Substrate, Myzel, Bodenleben und Materialkreisläufe als lebende Produktions- und Reparaturprozesse |
| Geschlossene Lebenserhaltung (ECLSS) | Wasser-, Luft- und Nährstoffrückgewinnung als gekoppeltes System; Rückgewinnung ist nicht automatisch logistische Autonomie |
| Landwirtschaft | pflanzliche Produktion, Nährstoffkreisläufe und Ernteflüsse innerhalb derselben Reservoire |
| Abfall / Recycling | Rückführung von Reststoffen in Substrat-, Wasser- und Nährstoffkreisläufe |
| Planetare Evolution | langfristige Geosphäre-Biosphäre-Kopplung als Randbedingung und Kontext |
| Künftige Ecopoiesis | spätere Erweiterung der Integrationsschicht; keine aktuelle Umsetzungszusage |

## 3. Zuständigkeiten

| Domäne | Zuständigkeit | Beitrag |
|---|---|---|
| `kueper-ecosystem` (`ECO`) | Systemweite Governance | Programmregistrierung, Zuständigkeitsverteilung, Querverweise und Routing von Folgearbeiten |
| `kueper-engineering` (`ENG`) | Konservierte Flüsse und Systemverträge | Reservoire und Flüsse für Masse, Wasser, Kohlenstoff/Nährstoffe und Energie; Prozessgrenzen; Einheiten; Fidelität, Resilienz und Schnittstellen zu Energy Grid und Mars Settlement Kernel |
| `kueper-knowledge-graph` (`KG`) | Material- und Prozessidentitäten | Kanonische Entitäten, Relationen und Einheiten für Substrate, Myzel, Kompost, Nährstoffkreisläufe und Wasseraufbereitung; Mapping statt Neudefinition |
| `noxia-universe` (`NXU`) | Historische und kulturelle Konsequenzen | Siedlungsgeschichte, Institutionen, Kultur und Konflikte, die aus lebender Infrastruktur folgen; keine technische Dimensionierung |
| `noxiagame` (`NOXIA`) | Spielerische Schleifen | Player-facing Loops, Balancing, UX und Lernmodule auf Basis stabiler Verträge; keine kanonischen Definitionen |
| `overtime-archive.org` (`OTA`) | Evidenz | Provenienz, Reifegrad, Unsicherheit und Konsolidierung der Forschung, einschließlich früherer Mars-Pilz-Arbeiten |
| `noxia-realtime` | – | erst nach stabilen Verträgen; derzeit nicht adressiert |

## 4. Integrations- und Ableitungsrichtung

```text
OTA-Evidenz → KG-Identitäten → ENG-Systemverträge
                              ├→ NXU-Historie/Kultur
                              └→ NOXIA-Spielschleifen
```

Die Richtung beschreibt Zuständigkeit und bevorzugte Ableitung, keine Pflicht zur
linearen technischen Verarbeitung. Konsumenten referenzieren die Verträge, statt
eigene Ressourcenzähler oder Begriffe zu duplizieren.

## 5. Querverweise zu Nachbarprogrammen

| Nachbarprogramm | Referenz | Verhältnis |
|---|---|---|
| Mycology / Soil Ecology / Ecopoiesis | [`mycology-soil-ecopoiesis.md`](mycology-soil-ecopoiesis.md) | Fachliche Nachbardomäne; Living Infrastructure ist die Integrationsschicht, kein konkurrierendes Programm. Ecopoiesis bleibt Zukunftserweiterung. |
| Planetary Evolution / Deep Time | [`planetary-evolution.md`](planetary-evolution.md) | Liefert langfristige Geosphäre-Biosphäre-Randbedingungen; Living Infrastructure arbeitet auf Siedlungs- und Engineering-Zeitskalen. |
| Mars Settlement Systems Kernel | [`mars-settlement-kernel.md`](mars-settlement-kernel.md) | Übergeordnete Integrationsautorität für Siedlungssysteme; Living Infrastructure nutzt gemeinsame Reservoire und erzeugt keine doppelten Ressourcenzähler. |
| Energy Grid Layer | [`energy-grid.md`](energy-grid.md) | Energieflüsse und Schnittstellen werden geteilt, nicht parallel modelliert. |
| Adaptive Industry | [`adaptive-industry.md`](adaptive-industry.md) | Material- und Prozessschnittstellen teilen KG-Identitäten und ENG-Verträge. |
| Robotics / MiniNode | [`robotics-mininode.md`](robotics-mininode.md) | Physische Operationen und Automatisierung konsumieren die Flussverträge; keine Voraussetzung für die Registrierung. |
| Geschlossene Lebenserhaltung, Landwirtschaft, Abfall/Recycling | [`reviews/2026-11-13-KUE-SCI-0172-2026-DE.md`](../../reviews/2026-11-13-KUE-SCI-0172-2026-DE.md) | Noch kein eigenes Programm-Request; als Bausteine hier und im Mars Settlement Kernel geführt. Evidenzhoheit bleibt OTA. |
| Myzelbaustoffe / naturverbundenes Bauen | [`reviews/2027-10-10-myzelbaustoffe-naturverbundenes-bauen.md`](../../reviews/2027-10-10-myzelbaustoffe-naturverbundenes-bauen.md) | Bestehender Querbezug zu ENG (`MYCO-0001`) und NXU; zeigt vorhandene Myzel-Forschung und wird 2027 überprüft. |
| `noxia-realtime` | – | Keine Adressierung, bis stabile Verträge vorliegen. |

## 6. Regeln und Abgrenzungen

- Living Infrastructure ist keine neue Source of Truth. Die Zuständigkeiten aus
  [`docs/source-of-truth.md`](../source-of-truth.md) bleiben unverändert.
- Gemeinsame Reservoire und Flüsse werden referenziert; kein Baustein führt
  eigene, konkurrierende Ressourcenzähler ein.
- Die epistemische Regel bleibt erhalten: physische Realität ≠ Beobachtung ≠
  Schätzung/Modell ≠ Akteurswissen.
- Frühere Mars-Pilz-Forschung wird nicht als abwesend behandelt. Repository-Suchen
  vom 25.09.2026 fanden unter den offensichtlichen Begriffen nichts; Abwesenheit
  in diesen Suchen ist kein Nachweis von Nichtexistenz. Möglich sind externe,
  anders benannte oder noch nicht migrierte Bestände. OTA konsolidiert den Stand.
- Cross-Repository-Änderungen laufen ausschließlich als External Tasks; dieses
  Repository ändert keine fremde Source of Truth.
- `noxia-realtime` wird erst adressiert, wenn stabile Verträge existieren.

## 7. Folgearbeiten und Meilensteine

Am 14.11.2026 zur Weiterleitung als External Tasks in `.kueper/outbox/` gestellt
(das Routing in die Ziel-Repositories übernimmt der Ecosystem-Loop):

- `ENG`: Vertrag für konservierte Flüsse und Systemgrenzen (Voraussetzung für alle
  weiteren Bausteine) – **erledigt (15.11.2026):** `ENG-LICF-r1` / `ENG-SYS-LICF-0001`,
  Status `baseline`, in `kueper-engineering/systems/living-infrastructure-conserved-flow-contract-r1.json`
  mit Begleitdokument `systems/living-infrastructure-conserved-flow-architecture-r1.md`.
  Source of Truth bleibt `kueper-engineering`; hier nur der Verweis.
- `KG`: kanonische Material- und Prozessidentitäten – **erledigt (15.11.2026):**
  `EXT-ECO-KG-20261114-001`, Export
  `kueper-knowledge-graph/exports/ontology-living-infrastructure-0.1.json`.
  Source of Truth bleibt `kueper-knowledge-graph`.
- `OTA`: Evidenzkonsolidierung und Provenienz, einschließlich der offenen Frage
  früherer Mars-Pilz-Bestände – **erledigt (27.11.2026):** `EXT-ECO-OTA-20261114-001`,
  Evidenzprofil `overtime-archive.org/docs/research/OTA-EVIDENCE-LIVING-INFRASTRUCTURE-2026-11.md`
  (Arbeitsindex, nicht kanonisch; nächste Prüfung spätestens 27.05.2027). Es
  referenziert den ENG-Flussvertrag (`ENG-LICF-r1`) und den KG-Export
  `ontology-living-infrastructure-0.1.json` und führt „nicht gefunden“
  ausdrücklich als Suchergebnis, nicht als Abwesenheitsnachweis (§6).

Meilenstein „stabile Verträge“: Der ENG-Flussvertrag und die KG-Identitäten liegen
vor und werden vom OTA-Evidenzprofil referenziert.
**Stand 28.11.2026: erreicht** – alle drei Teile liegen vor (ENG-Flussvertrag
15.11.2026, KG-Export 15.11.2026, OTA-Evidenzprofil 27.11.2026 mit Verweis auf
beide). Festgestellt im Ökosystem-Kreislauf zu
[`EXT-OTA-ECO-20261127-001`](../../external-tasks/done/EXT-OTA-ECO-20261127-001.md).
Vorbehalt: Der ENG-Vertrag hat Status `baseline` und der KG-Export Version 0.1 –
stabil heißt referenzierbar und versioniert, nicht validiert. Konsumenten binden
sich an die genannte Revision und zählen nicht selbst.

Damit freigegeben (28.11.2026):

- `NXU` und `NOXIA`: Die Folgearbeiten sind freigegeben und am 28.11.2026 als
  Umschläge in `.kueper/outbox/` gestellt (Routing in die Ziel-Repositories durch
  den Ecosystem-Loop): NXU für Siedlungsgeschichte, Institutionen und Kultur,
  NOXIA für Spielschleifen und Lernmodule – beide gebunden an `ENG-LICF-r1` und
  `ontology-living-infrastructure-0.1.json`, ohne eigene Begriffe oder Zähler.

Weiterhin nicht adressiert:

- `noxia-realtime`: ausdrücklich erst nach validierten, nicht nur stabilen
  Verträgen; die Zurückstellung aus der Registrierung bleibt bestehen.
