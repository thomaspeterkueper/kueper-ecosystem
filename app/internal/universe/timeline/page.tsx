"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

type UniverseEvent = {
  id: string;
  title: string;
  summary: string;
  location?: string;
  characters?: string[];
  time: {
    start?: string;
    end?: string;
    precision: string;
    certainty: "exact" | "approximate" | "speculative";
    display: string;
  };
  universe_or_scope: string;
  canonicality: "canonical" | "provisional" | "draft" | "deprecated";
  epistemic_status: "established" | "theoretical" | "speculative" | "fictional";
  source_refs: string[];
  relation_refs: string[];
};

type ApiResponse = {
  generated_at: string;
  source: string;
  canonical: boolean;
  note: string;
  events: UniverseEvent[];
};

const EPI_COLOR: Record<string, string> = {
  established: "#7fae7f",
  theoretical: "#4a6fa5",
  speculative: "#3e7c8a",
  fictional: "#a5658a",
};

function sortKey(e: UniverseEvent): number {
  const start = e.time.start;
  if (!start) return Number.MAX_SAFE_INTEGER;
  const n = parseFloat(String(start).replace(/-(\d+)-\d+$/, "$1")); // grobe Jahreszahl
  return Number.isNaN(n) ? Number.MAX_SAFE_INTEGER : n;
}

