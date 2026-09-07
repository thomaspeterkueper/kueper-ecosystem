"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

type SignatureEntry = {
  title: string;
  status: "ENTWURF" | "AKTIV" | "SUPERSEDED" | "REJECTED" | "UNKNOWN";
  location: string;
  lastSeen: string;
};

type CollisionEntry = {
  signature: string;
  occurrences: string[];
};

type SeriesEntry = {
  nextFree: number | null;
  signatures: Record<string, SignatureEntry>;
  collisions: CollisionEntry[];
  note?: string;
};

type Registry = {
  schema: string;
  lastScanned: string;
  series: Record<string, SeriesEntry>;
};

type ApiResponse = {
  fetchedAt: string;
  sourceUrl: string;
  registry: Registry;
  error?: string;
};

function statusClass(status: string) {
  switch (status) {
    case "AKTIV": return "sig-status active";
    case "ENTWURF": return "sig-status draft";
    case "SUPERSEDED": return "sig-status superseded";
    case "REJECTED": return "sig-status rejected";
    default: return "sig-status unknown";
  }
}

export default function SignaturesPage() {
  const [data, setData] = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [openSeries, setOpenSeries] = useState<Set<string>>(new Set());

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/signatures", { cache: "no-store" });
      setData(await response.json());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const seriesList = useMemo(() => {
    if (!data?.registry?.series) return [];
    return Object.entries(data.registry.series).sort(([a], [b]) => a.localeCompare(b));
  }, [data]);

  const totalCollisions = useMemo(() => {
    return seriesList.reduce((sum, [, entry]) => sum + (entry.collisions?.length || 0), 0);
  }, [seriesList]);

  const totalSignatures = useMemo(() => {
    return seriesList.reduce((sum, [, entry]) => sum + Object.keys(entry.signatures || {}).length, 0);
  }, [seriesList]);

  function toggle(series: string) {
    setOpenSeries((prev) => {
      const next = new Set(prev);
      if (next.has(series)) next.delete(series); else next.add(series);
      return next;
    });
  }

  return (
    <main className="wrap control-room trace-view">
      <header className="console control-header">
        <div className="brand">
          <span className="kicker">KUEPER · Control Plane</span>
          <h1>Signatur-Registry</h1>
          <span className="sub">
            OTA-*/ENG-*-Signaturen je Serie, nächste freie Nummer und bekannte Kollisionen
            (ECO-ARC-0032). Google-Drive-Anteil des overtime-archive-Bestands ist nicht
            automatisiert erfasst — bei Zweifel den Drive-Ordner direkt prüfen.
          </span>
        </div>
        <div className="controls">
          <div className="stamp">
            {data ? (
              <>
                Registry-Stand {new Date(data.registry.lastScanned).toLocaleTimeString("de-DE")}
                <br />
                {new Date(data.registry.lastScanned).toLocaleDateString("de-DE")}
              </>
            ) : "—"}
          </div>
          <button className="refresh" onClick={load} disabled={loading}>
            {loading ? "Lädt…" : "Aktualisieren"}
          </button>
        </div>
      </header>

      {data?.error && (
        <div className="trace-unavailable">
          <b>Registry nicht ladbar.</b>
          <span>{data.error}</span>
        </div>
      )}

      {data?.registry && (
        <>
          <section className="summary ops-summary trace-summary">
            <div className="metric">
              <span className="val mono">{seriesList.length}</span>
              <span className="lbl">Serien</span>
            </div>
            <div className="metric">
              <span className="val mono">{totalSignatures}</span>
              <span className="lbl">bekannte Signaturen</span>
            </div>
            <div className="metric">
              <span className="val mono" style={totalCollisions > 0 ? { color: "#e04b4b" } : undefined}>
                {totalCollisions}
              </span>
              <span className="lbl">Kollisionen</span>
            </div>
          </section>

          <section className="trace-list">
            {seriesList.map(([series, entry]) => (
              <article className={`trace-card ${entry.collisions?.length ? "blocked" : ""}`} key={series}>
                <div className="trace-card-head" onClick={() => toggle(series)} style={{ cursor: "pointer" }}>
                  <div>
                    <span className="eyebrow">OTA-{series}-*</span>
                    <h2>{series}</h2>
                    <p>
                      {Object.keys(entry.signatures || {}).length} Signaturen bekannt
                      {entry.note ? <span> · {entry.note}</span> : null}
                    </p>
                  </div>
                  <div className="trace-head-meta">
                    <span className="trace-status">
                      nächste frei: {entry.nextFree ?? "unbekannt"}
                    </span>
                    {entry.collisions?.length > 0 && (
                      <span className="trace-status rejected">
                        {entry.collisions.length} Kollision{entry.collisions.length > 1 ? "en" : ""}
                      </span>
                    )}
                  </div>
                </div>

                {entry.collisions?.length > 0 && (
                  <div className="trace-footer">
                    {entry.collisions.map((c) => (
                      <div key={c.signature} className="trace-blocker">
                        <b>{series}-{c.signature}</b>: {c.occurrences.join(" — ")}
                      </div>
                    ))}
                  </div>
                )}

                {openSeries.has(series) && (
                  <div className="trace-pipeline" style={{ flexDirection: "column", alignItems: "stretch", gap: "6px" }}>
                    {Object.entries(entry.signatures || {})
                      .sort(([a], [b]) => a.localeCompare(b))
                      .map(([number, sig]) => (
                        <div key={number} style={{ display: "flex", gap: "12px", fontSize: "0.85rem", padding: "4px 0", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                          <span className="mono" style={{ minWidth: "70px" }}>{series}-{number}</span>
                          <span className={statusClass(sig.status)} style={{ minWidth: "90px" }}>{sig.status}</span>
                          <span style={{ flex: 1 }}>{sig.title}</span>
                          <span style={{ opacity: 0.6, minWidth: "180px" }}>{sig.location}</span>
                          <span style={{ opacity: 0.4, minWidth: "90px" }}>{sig.lastSeen}</span>
                        </div>
                      ))}
                  </div>
                )}
              </article>
            ))}
          </section>
        </>
      )}

      {!data && <div className="empty">Signatur-Registry wird geladen…</div>}
    </main>
  );
}
