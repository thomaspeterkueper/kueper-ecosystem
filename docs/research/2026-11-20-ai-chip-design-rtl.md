# Forschungsnotiz: KI-gestützte RTL-Optimierung und Chipdesign (18.11.2026)

**Status:** Draft / quellengebundene Evidenznotiz, nicht kanonisch; keine Implementierungsfreigabe.  
**Erfasst:** 2026-11-20  
**Quelle:** OpenAI, *Advancing chip design with OpenAI models*, veröffentlicht 2026-11-18: https://openai.com/index/advancing-chip-design-with-our-models/  
**Evidenzgrad:** Herstellerbericht mit konkreten Mess- und Verifikationsangaben; keine hier unabhängig replizierte oder peer-reviewte Bestätigung.  
**Projektbezug:** KUEPER Ecosystem (AI-Agenten-Methodik und Evaluationsstandards), KG (spätere quellenbasierte technische Entitäten), ggf. SSF (Lehrmaterial nach Prüfung).

## Belegte Aussagen der Quelle (als Herstellerangaben)

- Bei Jalapeño beziffert OpenAI die durch Modellvorschläge erreichten Standardzellen-Flächenreduktionen auf ca. 13 % im Warp Engine und 10 % in der Matrix Unit. Die Änderungen seien beim Silicon Bring-up verifiziert worden.
- Bei AMD nennt OpenAI bis zu 14 % PPA-Verbesserung gegenüber optimierten GPU-IP-Baselines; AMD habe einen Teil der Änderungen bereits in ein zur Fertigung übergebenes Design aufgenommen. Die Bewertung beruht auf OpenAI-/Partnerangaben.
- Für zwei offene 32-Bit-RISC-V-Kerne (PicoRV32, Ibex) wurden generierte RTL-Entwürfe simulativ auf Korrektheit geprüft und mit einer geschätzten Durchsatzmetrik bewertet; insgesamt 9.881 bewertete Läufe über zwei Aufgaben, zwei Kerne und verschiedene Tokenbudgets.

## Interpretation / Hypothese (nicht als Befund übernehmen)

KI-Agenten könnten besonders dort messbaren Nutzen bringen, wo Vorschläge durch deterministische Werkzeuge (RTL-Simulation, formale Verifikation, Synthese) schnell und reproduzierbar geprüft werden können. Übertragbarkeit auf andere EDA-Werkzeuge, Kosten und produktive Chip-Generationen ist offen.

## Evidenzgrenzen

- Herstellerquelle mit Eigeninteresse; kein unabhängiger Vergleich aller genannten Produktionsgewinne.
- RISC-V-Benchmarks nutzen modellierte Frequenzen und begrenzte Features, keine vollständige physische Sign-off-Prüfung; die Quelle weist selbst auf mögliche Vorteile durch ausgelassene Features hin.
- Prozentwerte beziehen sich auf unterschiedliche Blöcke und Metriken; sie dürfen nicht addiert oder auf ganze Chips hochgerechnet werden.
- Keine Aussage über Energieeinsparungen im realen Rechenzentrum ohne gesonderte Messung.

## Nächster prüfbarer Schritt

Vor jeder Kanonisierung externe technische Gegenprüfung suchen, Original-Evaluationsprotokolle und Reproduzierbarkeit untersuchen, Benchmark-Metriken mit den bereits bestehenden KUEPER-Agenten-/CI-Kostenmessungen abgleichen. **Keine neue Agenten-Engine** anlegen.

## Doppelungsprüfung

GitHub-Issue- und PR-Titelsuche im Repository `kueper-ecosystem` nach „chip design Jalapeño RISC-V“ / „chip design RISC-V“ ergab am 20.11.2026 keine Treffer. Das ist **keine vollständige Code- oder KG-Doppelungsprüfung**; vor Übernahme in KG weitere Repositories und Dokumentindizes prüfen.