export default function UniverseTimelinePage() {
  const [tokenInput, setTokenInput] = useState("");
  const [token, setToken] = useState<string | null>(null);
  const [data, setData] = useState<ApiResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [scopeFilter, setScopeFilter] = useState<string>("all");
  const [epiFilter, setEpiFilter] = useState<Set<string>>(
    new Set(["established", "theoretical", "speculative", "fictional"])
  );
  const [query, setQuery] = useState("");

  useEffect(() => {
    const saved = typeof window !== "undefined" ? sessionStorage.getItem("uv-timeline-token") : null;
    if (saved) setToken(saved);
  }, []);

  const load = useCallback(async (t: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/internal/universe-timeline", {
        headers: { "x-internal-token": t },
        cache: "no-store",
      });
      if (res.status === 401) {
        setError("Zugriffscode falsch oder abgelaufen.");
        setToken(null);
        sessionStorage.removeItem("uv-timeline-token");
        return;
      }
      const json = await res.json();
      if (!res.ok) throw new Error(json?.error || `HTTP ${res.status}`);
      setData(json);
      sessionStorage.setItem("uv-timeline-token", t);
    } catch (e: any) {
      setError(e?.message || "Unbekannter Fehler");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (token) load(token);
  }, [token, load]);

  const scopes = useMemo(() => {
    if (!data) return [];
    return Array.from(new Set(data.events.map((e) => e.universe_or_scope)));
  }, [data]);

  const filtered = useMemo(() => {
    if (!data) return [];
    return data.events
      .filter((e) => scopeFilter === "all" || e.universe_or_scope === scopeFilter)
      .filter((e) => epiFilter.has(e.epistemic_status))
      .filter((e) => !query || e.title.toLowerCase().includes(query.toLowerCase()) || e.id.toLowerCase().includes(query.toLowerCase()))
      .sort((a, b) => sortKey(a) - sortKey(b));
  }, [data, scopeFilter, epiFilter, query]);

  const toggleEpi = (k: string) => {
    setEpiFilter((prev) => {
      const next = new Set(prev);
      if (next.has(k)) next.delete(k);
      else next.add(k);
      return next;
    });
  };

  if (!token) {
    return (
      <main style={styles.page}>
        <div style={{ maxWidth: 360, margin: "20vh auto", textAlign: "center" }}>
          <div style={styles.eyebrow}>Geschützter Bereich</div>
          <h1 style={styles.h1}>Universe Timeline</h1>
          <form
            onSubmit={(ev) => {
              ev.preventDefault();
              setToken(tokenInput);
            }}
            style={{ marginTop: "1.5rem" }}
          >
            <input
              type="password"
              value={tokenInput}
              onChange={(e) => setTokenInput(e.target.value)}
              placeholder="Zugriffscode"
              style={styles.input}
            />
            <button type="submit" style={styles.button}>
              Öffnen
            </button>
          </form>
          {error && <p style={{ color: "#c77", marginTop: "1rem" }}>{error}</p>}
        </div>
      </main>
    );
  }

  return (
    <main style={styles.page}>
      <header style={{ textAlign: "center", marginBottom: "2rem" }}>
        <div style={styles.eyebrow}>Küper Ecosystem · Internal · v0.1 Seed (nicht kanonisch)</div>
        <h1 style={styles.h1}>Universe Timeline</h1>
        {data && <p style={{ color: "#7b8494", fontStyle: "italic" }}>{filtered.length} / {data.events.length} Ereignisse</p>}
      </header>

      <div style={styles.controls}>
        <input
          type="text"
          placeholder="Suche nach Titel oder ID…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={{ ...styles.input, maxWidth: 260 }}
        />
        <select value={scopeFilter} onChange={(e) => setScopeFilter(e.target.value)} style={styles.select}>
          <option value="all">Alle Universen/Werke</option>
          {scopes.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        {["established", "theoretical", "speculative", "fictional"].map((k) => (
          <button
            key={k}
            onClick={() => toggleEpi(k)}
            style={{
              ...styles.chip,
              background: epiFilter.has(k) ? EPI_COLOR[k] : "transparent",
              color: epiFilter.has(k) ? "#05070c" : "#7b8494",
              borderColor: EPI_COLOR[k],
            }}
          >
            {k}
          </button>
        ))}
      </div>

      {loading && <p style={{ textAlign: "center", color: "#7b8494" }}>Lädt…</p>}
      {error && <p style={{ textAlign: "center", color: "#c77" }}>{error}</p>}

      <div style={{ borderLeft: "2px solid #1e2733", paddingLeft: "2rem", maxWidth: 900, margin: "0 auto" }}>
        {filtered.map((e) => (
          <div key={e.id} style={{ ...styles.event, borderLeftColor: EPI_COLOR[e.epistemic_status] }}>
            <div style={styles.eventDate}>{e.time.display}</div>
            <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem" }}>
              <span style={styles.eventTitle}>{e.title}</span>
              <span style={styles.eventMeta}>
                {e.universe_or_scope} {e.source_refs.length > 0 ? `· ${e.source_refs.join(", ")}` : ""}
              </span>
            </div>
            {e.summary && <div style={styles.eventDesc}>{e.summary}</div>}
            {(e.location || (e.characters && e.characters.length > 0)) && (
              <div style={{ marginTop: "0.5rem", fontSize: "0.78rem", color: "#9aa3b2" }}>
                {e.location && <div>📍 {e.location}</div>}
                {e.characters && e.characters.length > 0 && <div>👤 {e.characters.join(", ")}</div>}
              </div>
            )}
            <div style={{ marginTop: "0.5rem", display: "flex", gap: "0.5rem" }}>
              <span style={styles.badge}>{e.epistemic_status}</span>
              <span style={{ ...styles.badge, background: "#2c3d2c", color: "#9fcf9f" }}>{e.canonicality}</span>
              <span style={{ ...styles.badge, background: "#22314a", color: "#a9c1e8" }}>{e.time.certainty}</span>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: { minHeight: "100vh", background: "#05070c", color: "#d8dbe0", fontFamily: "Lora, serif", padding: "3rem 1rem" },
  eyebrow: { fontFamily: "Lato, sans-serif", fontSize: "0.62rem", fontWeight: 700, letterSpacing: "0.3em", textTransform: "uppercase", color: "#cba25f" },
  h1: { fontFamily: "'Crimson Text', serif", fontWeight: 400, fontSize: "2.4rem", color: "#f2ede1", margin: "0.5rem 0" },
  input: { background: "#0c1119", border: "1px solid #1e2733", color: "#d8dbe0", padding: "0.5rem 0.8rem", borderRadius: "2px", fontFamily: "Lora, serif" },
  select: { background: "#0c1119", border: "1px solid #1e2733", color: "#d8dbe0", padding: "0.5rem 0.8rem", borderRadius: "2px", fontFamily: "Lato, sans-serif", fontSize: "0.8rem" },
  button: { marginLeft: "0.5rem", background: "#cba25f", border: "none", color: "#05070c", padding: "0.5rem 1.1rem", borderRadius: "2px", fontFamily: "Lato, sans-serif", fontWeight: 700, cursor: "pointer" },
  controls: { display: "flex", flexWrap: "wrap", gap: "0.6rem", justifyContent: "center", marginBottom: "2rem" },
  chip: { fontFamily: "Lato, sans-serif", fontSize: "0.62rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", padding: "0.4rem 0.85rem", border: "1px solid", borderRadius: "2px", cursor: "pointer" },
  event: { background: "#0c1119", border: "1px solid #1e2733", borderLeftWidth: "3px", borderLeftStyle: "solid", padding: "1.1rem 1.4rem", marginBottom: "0.9rem", borderRadius: "2px" },
  eventDate: { fontFamily: "Lato, sans-serif", fontSize: "0.62rem", letterSpacing: "0.12em", color: "#cba25f", textTransform: "uppercase", marginBottom: "0.35rem" },
  eventTitle: { fontFamily: "'Crimson Text', serif", fontSize: "1.2rem", color: "#f2ede1" },
  eventMeta: { fontFamily: "Lato, sans-serif", fontSize: "0.58rem", color: "#7b8494" },
  eventDesc: { marginTop: "0.5rem", fontSize: "0.85rem", color: "#7b8494", lineHeight: 1.6 },
  badge: { fontSize: "0.58rem", fontFamily: "Lato, sans-serif", padding: "0.15rem 0.5rem", borderRadius: "2px", background: "#22314a", color: "#a9c1e8" },
};
