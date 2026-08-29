#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'ota')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one occurrence, found {count}')
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# OTA-FND-0030 — epistemic cleanup + current AVI boundary
# ---------------------------------------------------------------------------
fnd_path = root / 'src/content/documents/OTA-FND-0030-2026-DE.md'
fnd = fnd_path.read_text(encoding='utf-8')
fnd = replace_once(fnd, 'version: "v1.0"', 'version: "v1.1"', 'FND frontmatter version')
fnd = replace_once(fnd, '| **Version:**             | 1.0                                            |', '| **Version:**             | 1.1                                            |', 'FND document version')
fnd = replace_once(
    fnd,
    '| **[F]** | Fiktiv | Saga-interne Physik | NOXIA-Universum |\n\n**Zusätzliche Marker:**',
    '| **[F]** | Fiktiv | Saga-interne Physik | NOXIA-Universum |\n| **[W]** | Werk-Setzung | Autorielle, kulturelle oder kanonische Ordnungsregel; extern nicht empirisch prüfbar | Werkebene |\n\n**Zusätzliche Marker:**',
    'FND W marker',
)
fnd = replace_once(
    fnd,
    '''### §2.3 Funktional-Charakter

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│           Φ(a) = ℱ[Vakuumgeschichte bis a]              │
│                                                         │
│          Nicht-markovsch, komprimiertes Gedächtnis [T]  │
└─────────────────────────────────────────────────────────┘
```''',
    '''### §2.3 Historienseparation als offener Modelltest

AVI setzt gegenwärtig **nicht** voraus, dass Φ unmittelbar als Funktion einer „Vakuumgeschichte“ definiert werden kann. Der aktuelle Modelltest fragt zuerst, ob der gegenwärtige kosmologische Zustand `Y` zur Beschreibung genügt oder ob zwei dynamisch zulässige Historien bei gleichem `Y` physikalisch unterscheidbar bleiben.

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│                    Z_AVI = (Y, ξ)                       │
│                                                         │
│       Erweiterter Zustandsansatz als Modelltest [T/H]   │
└─────────────────────────────────────────────────────────┘
```

`ξ` bezeichnet dabei einen **noch nicht ontologisch festgelegten zusätzlichen Zustandsanteil**. Erst wenn gezeigt werden kann, dass `Y` unvollständig ist und ein solcher Zusatz eine beobachtbare Differenz trägt, darf diese Information in nachgelagerte Größen wie `Q`, `Φ` oder eine AVI-Kopplung eingehen. Eine irreduzible Nicht-Markovschheit ist damit **nicht vorausgesetzt**, sondern Gegenstand des Tests.''',
    'FND AVI history model',
)
fnd = replace_once(
    fnd,
    '| **Kran** | ◇ | Struktur, Ordnung, Emergenz | Komplexität | [R] |\n| **Ira** | ∿ | Impuls, Energie, Dynamik | Thermodynamik | [R] |',
    '| **Kran** | ◇ | Struktur, Ordnung, Emergenz | Komplexität | [F/R-Anker] |\n| **Ira** | ∿ | Impuls, Energie, Dynamik | Thermodynamik | [F/R-Anker] |',
    'FND Kran/Ira table',
)
fnd = replace_once(
    fnd,
    '**Kran (◇) — Struktur:** Das Ordnungsprinzip. Emergente Strukturbildung — von Kristallen bis zu Galaxien. Standardphysik [R].\n\n**Ira (∿) — Impuls:** Das dynamische Prinzip. Energie, Bewegung, Veränderung. Standardphysik [R].',
    '**Kran (◇) — Struktur:** Das Ordnungsprinzip der Hexade [F]. **Realer Anker [R]:** Strukturbildung von Kristallen bis zu Galaxien wird mit etablierter Festkörper-, statistischer und astrophysikalischer Physik beschrieben. Die Zusammenfassung dieser Prozesse im Operator „Kran“ ist jedoch eine NOXIA-Werksetzung.\n\n**Ira (∿) — Impuls:** Das dynamische Prinzip der Hexade [F]. **Realer Anker [R]:** Impuls, Energie und thermodynamische Dynamik sind etablierte physikalische Größen und Gesetze. Ihre Bündelung im Operator „Ira“ ist eine NOXIA-Werksetzung.',
    'FND Kran/Ira definitions',
)
fnd = replace_once(
    fnd,
    '*Die 0,7-Hz-Frequenz steht in der NOXIA-Kultur in Beziehung zur 12-Hz-Resonanz: 12 Hz / 17,14 ≈ 0,7 Hz. In der realen AVI-Theorie hat diese Zahl keine Entsprechung.*',
    '*Die 0,7-Hz-Frequenz steht in der NOXIA-Kultur in Beziehung zur 12-Hz-Resonanz. Diese Beziehung ist eine kulturelle und gestalterische Zuordnung, keine physikalische Herleitung. In der realen AVI-Theorie hat diese Zahl keine Entsprechung.*',
    'FND circular ratio',
)
fnd = replace_once(
    fnd,
    '| 7,83 Hz | Schumann-Resonanz | Erdgebundene Referenz | [R] |',
    '| ≈ 7,83 Hz | Schumann-Grundmode (Nominalwert) | Erdgebundene Referenz | [R-Anker] |',
    'FND Schumann hierarchy',
)
fnd = replace_once(
    fnd,
    'Die Schumann-Resonanz (7,83 Hz) ist ein reales geophysikalisches Phänomen [R]. Sie steht **außerhalb** der harmonischen NOXIA-Hierarchie — ein bewusster Bruch, der anzeigt, dass die Erde nicht vollständig in die χ-Feld-Struktur integriert ist.',
    'Die Schumann-Resonanz ist ein reales geophysikalisches Phänomen [R]. **7,83 Hz ist ein üblicher Nominalwert der Grundmode, keine Fundamentalkonstante**; die reale Resonanzfrequenz variiert mit den Eigenschaften der Erde-Ionosphären-Kavität. In der NOXIA-Hierarchie dient der Nominalwert ausschließlich als [R-Anker]. Sie steht **außerhalb** der harmonischen NOXIA-Hierarchie — ein bewusster Bruch, der anzeigt, dass die Erde nicht vollständig in die χ-Feld-Struktur integriert ist.',
    'FND Schumann explanation',
)
fnd = replace_once(fnd, '# TEIL VI: KONSTANTEN\n\n## §7 Kanonische Konstanten', '# TEIL VI: REFERENZWERTE UND KANONISCHE KONSTANTEN\n\n## §7 Referenzwerte und kanonische Konstanten', 'FND constants heading')
fnd = replace_once(
    fnd,
    '| Schumann-Resonanz | f_Sch | 7,83 | Hz | — | [R] |',
    '| Schumann-Grundmode (Nominalwert) | f_Sch | ≈ 7,83 | Hz | Realanker | [R-Anker] |',
    'FND constants row',
)
fnd = replace_once(
    fnd,
    '| 2026-05-09 | Erstellung als OTA-FND-0030-2026-DE v1.0. Umklassifizierung der ehemaligen "Formelsammlung" von SCI zu FND. Korrekturen: χ-Formel auf sechste Wurzel, Marker vereinheitlicht, Numerologie als kulturelle Bedeutung [F] markiert, Schicht-Architektur explizit, Verweis auf OTA-SCI-0001 als theoretische Basis. |',
    '| 2026-05-09 | Erstellung als OTA-FND-0030-2026-DE v1.0. Umklassifizierung der ehemaligen "Formelsammlung" von SCI zu FND. Korrekturen: χ-Formel auf sechste Wurzel, Marker vereinheitlicht, Numerologie als kulturelle Bedeutung [F] markiert, Schicht-Architektur explizit, Verweis auf OTA-SCI-0001 als theoretische Basis. |\n| 2026-08-29 | v1.1 Evidenz-Audit: [W] explizit definiert; AVI-Historienseparation auf `Z_AVI=(Y,ξ)` als offenen Modelltest aktualisiert; keine Definition von ℱ über „Vakuumgeschichte“; Kran/Ira als fiktive Operatoren mit Realankern präzisiert; Schumann-7,83-Hz als variabler Nominalwert statt Konstante gekennzeichnet; zirkuläre 12/17,14-Herleitung entfernt. |',
    'FND revision',
)
fnd_path.write_text(fnd, encoding='utf-8')

