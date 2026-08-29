#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'ota')
path = root / 'src/content/documents/OTA-SCI-0037-2026-DE.md'
text = path.read_text(encoding='utf-8')


def rep(old: str, new: str, label: str) -> None:
    global text
    n = text.count(old)
    if n != 1:
        raise SystemExit(f'{label}: expected 1 occurrence, found {n}')
    text = text.replace(old, new, 1)

rep('**\\[THEORETISCH / HYPOTHETICAL\\]** Für parallele Spins beträgt das mit',
    '**\\[HYPOTHETICAL\\]** Für parallele Spins beträgt das mit',
    'standardize theoretical marker')

rep('**\\[ESTABLISHED / VORLÄUFIG\\]** CMS legte 2026 mit',
    '**\\[ESTABLISHED\\]** **Vorläufiger Kollaborationsbefund (noch nicht peer-reviewed):** CMS legte 2026 mit',
    'standardize CMS marker')

rep('''**\\[ESTABLISHED\\]** Diese materialisieren sich später als Lambda(Λ)- und
Antilambda(Λ̅)-Hyperonen, kurzlebige Baryonen, die im STAR-Detektor
(Solenoidal Tracker at RHIC) nachweisbar sind.''',
    '''**\\[ESTABLISHED\\]** In den analysierten Kollisionen werden unter
anderem Lambda(Λ)- und Antilambda(Λ̅)-Hyperonen produziert. Diese
kurzlebigen Baryonen werden über ihre Zerfallsprodukte im STAR-Detektor
(Solenoidal Tracker at RHIC) rekonstruiert. Ihre gemessene Existenz
belegt für sich genommen keine bestimmte virtuelle Vorläuferkonfiguration.''',
    'remove materialization claim')

rep('''**\\[ESTABLISHED\\]** Die RHIC-Entdeckung reiht sich in eine Serie von
Belegen für die physikalische Realität des Vakuums ein: Casimir-Effekt
(1948 vorhergesagt, 1997 präzise bestätigt), Lamb-Verschiebung (1947,
Nobelpreis 1955), spontane Emission angeregter Atome, dynamischer
Casimir-Effekt (2011, Chalmers University).''',
    '''**\\[ESTABLISHED\\]** Der Grundzustand quantisierter Felder hat
experimentell nachweisbare Konsequenzen. Dazu gehören unter anderem
Lamb-Verschiebung, Casimir-Effekt und dynamischer Casimir-Effekt. Diese
Befunde stützen die physikalische Relevanz des QFT-Vakuumzustands; sie
legen jedoch keine eindeutige Ontologie „virtueller Teilchen" fest.''',
    'vacuum ontology wording')

rep('''Vakuumfluktuationen sind mehr als Rechenhilfen. Die gemessenen
Spinkorrelationen gelten als direkter Fingerabdruck einer strukturierten
Vakuumkonfiguration, aus der reale Teilchen hervorgehen. Vertreter:
Teile der STAR Collaboration, Befürworter ontologischer
QFT-Interpretationen.''',
    '''In dieser Lesart gelten die gemessenen Spinkorrelationen als möglicher
Fingerabdruck einer strukturierten QCD-Vakuumkonfiguration, deren
Spinstruktur bis in hadronische Endzustände reicht. Die STAR-Publikation
und die BNL-Kommunikation verwenden diese Deutungsrichtung, ohne damit
eine allgemeine ontologische Festlegung der QFT zu etablieren.''',
    'position A sociology')

rep('''Für viele Forschende steht im Vordergrund, dass die Daten die
Vorhersagen der QCD präzisieren und bestätigen. Die Frage nach der
„Realität" virtueller Zustände wird als semantisch oder metaphysisch
angesehen. Diese Position dominiert in der praktischen Forschung.''',
    '''Eine pragmatische Arbeitsweise konzentriert sich auf die messbare
Korrelation und auf diskriminierbare QCD-Modelle, ohne aus der
erfolgreichen Beschreibung eine eindeutige Ontologie virtueller Zustände
abzuleiten. Wie verbreitet einzelne philosophische Lesarten in der
Fachgemeinschaft sind, wird hier nicht quantifiziert.''',
    'position C sociology')

