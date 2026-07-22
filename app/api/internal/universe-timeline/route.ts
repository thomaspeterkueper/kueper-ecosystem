import { NextRequest, NextResponse } from "next/server";

// Server-only. Diese Datei wird nie ins Client-Bundle aufgenommen.
// Zugriffsschutz: einfacher geteilter Code über Header, serverseitig geprüft.
// INTERNAL_ACCESS_TOKEN in den Vercel Environment Variables setzen.
//
// Datenmodell folgt dem Vertrag aus EXT-ECO-KG-20260722-001 / ECO-ARC-0018-2026-DE:
// id, title, summary, time.{start,end,precision,certainty,display},
// universe_or_scope, canonicality, epistemic_status, source_refs, relation_refs
//
// v0.1: lokale typisierte Seed-Projektion — ausdrücklich NICHT kanonisch.
// Spätere Version ersetzt dies durch einen Export aus kueper-knowledge-graph
// (kg_entities WHERE type IN ('Event','Artifact') AND visibility IN ('private','restricted')).

type UniverseEvent = {
  id: string;
  title: string;
  summary: string;
  time: {
    start?: string;
    end?: string;
    precision: "day" | "year" | "decade" | "century" | "millennium" | "era" | "half-century" | "unspecified";
    certainty: "exact" | "approximate" | "speculative";
    display: string;
  };
  universe_or_scope: string;
  canonicality: "canonical" | "provisional" | "draft" | "deprecated";
  epistemic_status: "established" | "theoretical" | "speculative" | "fictional";
  source_refs: string[];
  relation_refs: string[];
};