# ---------------------------------------------------------------------------
# OTA-SCI-0037 — source-grounded correction after STAR/CMS audit
# ---------------------------------------------------------------------------
sci_path = root / 'src/content/documents/OTA-SCI-0037-2026-DE.md'
sci = sci_path.read_text(encoding='utf-8')
sci = replace_once(sci, 'version: "v1.0"', 'version: "v1.1"', 'SCI frontmatter version')
sci = replace_once(sci, 'epistemicStatus: ["H", "T", "S", "W"]', 'epistemicStatus: ["R", "H", "T", "S", "W"]', 'SCI frontmatter epistemics')
sci = replace_once(sci, 'summary: "Vakuumresonanz: Quantenvakuum und Nullpunktenergie [T/H], AVI-Modell-Integration [W/S]."', 'summary: "STAR-Lambda-Antilambda-Spinkorrelation [R], QCD-Vakuum-/Dekohärenz-Deutung [T/H], Resonanzrahmen [W/S]; aktualisiert mit CMS-2026-Kreuzvergleich."', 'SCI summary')
sci = replace_once(sci, '**Version:**            1.0', '**Version:**            1.1', 'SCI document version')
sci = replace_once(
    sci,
    '''*Das RHIC-Experiment liefert den bislang direktesten experimentellen
> Zugang zur physikalischen Realität des Quantenvakuums. Die gemessene
> Spinkorrelation von (18 ± 4)% zwischen
> Lambda-Antilambda-Hyperon-Paaren dokumentiert erstmals den
> Informationstransfer vom virtuellen in den realen Zustand. Dieses
> Dokument archiviert die Fakten, ordnet die Interpretationslandschaft
> und legt die Brücke zum Omnizedenz-Resonanzrahmen offen -- mit klarer
> epistemologischer Schichtung. --- T.P.K.*''',
    '''*Das RHIC/STAR-Ergebnis eröffnet einen neuen experimentellen Zugang zur
> Spin-Dynamik während des QCD-Confinements. Gemessen wird eine positive
> Kurzbereichs-Spinkorrelation von (18 ± 4)% zwischen
> Lambda-Antilambda-Hyperon-Paaren. Die STAR-Autoren interpretieren den
> Befund als mit einer Vererbung spin-korrelierter Strange-Quark-Paare aus
> dem QCD-Vakuum vereinbar; ein ontologischer „Transfer vom Virtuellen ins
> Reale“ ist damit jedoch nicht als experimenteller Fakt bewiesen. Dieses
> Dokument trennt Messbefund, QCD-Modellinterpretation und
> Omnizedenz-Resonanzrahmen ausdrücklich. --- T.P.K.*''',
    'SCI curator note 0.1',
)
sci = replace_once(
    sci,
    '''**\\[ESTABLISHED\\]** Das Quantenvakuum ist kein leerer Raum. Seit
Jahrzehnten wissen Physiker, dass es von virtuellen Teilchenpaaren
durchzogen ist, die ständig entstehen und wieder vergehen. Die
Heisenbergsche Unschärferelation für Zeit und Energie (ΔE·Δt ≥ ħ/2)
erlaubt dem Vakuum, kurzzeitig Energie zu „borgen", solange die
Leihfrist kurz genug ist.''',
    '''**\\[ESTABLISHED\\]** In der Quantenfeldtheorie ist das Vakuum der
Grundzustand der Quantenfelder und besitzt eine nichttriviale Struktur.
In der QCD gehört dazu insbesondere das nichtverschwindende
Quarkkondensat. Begriffe wie „virtuelle Teilchen" sind nützliche
Bestandteile perturbativer Beschreibungen, aber keine direkt
beobachtbaren kurzlebigen Teilchen, die aufgrund einer
Energie-Zeit-Unschärferelation Energie „borgen". Diese populäre
Metapher wird hier nicht als physikalischer Mechanismus verwendet.''',
    'SCI vacuum wording',
)
sci = replace_once(
    sci,
    '''**\\[ESTABLISHED\\]** Bei Kollisionen von Protonenstrahlen mit nahezu
Lichtgeschwindigkeit am Relativistic Heavy Ion Collider (RHIC) des
Brookhaven National Laboratory entstehen für Sekundenbruchteile
Bedingungen, wie sie kurz nach dem Urknall herrschten. In diesem
extremen Energiebereich können virtuelle Strange-Quark-Antiquark-Paare
genügend Energie absorbieren, um zu realen Teilchen zu werden -- die
energetische „Schuld" wird durch die Kollisionsenergie beglichen.''',
    '''**\\[ESTABLISHED\\]** Die STAR-Messung verwendet
Proton-Proton-Kollisionen bei √s = 200 GeV am Relativistic Heavy Ion
Collider (RHIC) des Brookhaven National Laboratory. Sie untersucht die
Spin-Korrelation rekonstruierter Lambda-Antilambda-Paare als Sonde der
nichtperturbativen QCD-Hadronisierung. Die häufige Analogie zu
„Urknallbedingungen" gehört primär zur Schwerionen-/QGP-Physik und ist
für diese p+p-Messung keine sachgerechte Beschreibung.

**\\[INTERPRETATION\\]** Im Modellrahmen der STAR-Publikation können
hochenergetische Kollisionen spin-korrelierte Strange-Quark-Antiquark-
Konfigurationen aus dem QCD-Vakuumkondensat zugänglich machen, die
anschließend hadronisieren. Diese Herkunftsdeutung ist theoretisch
motiviert und nicht selbst die gemessene Observable.''',
    'SCI pp collision wording',
)
sci = replace_once(
    sci,
    '''**\\[ESTABLISHED\\]** Die STAR Collaboration berichtet ein relatives
Polarisationssignal von **(18 ± 4)%** zwischen ΛΛ̅-Hyperon-Paaren. Diese
Spinkorrelation verknüpft die spin-verschränkten virtuellen Quark-Paare
aus dem QCD-Vakuum mit ihren Endzustand-Hadron-Gegenstücken.

**\\[ESTABLISHED\\]** Entscheidend: Diese Korrelation verschwindet, wenn
die Hyperon-Paare weit voneinander getrennt sind -- konsistent mit der
Dekohärenz des Quantensystems. Die theoretische Erwartung für reine
chirale Kondensatpaare liegt bei 100% Spin-Alignment; die gemessenen 18%
dokumentieren den partiellen Informationsverlust während der
Hadronisierung.''',
    '''**\\[ESTABLISHED\\]** Die STAR Collaboration misst für kurzreichweitige
ΛΛ̅-Paare eine positive Spinkorrelation
**P_ΛΛ̅ = 0,181 ± 0,035 (stat) ± 0,022 (sys)**, entsprechend einem
relativen Polarisationssignal von rund **(18 ± 4)%**, mit 4,4σ
Signifikanz gegenüber null.

**\\[ESTABLISHED\\]** Bei großer Winkel-/Rapiditätstrennung ist die
Korrelation mit null vereinbar. **\\[INTERPRETATION\\]** Die STAR-Autoren
deuten die Abnahme als mit Dekohärenz oder anderen Wechselwirkungs-
mechanismen vereinbar.

**\\[THEORETISCH / HYPOTHETICAL\\]** Für parallele Spins beträgt das mit
der STAR-Methode maximal messbare Korrelationsmaß P = 1/3. Unter der
Annahme zu 100% spin-ausgerichteter initialer s-s̄-Paare ergibt das
SU(6)-Modell nach Feed-down für die verwendete Kinematik
P_ΛΛ̅ = 0,096 ± 0,004. Der Messwert ist damit innerhalb der Unsicherheiten
vereinbar. Die Zahl 18% darf daher **nicht** als „18 von 100 Prozent
verbliebene Kohärenz" gelesen werden.''',
    'SCI key measurement',
)
sci = replace_once(
    sci,
    '''*Die Differenz zwischen theoretischen 100% und gemessenen 18% ist kein
> Defizit, sondern das eigentliche Fenster: Sie quantifiziert erstmals
> die Dekohärenz während des QCD-Confinements. Das ist für die
> Omnizedenz-These der „Feldkondensation" hochrelevant -- die Resonanz
> wird beim Übergang nicht zerstört, sondern gedämpft. --- T.P.K.*''',
    '''*Das belastbare Fenster liegt nicht in einer Subtraktion „100% minus
> 18%", sondern in der **Abhängigkeit der gemessenen Korrelation von der
> Paardistanz** und im Vergleich mit expliziten Hadronisierungsmodellen.
> Die Daten erlauben damit Tests von Kohärenzverlust während des
> QCD-Confinements, ohne bereits einen eindeutigen Dekohärenzparameter
> oder eine ontologische Vakuumübertragung festzulegen. --- T.P.K.*''',
    'SCI curator note 2.1',
)
sci = replace_once(
    sci,
    '''**\\[ESTABLISHED\\]** Die Experimente bestätigen, dass über 90 Prozent der
Protonenmasse nicht aus den nackten Quarkmassen stammen, sondern aus der
dynamischen Energie der Gluonenfelder und Vakuumfluktuationen.
Lattice-QCD-Rechnungen und Experimente zeigen konsistent, dass nur ein
kleiner Bruchteil der Protonenmasse auf nackte Quarkmassen entfällt.''',
    '''**\\[ESTABLISHED\\]** Unabhängige QCD- und Lattice-QCD-Arbeiten zeigen,
dass nur ein kleiner Teil der Protonenmasse auf die nackten Quarkmassen
zurückgeht; der überwiegende Anteil entsteht aus der QCD-Dynamik von
Quark- und Gluonfeldern. **Die STAR-Spinkorrelationsmessung selbst ist
kein neuer experimenteller Nachweis dieser Protonenmassenzusammensetzung.**''',
    'SCI proton mass',
)
sci = replace_once(
    sci,
    '''**\\[ESTABLISHED\\]** Die erhaltene Spinkorrelation zeigt, dass
Information aus dem virtuellen Zustand in die reale Teilchenwelt
transportiert wird. Dies ist die zentrale experimentelle Aussage der
RHIC-Daten.''',
    '''**\\[INTERPRETATION\\]** Die erhaltene Spinkorrelation ist mit der
Hypothese vereinbar, dass Spin-Information einer anfänglichen
s-s̄-Konfiguration teilweise bis in die hadronischen Endzustände
übertragen wird. Die **gemessene** Aussage ist die ΛΛ̅-Spinkorrelation;
die Herkunft dieser Information aus einem „virtuellen Zustand" ist eine
QCD-Modellinterpretation, kein separat beobachteter Transferprozess.''',
    'SCI information transfer',
)
sci = replace_once(
    sci,
    '''**\\[INTERPRETATION\\]** Neu ist, dass wir jetzt nicht nur indirekte
Effekte sehen, sondern den Übergang von virtuell zu real direkt
verfolgen können.''',
    '''**\\[INTERPRETATION\\]** Neu ist die Möglichkeit, Spin-Korrelationen
über den Quark-zu-Hadron-Übergang experimentell zu verfolgen. Ob dieser
Befund ontologisch als Übergang „virtuell zu real" beschrieben werden
sollte, bleibt eine Interpretation des QCD-Vakuum-Modellrahmens.''',
    'SCI virtual-to-real',
)
sci = replace_once(
    sci,
    '**Position C: Pragmatische Haltung \\[ESTABLISHED\\]**',
    '**Position C: Pragmatische Haltung \\[INTERPRETATION\\]**',
    'SCI position C marker',
)
sci = replace_once(
    sci,
    '''**\\[HYPOTHETICAL\\] Präzisionsmessungen der Vakuumstruktur:** Mit
verfeinerten Detektoren könnten systematische Kartierungen der
Vakuumfluktuationen möglich werden. Unterschiedliche Energieniveaus und
Kollisionsgeometrien würden verschiedene Aspekte des Vakuumspektrums
sichtbar machen. Der Beam Energy Scan II am RHIC (2025--2028) ist
bereits geplant.''',
    '''**\\[HYPOTHETICAL\\] Präzisionsmessungen der QCD-Spindynamik:** Weitere
Messungen bei unterschiedlichen Kollisionsenergien, Systemgrößen und
Kinematiken können testen, wie robust die ΛΛ̅-Spinkorrelation und ihre
Distanzabhängigkeit sind. RHIC beendete seine letzten Kollisionen im
Februar 2026 und wird für den Electron-Ion Collider umgebaut; ein
„Beam Energy Scan II 2025--2028" findet nicht statt.

**\\[ESTABLISHED / VORLÄUFIG\\]** CMS legte 2026 mit
**CMS-PAS-HIN-26-002** eine vorläufige Messung bei 13 TeV (pp) und
8,16 TeV (pPb) vor. Die ΛΛ̅-Korrelation zeigt dort bei kleinem ΔR keine
statistisch signifikante Abweichung von null und verhält sich damit
anders als das positive STAR-Signal bei 200 GeV. CMS wertet dies als
Hinweis auf eine Kollisionsenergie-Abhängigkeit; der zugrunde liegende
Mechanismus ist offen.''',
    'SCI future measurements',
)
sci = replace_once(
    sci,
    '''*Die RHIC-Daten zeigen, dass das Vakuum bei QCD-Skalen (Λ_QCD ≈ 200
> MeV) strukturiert ist, aber sie lösen die Vakuumkatastrophe nicht. Der
> Energiebereich liegt \\~17 Größenordnungen über der kosmologischen
> Konstante. Die Daten verschärfen eher die Frage: Warum trägt messbares
> Vakuum bei 200 MeV nicht zur kosmologischen Konstante bei?''',
    '''*Die RHIC-Daten berühren QCD-Skalen (Λ_QCD ≈ 200 MeV), lösen aber das
> kosmologische Konstantenproblem nicht. Ein Vergleich muss zwischen
> **Energieskala** und **Energiedichte** unterscheiden: Die oft zitierte
> Diskrepanz von bis zu ~120 Größenordnungen betrifft naive
> Planck-Cutoff-Abschätzungen der Vakuumenergiedichte; QCD-Beiträge liegen
> gegenüber der beobachteten Dunkelenergiedichte grob um ~40
> Größenordnungen höher. Aus der STAR-Messung folgt daraus keine neue
> Lösung des Problems.''',
    'SCI vacuum catastrophe orders',
)
sci = replace_once(
    sci,
    '''**\\[HYPOTHETICAL\\] Schwinger-Effekt via Hochleistungslaser:** Geplante
Experimente an der Extreme Light Infrastructure (ELI, 2026--2028) zur
Paarerzeugung aus dem Vakuum bei Feldstärken \\> 10¹⁸ V/m.''',
    '''**\\[HYPOTHETICAL\\] Starke-Feld-QED und Schwinger-Regime:** Anlagen der
Extreme Light Infrastructure untersuchen nichtlineare QED in extremen
Laserfeldern. Das Schwinger-Kritikfeld liegt bei etwa
**1,3 × 10¹⁸ V/m** und bleibt für direkte statische
Vakuum-Paarerzeugung deutlich außerhalb heutiger Laserfeldstärken.
Experimentell zugänglich sind verwandte starke-Feld-Prozesse und
Elektronstrahl-Laser-Kollisionen; eine direkte Demonstration des
Schwinger-Limits ist damit nicht gleichzusetzen.''',
    'SCI ELI',
)
sci = replace_once(
    sci,
    '''*Kritische Einordnung: Der Schritt von RHIC-Beobachtungen zu
> Vakuum-Engineering überbrückt \\~12 Größenordnungen in Energiedichte.
> Erforderliche Energiedichten: \\> 10²⁹ J/m³ (Planck-Skala). Keine
> experimentellen Ansätze, reine Spekulation.''',
    '''*Kritische Einordnung: Zwischen der beobachteten QCD-Spinkorrelation
> und einem hypothetischen „Vakuum-Engineering" existiert **kein
> etablierter technologischer Skalierungspfad**, aus dem sich eine
> belastbare Zahl von Größenordnungen ableiten ließe. Insbesondere ist
> 10²⁹ J/m³ nicht die Planck-Energiedichte. Der Anwendungssprung bleibt
> daher reine Spekulation ohne experimentelles Engineering-Modell.''',
    'SCI vacuum engineering scale',
)
sci = replace_once(
    sci,
    '''**\\[HYPOTHETICAL\\] Kurzfristig (5--10 Jahre):** Verfeinerung der
Messmethoden am RHIC und zukünftigen Beschleunigern. Systematische
Untersuchung verschiedener Quarkflavors (Bottom, Charm). Theoretische
Modellbildung zur Vorhersage von Vakuumkorrelationen. Beam Energy Scan
II am RHIC (2025--2028).''',
    '''**\\[HYPOTHETICAL\\] Kurzfristig (5--10 Jahre):** Vergleich der
STAR-Referenzmessung mit Ergebnissen bei höheren Kollisionsenergien und
anderen Systemen, insbesondere mit der 2026 vorgelegten CMS-Messung;
präzisere Spin-Tomographie und Tests, die echte Verschränkung von
allgemeiner Spin-Korrelation unterscheiden; theoretische Modellbildung
zur QCD-Hadronisierung. RHIC selbst hat 2026 den Kollisionsbetrieb
beendet und geht in den EIC-Umbau über.''',
    'SCI outlook',
)
sci = replace_once(
    sci,
    '''**Vakuum-Signatur \\[INTERPRETATION\\]** Die charakteristische Musterung
von Korrelationen (Spin, Impuls, Ladung), die erkennen lässt, aus
welchem Bereich des Vakuumzustands ein realisiertes Teilchenpaar
hervorgegangen ist. Direkt messbar durch die RHIC-Methode.''',
    '''**Vakuum-Signatur \\[INTERPRETATION\\]** Eine interpretative Bezeichnung
für charakteristische Korrelationsmuster (Spin, Impuls, Ladung). Die
Korrelation selbst ist messbar; ihre eindeutige Herkunft aus einem
bestimmten Bereich des Vakuumzustands ist modellabhängig und wird durch
die RHIC-Methode nicht direkt beobachtet.''',
    'SCI vacuum signature',
)
sci = replace_once(
    sci,
    '''**Informationstransfer virtuell/real \\[INTERPRETATION\\]** Die durch die
RHIC-Experimente nachgewiesene Erhaltung von Korrelationen beim Übergang
von virtuellen zu realen Zuständen, die auf eine fundamentale Rolle von
Information im Aufbau der physikalischen Realität hindeutet.''',
    '''**Informationstransfer virtuell/real \\[INTERPRETATION\\]** Eine mögliche
Deutung der gemessenen ΛΛ̅-Spinkorrelation im QCD-Vakuum-Modell. Direkt
nachgewiesen ist die Korrelation der hadronischen Endzustände; die
Formulierung als Transfer aus einem „virtuellen" Zustand ist eine
Interpretation und darf nicht als eigenständige Observable behandelt
werden.''',
    'SCI glossary information transfer',
)
sci = replace_once(
    sci,
    'Brookhaven National Laboratory Press Release: „Scientists Capture a\nGlimpse into the Quantum Vacuum" (Februar 2026).\nhttps://www.bnl.gov/newsroom/',
    'Brookhaven National Laboratory Press Release: „Scientists Capture a\nGlimpse into the Quantum Vacuum" (4. Februar 2026).\nhttps://www.bnl.gov/newsroom/news.php?a=222738\n\nCMS Collaboration: „Measurements of Λ hyperon spin correlations in\nproton-proton and proton-lead collisions", CMS-PAS-HIN-26-002 (17. Mai\n2026), vorläufiges Ergebnis.\nhttps://cms-results.web.cern.ch/cms-results/public-results/preliminary-results/HIN-26-002/index.html',
    'SCI sources CMS',
)
sci = replace_once(
    sci,
    '*Erstfassung mit korrigierten Experimentaldaten und epistemologischer\nSchichtung*',
    '*v1.1 · Evidenz-Audit 29.08.2026: STAR-Messgröße und Modellgrenzen präzisiert; 100%-vs.-18%-Fehldeutung entfernt; p+p/QGP-Konflation, veralteter RHIC-Ausblick und ELI/Schwinger-Skalierung korrigiert; CMS-PAS-HIN-26-002 als aktuelle Kreuzmessung ergänzt; „virtuell → real" als Interpretation statt Messfakt markiert.*',
    'SCI revision footer',
)
sci_path.write_text(sci, encoding='utf-8')

print('Applied OTA evidence-audit corrections to FND-0030 and SCI-0037')