rep('''**\\[HYPOTHETICAL\\]** Dies hat weitreichende Konsequenzen für unser
Verständnis von Quanteninformation und könnte neue Ansätze für
Quantencomputing inspirieren -- etwa durch Protokolle, die explizit
Spinkorrelationen aus dem Vakuum nutzen, statt sie als Störgröße zu
behandeln.''',
    '''**\\[SPECULATIVE\\]** Ob aus solchen QCD-Spinkorrelationen jemals ein
praktischer Ansatz für Quanteninformation oder Quantencomputing
abgeleitet werden kann, ist gegenwärtig offen. Die STAR-Messung liefert
keinen technologischen Pfad und keine nutzbare Vakuum-Ressource.''',
    'quantum computing speculation')

rep('''**\\[HYPOTHETICAL\\] Quantensensoren:** Die Empfindlichkeit für
Vakuumkorrelationen könnte zu neuartigen Sensortypen führen, die auf
Vakuumfluktuationen reagieren. Solche Sensoren könnten winzige
Änderungen von Gravitations- oder Feldkonfigurationen über ihre Wirkung
auf das Vakuum detektieren.''',
    '''**\\[SPECULATIVE\\] Quantensensoren:** Aus der STAR-Messung folgt derzeit
kein belastbares Sensorkonzept. Denkbare Anwendungen, die eine
experimentell kontrollierbare QCD-Vakuumkorrelation als Ressource
verwenden würden, sind reine Langfrist-Spekulation.''',
    'sensor speculation')

rep('''**\\[HYPOTHETICAL\\] Kontrollierte Teilchenerzeugung:** Ein tieferes
Verständnis der virtuell-zu-real-Übergänge könnte gezieltere Methoden
der Teilchenerzeugung ermöglichen, relevant für Medizin (PET),
Materialwissenschaft und Energieforschung.''',
    '''**\\[SPECULATIVE\\] Kontrollierte Teilchenerzeugung:** Ein besseres
Verständnis nichtperturbativer Hadronisierung ist wissenschaftlich
wertvoll; ein daraus abgeleiteter neuer technischer Mechanismus zur
Teilchenerzeugung für Medizin, Materialwissenschaft oder Energie ist
jedoch nicht etabliert.''',
    'particle generation speculation')

rep('''Die RHIC-Entdeckung markiert einen Paradigmenwechsel. Das Vakuum
transformiert sich vom abstrakten Konzept zum experimentell zugänglichen
Forschungsgegenstand.''',
    '''Die STAR-Messung eröffnet einen neuen experimentellen Zugang zur
Spin-Dynamik des QCD-Confinements. Experimentell zugänglich ist dabei
die Hyperon-Spinkorrelation; daraus folgt nicht, dass „das Vakuum" als
Ganzes direkt beobachtet oder ontologisch entschieden wäre.''',
    'remove paradigm shift')

rep('''*Die RHIC-Entdeckung erinnert uns daran, dass die tiefsten Geheimnisse
der Physik oft dort verborgen liegen, wo wir nichts erwarten. Das Vakuum
erweist sich als reichhaltige Quelle, aus der die materielle Welt
hervorgeht. In gewisser Weise kehrt die moderne Physik damit zu einer
uralten Intuition zurück: dass das Sichtbare aus dem Unsichtbaren
entspringt. Nur dass wir diese Intuition jetzt in Spinkorrelationen
messen können.*''',
    '''*Der experimentelle Befund ist präziser als jede ontologische Metapher:
Messbar ist eine energie- und kinematikabhängige Spinkorrelation. Ob und
in welchem Sinn sie als Signatur des QCD-Vakuums verstanden werden kann,
bleibt eine Frage, die weitere Messungen und Modelle entscheiden müssen.*''',
    'final epistemic wording')

path.write_text(text, encoding='utf-8')
print('Refined OTA-SCI-0037 evidence-audit wording')