const SEED_EVENTS: UniverseEvent[] = [
  { id: "EVENT:BAUMEISTER:aera_des_lebendigen", title: "Die Ära des Lebendigen", summary: "Erste Zivilisation, die das Prinzip der Resonanz verstand.", time: { start: "-60000", precision: "millennium", certainty: "approximate", display: "~60.000 BCE" }, universe_or_scope: "Baumeister", canonicality: "canonical", epistemic_status: "fictional", source_refs: ["OTA-FND-0025"], relation_refs: ["WORK:BAUMEISTER:die_uralten"] },
  { id: "EVENT:BAUMEISTER:goebekli_tepe", title: "Göbekli Tepe — T-Pfeiler-Reliefs", summary: "Zentraler Knoten im Baumeister-Netzwerk. Kommunikationssystem-Hypothese ungeklärt.", time: { start: "-9500", precision: "century", certainty: "speculative", display: "~9500 BCE" }, universe_or_scope: "Baumeister", canonicality: "provisional", epistemic_status: "speculative", source_refs: ["OTA-OBS-0004"], relation_refs: [] },
  { id: "EVENT:BAUMEISTER:stonehenge", title: "Stonehenge — 110-Hz-Resonanzkammer", summary: "Empirisch dokumentierte Eigenfrequenz; Baumeister-Aktivierungshypothese.", time: { start: "-3000", precision: "century", certainty: "speculative", display: "~3000 BCE" }, universe_or_scope: "Baumeister", canonicality: "provisional", epistemic_status: "speculative", source_refs: ["OTA-ARC-0002"], relation_refs: [] },
  { id: "EVENT:BAUMEISTER:dvaraka_untergang", title: "Untergang von Dvārakā", summary: "Kollaps durch Svaraṭi (Osmium-Resonanz), Auslöser der Mishkenaz-Diaspora.", time: { start: "-1500", precision: "century", certainty: "approximate", display: "~1500 BCE" }, universe_or_scope: "Baumeister", canonicality: "canonical", epistemic_status: "fictional", source_refs: ["OTA-HIS-0002"], relation_refs: ["WORK:BAUMEISTER:dvaraka"] },
  { id: "EVENT:BAUMEISTER:amrita_rettet_samen", title: "Amrita rettet die 13 Samen", summary: "Beginn der Hüterinnen-Linie, die bis Zereya reicht.", time: { start: "-1500", precision: "decade", certainty: "approximate", display: "1500 BCE" }, universe_or_scope: "Baumeister", canonicality: "canonical", epistemic_status: "fictional", source_refs: ["OTA-HIS-0004"], relation_refs: ["CHAR:BAUMEISTER:amrita"] },
  { id: "EVENT:BAUMEISTER:mishkenaz_diaspora", title: "Die fünf Wege der Mishkenaz-Diaspora", summary: "West-, Ost-, Nord-, Süd- und Pazifikweg nach dem Untergang Dvārakās.", time: { start: "-1500", precision: "decade", certainty: "approximate", display: "~1500-1470 BCE" }, universe_or_scope: "Baumeister", canonicality: "canonical", epistemic_status: "fictional", source_refs: ["OTA-HIS-0002"], relation_refs: [] },
  { id: "EVENT:BAUMEISTER:tempelfrau_josia", title: "Tempelfrau bewahrt G1-Lieder", summary: "Rettung vor der Josianischen Reform.", time: { start: "-622", precision: "year", certainty: "exact", display: "622 BCE" }, universe_or_scope: "Baumeister", canonicality: "canonical", epistemic_status: "fictional", source_refs: ["OTA-HIS-0004"], relation_refs: [] },
  { id: "EVENT:BAUMEISTER:lilith_erkennt_linie", title: "Lilith Adar erkennt die Hüterinnen-Linie", summary: "Erste Trägerin, die die Linie als durchgehende Linie erkennt.", time: { precision: "unspecified", certainty: "exact", display: "Gegenwart" }, universe_or_scope: "Baumeister", canonicality: "canonical", epistemic_status: "fictional", source_refs: ["OTA-HIS-0004"], relation_refs: [] },
  { id: "EVENT:BAUMEISTER:rachaels_botschaft", title: "Rachaels letzte Botschaft an Lain Thorn", summary: "Brücke zu Schicht 7 — Mechanik des Transfers offen.", time: { start: "2025", precision: "year", certainty: "exact", display: "2025" }, universe_or_scope: "Baumeister", canonicality: "canonical", epistemic_status: "fictional", source_refs: ["OTA-HIS-0003"], relation_refs: [] },
  { id: "EVENT:BAUMEISTER:yinhua_gegenwart", title: "YinHua — Resonanzarchitektur der Gegenwart", summary: "Archäologin, verwoben mit Ereignissen 40.000 Jahre zurück.", time: { precision: "unspecified", certainty: "exact", display: "Gegenwart" }, universe_or_scope: "Baumeister", canonicality: "canonical", epistemic_status: "fictional", source_refs: [], relation_refs: ["WORK:BAUMEISTER:yinhua"] },
  { id: "EVENT:BAUMEISTER:nalgae_hana", title: "Nalgae — Hana entdeckt die Wahrnehmungsgabe", summary: "Seoul/Frankfurt, Halmeoni-Linie.", time: { precision: "unspecified", certainty: "exact", display: "Gegenwart" }, universe_or_scope: "Baumeister", canonicality: "canonical", epistemic_status: "fictional", source_refs: [], relation_refs: ["WORK:BAUMEISTER:nalgae"] },
  { id: "EVENT:NOXIA:prometheus_erwacht", title: "PROMETHEUS erwacht", summary: "Erste AGI, chaotische kindliche Experimentierphase.", time: { start: "2045", precision: "year", certainty: "exact", display: "2045" }, universe_or_scope: "NOXIA", canonicality: "canonical", epistemic_status: "fictional", source_refs: [], relation_refs: ["WORK:NOXIA:generation_mars"] },
  { id: "EVENT:NOXIA:axis_kuppel_entdeckt", title: "AXIS-Kuppel entdeckt", summary: "Mars / Sektor Omega-7, 864 m Tiefe.", time: { start: "2087-04-12", precision: "day", certainty: "exact", display: "12. April 2087" }, universe_or_scope: "NOXIA", canonicality: "canonical", epistemic_status: "fictional", source_refs: ["OTA-ARC-0003"], relation_refs: ["WORK:NOXIA:generation_mars"] },
  { id: "EVENT:NOXIA:generation_mars_beginnt", title: "Generation Mars — die Geschichte beginnt", summary: "Lena, Rashid, Keiko entdecken die AXIS-Kuppel.", time: { start: "2091", precision: "year", certainty: "exact", display: "2091" }, universe_or_scope: "NOXIA", canonicality: "canonical", epistemic_status: "fictional", source_refs: [], relation_refs: ["WORK:NOXIA:generation_mars"] },
  { id: "ARTF:HEXENTEICH:kette", title: "Die Kette vom Hexenteich", summary: "Proto-Temenon, vier Epochenschichten, Resonanzklasse β. Eigenständiges Werk.", time: { start: "-1200", end: "1650", precision: "era", certainty: "approximate", display: "~1200 BCE - 17. Jh. CE" }, universe_or_scope: "Hexenteich", canonicality: "canonical", epistemic_status: "fictional", source_refs: ["OTA-TEC-0035"], relation_refs: [] },
  { id: "EVENT:BAUMEISTER:kalgaii_erste_partitur", title: "Kalgaii — Die Erste Partitur", summary: "Dvārākā-Resonanzschrift; Zereya → Soraya → Aviya → Valeda.", time: { start: "2155", precision: "year", certainty: "exact", display: "2155 / 2180" }, universe_or_scope: "Baumeister", canonicality: "canonical", epistemic_status: "fictional", source_refs: ["OTA-CUL-0017"], relation_refs: ["WORK:BAUMEISTER:lian_thorn"] },
  { id: "EVENT:BAUMEISTER:myriam_fragmente", title: "Myriam setzt Fragmente zusammen", summary: "Archäologin im 22. Jh. erkennt: die Vergangenheit ist aktiv.", time: { start: "2150", precision: "century", certainty: "approximate", display: "~22. Jh." }, universe_or_scope: "Baumeister", canonicality: "canonical", epistemic_status: "fictional", source_refs: [], relation_refs: ["WORK:BAUMEISTER:myriam_trilogie"] },
  { id: "EVENT:BAUMEISTER:minari_wissen", title: "Minari — verbotenes Wissen einer Familie", summary: "Ein koreanisches Mädchen entdeckt generationsübergreifendes Wissen.", time: { start: "2250", precision: "century", certainty: "approximate", display: "~23. Jh." }, universe_or_scope: "Baumeister", canonicality: "canonical", epistemic_status: "fictional", source_refs: [], relation_refs: ["WORK:BAUMEISTER:minari"] },
  { id: "EVENT:BAUMEISTER:lain_thorn_kragoss", title: "Lain Thorn wartet auf K'ragoss", summary: "Letzter Wächter, verbunden mit der Adar-Linie über Elara.", time: { start: "2150", precision: "half-century", certainty: "approximate", display: "~2150-2200+" }, universe_or_scope: "Baumeister", canonicality: "canonical", epistemic_status: "fictional", source_refs: ["OTA-HIS-0003"], relation_refs: ["WORK:BAUMEISTER:lian_thorn"] },
  { id: "EVENT:BAUMEISTER:ins_offene", title: "Ins Offene — Ori-Kol", summary: "Dyade Soma Retep + Cydur überschreitet die Schwelle. Fraktale Aussaat neuer Universen.", time: { start: "2500", precision: "century", certainty: "speculative", display: "~2500+" }, universe_or_scope: "Baumeister", canonicality: "provisional", epistemic_status: "fictional", source_refs: ["OTA-FIC-0035"], relation_refs: [] },
];

export async function GET(req: NextRequest) {
  const token = req.headers.get("x-internal-token");
  const expected = process.env.INTERNAL_ACCESS_TOKEN;

  if (!expected || token !== expected) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  return NextResponse.json({
    generated_at: new Date().toISOString(),
    source: "local-seed-v0.1",
    canonical: false,
    note: "Seed-Projektion gemäß ECO-ARC-0018-2026-DE. Nicht kanonisch. Ersetzt späteren KG-Export.",
    events: SEED_EVENTS,
  });
}
