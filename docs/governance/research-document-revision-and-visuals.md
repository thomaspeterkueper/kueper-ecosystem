# Forschungsdokumente: Revision, Evidenz und Visualisierung (Vorschlag)

Status: **DRAFT / review-gated**, 2026-10-10. Ergänzt die bestehende Ecosystem-Research-Governance; ersetzt keine vorhandenen Review-, Canon- oder Source-Gates. Keine automatische Veröffentlichung, Kanonisierung oder Auto-Merges.

## Revisionsregel

Jedes **aktive** Forschungsdokument muss spätestens **365 Tage nach dem letzten abgeschlossenen inhaltlichen Review** erneut geprüft werden. Formatänderungen, automatisches Reformatieren, reine Metadatenänderungen und unverifizierte Recherchen setzen die Frist nicht zurück. Für historische, abgeschlossene oder archivierte Dokumente wird der Status und ein begründeter Review-Modus dokumentiert, statt sie stillschweigend als aktuell zu führen.

Empfohlene maximale Intervalle, sofern keine strengere bestehende Policy gilt:

| Klasse | Maximales Intervall |
| --- | --- |
| Grundlagen, philosophische Modelle | 365 Tage |
| Aktive Hypothesen und laufende Forschungsfragen | 180 Tage |
| Empirische Naturwissenschaften mit schneller Evidenzentwicklung | 90 Tage |
| Technische Architektur, APIs, Sicherheit | 30–90 Tage, risikobasiert |
| Ereignisbezogene Beobachtungen | Bei relevanter neuer Evidenz, spätestens 365 Tage |

**Ereignisgesteuerte Vorprüfung:** Neue widersprechende Befunde, Retraktionen, geänderte Daten oder technische Breaking Changes können einen Review vorziehen. Eine bloße Nachricht darf keinen gesicherten Widerspruch vortäuschen.

## Review-Metadaten

Für jedes Dokument: stabile ID, verantwortliches Projekt, Status, Pfad, Quellen/DOIs mit Abruf- und Veröffentlichungsdatum, letztes abgeschlossenes inhaltliches Review, nächster Termin, Evidenzstatus, Änderungs-/Entscheidungsprotokoll und Links zu Grafiken. Bestehende Metadatenkonventionen haben Vorrang; keine zweite Registry ohne Bestandsabgleich.

Review-Schritte: aktuelle Version und Quellen prüfen → neue Primärliteratur/ggf. Retraktionen suchen → Behauptungen nach Evidenzgrad und Provenienz vergleichen → Gegenargumente und negative Befunde dokumentieren → Änderungen als Draft/PR vorschlagen → bestehende Source/Evidence- und Exact-Head-Gates anwenden → erst nach menschlich freigegebener inhaltlicher Prüfung Review-Datum aktualisieren. Keine automatische Kanonisierung.

## Grafiken als Forschungsartefakte

Markdown-Mermaid für Ablauf-/Beziehungsmodelle, SVG als bevorzugte skalierbare Abbildung, PNG als Vorschau; PDFs als Lesefassung. Grafikquelle, gerenderte Fassung und Text gehören versioniert zusammen. Jede Abbildung benötigt: eindeutige ID, Titel/Bildunterschrift, Aussage, Evidenzstatus (**Illustration / Modell / Simulation / Messdaten**), Quellen/Parameter, Erstellungsdatum und Version. Achsen und Einheiten nennen; keine schematische Zeichnung als gemessene Kurve ausgeben. Grafiken bei inhaltlichen Änderungen mitprüfen. Barrierefreiheit: Alternativtext und Textbeschreibung.

## IND-002 – Entstehung, Bestimmung, Stabilisierung, Beobachtung

Vorläufige Forschungsfrage: Unter welchen Bedingungen schränkt die Kopplung eines Systems an seine Umgebung Zustandsübergänge ein, ohne den ursprünglichen Zustand eindeutig zu bestimmen?

Vier Begriffe getrennt halten: **Entstehung** (Zustandsbildung), **Bestimmung** (Einschränkung/Festlegung von Möglichkeiten), **Stabilisierung** (Persistenz/Übergangshemmung), **Beobachtung** (Informationszugang). Physikalische Dekohärenz nicht mit bewusster Beobachtung oder dem Nachweis eines einzelnen Messergebnisses gleichsetzen. Analogie zu NPC-Gewohnheiten oder sozialen Institutionen ausdrücklich als Analogie markieren, nicht als identischen Mechanismus.

Vor Übernahme in AVI, Omnizedenz oder Kontrakomologie: aktuelle Primärdefinitionen und Dokumentpfade in ihren jeweiligen Repositories identifizieren, auf Widersprüche prüfen und einen projektspezifischen Impact Report erstellen. Diese Policy behauptet **keinen bereits abgeschlossenen Begriffsabgleich**.

## Einführung

Zunächst manuelle bzw. bestehende Review-Queue verwenden; keine neuen stündlichen Jobs oder ChatGPT-Automationen. Vor einer Automatisierung vorhandene Revisionsdateien, Registries, Worker und Fristen vollständig inventarisieren und deduplizieren. Eine abgelaufene Frist erzeugt einen Prüfbedarf, keine automatische Textänderung.
