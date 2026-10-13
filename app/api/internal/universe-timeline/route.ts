import { NextRequest, NextResponse } from "next/server";
import {
  PROJECTION_CAVEATS,
  PROJECTION_NOTE,
  PROJECTION_SOURCE,
  SEED_EVENTS,
} from "../../../internal/universe/timeline/seed-projection";

// Server-only. Diese Datei wird nie ins Client-Bundle aufgenommen.
// Zugriffsschutz: einfacher geteilter Code über Header, serverseitig geprüft.
// INTERNAL_ACCESS_TOKEN in den Vercel Environment Variables setzen.
//
// Datenmodell folgt dem Vertrag aus EXT-ECO-KG-20260722-001 / ECO-ARC-0018-2026-DE:
// id, title, summary, time.{start,end,precision,certainty,display},
// universe_or_scope, canonicality, epistemic_status, source_refs, relation_refs
// Erweitert (v0.1.1) um location und characters — beides optionale Anreicherung,
// verändert den Kernvertrag nicht, macht die Ansicht aber lesbarer.
//
// v0.2.0: Die Projektionsdaten liegen in app/internal/universe/timeline/seed-projection.ts
// (typisiert, testbar, inkl. Utopia-/Mars-Industrie-Strang aus EXT-OTA-ECO-20260911).
// Dieser Endpunkt liefert sie nur aus — ausdrücklich NICHT kanonisch.
// Regeln, Marker-Mapping und Quellenstand: docs/utopia-mars-chronology-projection.md
// Spätere Version ersetzt dies durch einen Export aus kueper-knowledge-graph
// (kg_entities WHERE type IN ('Event','Artifact') AND visibility IN ('private','restricted')).

export async function GET(req: NextRequest) {
  const token = req.headers.get("x-internal-token");
  const expected = process.env.INTERNAL_ACCESS_TOKEN;

  if (!expected || token !== expected) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  return NextResponse.json({
    generated_at: new Date().toISOString(),
    source: PROJECTION_SOURCE,
    canonical: false,
    note: PROJECTION_NOTE,
    caveats: PROJECTION_CAVEATS,
    events: SEED_EVENTS,
  });
}
