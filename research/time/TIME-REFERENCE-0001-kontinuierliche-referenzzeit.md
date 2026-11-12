# TIME-REFERENCE-0001 — Kontinuierliche Referenzzeit und Synchronisationsrelationen

Status: Forschungsnotiz / proposed · Erstellt: 2026-10-11 · Review: 2026-10-16 (Beschlussprüfung), 2027-10-11 (Jahresreview)
Schlagworte: Schaltsekunde, UTC, UT1, Metrologie, Timescale Engineering, Integrity of Observation, AVI, Omnizedenz, Kontrakomologie, NOXIA, Mishkenaz

## Ausgangspunkt und Evidenz
Nachrichtenanlass: https://www.n-tv.de/wissen/Der-Schaltsekunde-droht-das-Aus-nach-54-Jahren-id31394950.html
Primärquelle: CGPM Resolution 4 (2022), https://www.bipm.org/en/cgpm-2022/resolution-4
BIPM-Zeitkoordination: https://www.bipm.org/en/time-department/time-future
NIST: https://www.nist.gov/pml/time-and-frequency-division/time-realization/leap-seconds

UTC ist atomzeitbasiert und wird derzeit durch Schaltsekunden mit der rotationsabhängigen UT1 näherungsweise verbunden. Die CGPM beschloss 2022, den maximal zulässigen Betrag |UT1−UTC| bis spätestens 2035 zu erhöhen, mit dem Ziel einer über mindestens ein Jahrhundert kontinuierlichen UTC. Die genaue weitere Umsetzung und Beschlusslage im Oktober 2026 bei neuer Prüfung gegen BIPM verifizieren. Eine spätere technische Umstellung weder als bereits wirksam noch als endgültig beschlossen voraussetzen. Schaltsekunden wurden bislang positiv eingefügt; negative Schaltsekunden sind theoretisch möglich, aber bislang nicht eingesetzt worden.

## Trennung von Beobachtung, Standard und Hypothese
BEOBACHTUNG: Erdrotation schwankt; Atomuhren liefern stabilere Referenzintervalle.
STANDARD: UTC/UT1, zulässige Differenz und Interkalation sind Vereinbarungen zur Koordination.
ABLEITUNG: Unterschiedliche legitime Zeitkoordinaten können über dokumentierte Transformationsregeln verbunden werden.
NICHT BELEGT: Dass daraus eine neue ontologische Struktur der Zeit oder AVI-spezifische physikalische Mechanismen folgen.

## Projektfolgen
- AVI/Kontrakomologie: physikalische Dynamik, Uhrprozess, Messoperation, Modellzeit und Koordinatenwahl explizit unterscheiden. Keine neue physikalische Behauptung ohne falsifizierbare Prognose.
- Omnizedenz: zeitliche Bestimmtheit nicht stillschweigend mit einer besonderen Skala identifizieren; Eigenschaften versus relationale Zuordnung separat prüfen.
- Timescale Engineering: kontinuierliche monotone interne Zeiten, explizite Abbildung auf zivile/astronomische Zeiten, Grenzen und Fehlerintervalle. Korrekturen nur kontrolliert und nachvollziehbar.
- NOXIA: Kanonische Ereignisreihenfolge und Simulationszeit unabhängig von lokalen Sonnenzeiten und Zeitzonen; Mars- und Erdtag sind Darstellungen, keine Basis der Kausalordnung. UTC für externe Anzeige mit Versionskennung der Leap-Second-Tabelle.
- Mishkenaz: Ausdrücke für Zeitpunkt, Dauer, Reihenfolge, Referenzsystem und Unsicherheit gesondert validieren.

## Testprotokoll NOXIA (vorgeschlagen, kein implementierter Code)
1. Zwei Welten mit abweichenden Rotationsperioden bekommen Ereignisse mit identischer kanonischer Simulationszeit.
2. Lokale Anzeigezeiten unterscheiden sich, Ereignis-ID und deterministische kausale Reihenfolge bleiben stabil.
3. Verschiebung/Änderung ziviler Zeittabellen darf bestehende kanonische Zeitstempel nicht ändern.
4. Test auf Uhrsprung, Drift, Replay und idempotente Tick-Verarbeitung; messen: verlorene/duplizierte Ereignisse und Inkonsistenzen.
5. Kein unmittelbarer Eingriff in produktive Tick-/Datenbanklogik ohne gesonderte Architekturprüfung.

## Review
2026-10-16: internationale Beschlusslage und Wirksamkeitsdatum anhand BIPM/CGPM prüfen; Zeitungsaussagen gegen Primärquellen abgleichen.
2027-10-11: Standardentwicklung, Leap-Second-Politik, verfügbare Referenz-/Zeittabellen und technische NOXIA-Anforderungen erneut prüfen.
Danach jährlicher Review bzw. früher bei grundlegenden Standardänderungen.

## Erkenntnisstatus
Referenzfall für Trennung von Messung, Konvention und Modell. Übergreifende Folgerungen sind konzeptionelle Arbeitsannahmen, nicht empirische Bestätigungen von AVI oder Omnizedenz.
