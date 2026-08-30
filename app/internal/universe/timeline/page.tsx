"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
  type WheelEvent as ReactWheelEvent,
} from "react";
import {
  buildTicks,
  clusterByPixel,
  extent,
  formatAxisYear,
  panViewport,
  temporalToYear,
  yearToRatio,
  zoomViewport,
  type TimelineViewport,
} from "./timeline-math";

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

type ClusterPoint = {
  id: string;
  temporal: UniverseEvent["time"];
  event: UniverseEvent;
};

const EPI_COLOR: Record<string, string> = {
  established: "#7fae7f",
  theoretical: "#4a6fa5",
  speculative: "#3e7c8a",
  fictional: "#a5658a",
};

const DEFAULT_VIEWPORT: TimelineViewport = { min: -10_000, max: 2100 };
const LANE_HEIGHT = 74;
const AXIS_HEIGHT = 46;

function sortKey(e: UniverseEvent): number {
  return temporalToYear(e.time) ?? Number.MAX_SAFE_INTEGER;
}

function TimelineExplorer({ events, onSelect }: { events: UniverseEvent[]; onSelect: (event: UniverseEvent) => void }) {
  const shellRef = useRef<HTMLDivElement | null>(null);
  const dragRef = useRef<{ x: number; viewport: TimelineViewport } | null>(null);
  const [width, setWidth] = useState(900);

  const bounds = useMemo(
    () => extent(events.map((event) => ({ id: event.id, temporal: event.time })), DEFAULT_VIEWPORT),
    [events]
  );
  const [viewport, setViewport] = useState<TimelineViewport>(bounds);

  useEffect(() => {
    setViewport(bounds);
  }, [bounds.min, bounds.max]);

  useEffect(() => {
    const element = shellRef.current;
    if (!element) return;
    const observer = new ResizeObserver((entries) => {
      const nextWidth = entries[0]?.contentRect.width;
      if (nextWidth && nextWidth > 0) setWidth(nextWidth);
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const scopes = useMemo(
    () => Array.from(new Set(events.map((event) => event.universe_or_scope))).sort(),
    [events]
  );
  const ticks = useMemo(() => buildTicks(viewport, Math.max(5, Math.floor(width / 150))), [viewport, width]);
  const span = viewport.max - viewport.min;

  const zoom = (factor: number, ratio = 0.5) => {
    setViewport((current) => zoomViewport(current, bounds, factor, ratio));
  };

  const handleWheel = (event: ReactWheelEvent<HTMLDivElement>) => {
    event.preventDefault();
    const rect = event.currentTarget.getBoundingClientRect();
    const ratio = rect.width > 0 ? (event.clientX - rect.left) / rect.width : 0.5;
    zoom(event.deltaY > 0 ? 1.35 : 0.72, ratio);
  };

  const handlePointerDown = (event: ReactPointerEvent<HTMLDivElement>) => {
    event.currentTarget.setPointerCapture(event.pointerId);
    dragRef.current = { x: event.clientX, viewport };
  };

  const handlePointerMove = (event: ReactPointerEvent<HTMLDivElement>) => {
    const drag = dragRef.current;
    if (!drag) return;
    const dx = event.clientX - drag.x;
    const deltaYears = -(dx / Math.max(width, 1)) * (drag.viewport.max - drag.viewport.min);
    setViewport(panViewport(drag.viewport, bounds, deltaYears));
  };

  const handlePointerEnd = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
    dragRef.current = null;
  };

  return (
    <section style={styles.timelineSection}>
      <div style={styles.timelineToolbar}>
        <div>
          <strong style={{ color: "#f2ede1" }}>Zeitfenster</strong>{" "}
          <span style={{ color: "#7b8494" }}>
            {formatAxisYear(viewport.min, span)} – {formatAxisYear(viewport.max, span)}
          </span>
        </div>
        <div style={{ display: "flex", gap: "0.4rem" }}>
          <button type="button" onClick={() => zoom(0.55)} style={styles.smallButton} aria-label="Hineinzoomen">+</button>
          <button type="button" onClick={() => zoom(1.8)} style={styles.smallButton} aria-label="Herauszoomen">−</button>
          <button type="button" onClick={() => setViewport(bounds)} style={styles.smallButton}>Alles</button>
        </div>
      </div>

      <div
        ref={shellRef}
        onWheel={handleWheel}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerEnd}
        onPointerCancel={handlePointerEnd}
        style={styles.timelineShell}
        title="Ziehen zum Verschieben · Mausrad/Trackpad zum Zoomen"
      >
        <div style={{ height: AXIS_HEIGHT + scopes.length * LANE_HEIGHT, minHeight: 220, position: "relative", userSelect: "none" }}>
          <div style={{ position: "absolute", left: 0, right: 0, top: AXIS_HEIGHT - 1, borderTop: "1px solid #2a3544" }} />

          {ticks.map((tick) => {
            const left = `${yearToRatio(tick, viewport) * 100}%`;
            return (
              <div key={tick} style={{ position: "absolute", left, top: 0, bottom: 0, pointerEvents: "none" }}>
                <div style={styles.tickLabel}>{formatAxisYear(tick, span)}</div>
                <div style={styles.tickLine} />
              </div>
            );
          })}

          {scopes.map((scope, laneIndex) => {
            const laneEvents = events.filter((event) => event.universe_or_scope === scope);
            const clusterInput: ClusterPoint[] = laneEvents.map((event) => ({ id: event.id, temporal: event.time, event }));
            const clusters = clusterByPixel(clusterInput, viewport, width, 28);
            const top = AXIS_HEIGHT + laneIndex * LANE_HEIGHT;

            return (
              <div key={scope} style={{ position: "absolute", left: 0, right: 0, top, height: LANE_HEIGHT, borderBottom: "1px solid #151d28" }}>
                <div style={styles.laneLabel}>{scope}</div>
                {clusters.map((cluster, clusterIndex) => {
                  const item = cluster.items[0];
                  const left = cluster.x;
                  const multi = cluster.items.length > 1;
                  const color = multi ? "#cba25f" : EPI_COLOR[item.event.epistemic_status] ?? "#8ea0b8";

                  return (
                    <button
                      type="button"
                      key={`${scope}-${clusterIndex}-${item.id}`}
                      onPointerDown={(ev) => ev.stopPropagation()}
                      onClick={(ev) => {
                        ev.stopPropagation();
                        if (multi) {
                          const ratio = Math.min(Math.max(cluster.x / Math.max(width, 1), 0), 1);
                          zoom(0.28, ratio);
                        } else {
                          onSelect(item.event);
                        }
                      }}
                      title={multi ? `${cluster.items.length} Ereignisse — klicken zum Zoomen` : `${item.event.time.display}: ${item.event.title}`}
                      style={{
                        ...styles.marker,
                        left: Math.max(10, Math.min(width - 10, left)),
                        background: color,
                        width: multi ? 28 : 14,
                        height: multi ? 28 : 14,
                        marginLeft: multi ? -14 : -7,
                        marginTop: multi ? -14 : -7,
                      }}
                    >
                      {multi ? cluster.items.length : ""}
                    </button>
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>
      <div style={styles.timelineHint}>Ziehen = Zeit verschieben · Mausrad/Trackpad = Zoom · Clusterzahl anklicken = hineinzoomen</div>
    </section>
  );
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
  const [canonFilter, setCanonFilter] = useState<string>("all");
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<UniverseEvent | null>(null);

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
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unbekannter Fehler");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (token) load(token);
  }, [token, load]);

  const scopes = useMemo(() => {
    if (!data) return [];
    return Array.from(new Set(data.events.map((e) => e.universe_or_scope))).sort();
  }, [data]);

  const filtered = useMemo(() => {
    if (!data) return [];
    const normalizedQuery = query.trim().toLowerCase();
    return data.events
      .filter((e) => scopeFilter === "all" || e.universe_or_scope === scopeFilter)
      .filter((e) => epiFilter.has(e.epistemic_status))
      .filter((e) => canonFilter === "all" || e.canonicality === canonFilter)
      .filter((e) => !normalizedQuery || e.title.toLowerCase().includes(normalizedQuery) || e.id.toLowerCase().includes(normalizedQuery))
      .sort((a, b) => sortKey(a) - sortKey(b));
  }, [data, scopeFilter, epiFilter, canonFilter, query]);

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
              if (tokenInput.trim()) setToken(tokenInput.trim());
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
            <button type="submit" style={styles.button}>Öffnen</button>
          </form>
          {error && <p style={{ color: "#c77", marginTop: "1rem" }}>{error}</p>}
        </div>
      </main>
    );
  }

  return (
    <main style={styles.page}>
      <header style={{ textAlign: "center", marginBottom: "1.6rem" }}>
        <div style={styles.eyebrow}>Küper Ecosystem · Internal · v0.2 Histography View</div>
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
          {scopes.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={canonFilter} onChange={(e) => setCanonFilter(e.target.value)} style={styles.select}>
          <option value="all">Alle Kanonstatus</option>
          <option value="canonical">canonical</option>
          <option value="provisional">provisional</option>
          <option value="draft">draft</option>
          <option value="deprecated">deprecated</option>
        </select>
        {["established", "theoretical", "speculative", "fictional"].map((k) => (
          <button
            type="button"
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

      {data && !loading && <TimelineExplorer events={filtered} onSelect={setSelected} />}

      {selected && (
        <section style={styles.detailPanel}>
          <button type="button" onClick={() => setSelected(null)} style={{ ...styles.smallButton, float: "right" }}>×</button>
          <div style={styles.eventDate}>{selected.time.display}</div>
          <h2 style={{ ...styles.eventTitle, fontSize: "1.55rem", margin: "0.2rem 0 0.5rem" }}>{selected.title}</h2>
          <div style={styles.eventMeta}>{selected.universe_or_scope} · {selected.id}</div>
          <p style={{ ...styles.eventDesc, fontSize: "0.95rem" }}>{selected.summary}</p>
          {selected.location && <div style={styles.detailLine}>📍 {selected.location}</div>}
          {selected.characters && selected.characters.length > 0 && <div style={styles.detailLine}>👤 {selected.characters.join(", ")}</div>}
          {selected.source_refs.length > 0 && <div style={styles.detailLine}>Quellen: {selected.source_refs.join(", ")}</div>}
          {selected.relation_refs.length > 0 && <div style={styles.detailLine}>Relationen: {selected.relation_refs.join(", ")}</div>}
          <div style={{ marginTop: "0.8rem", display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
            <span style={styles.badge}>{selected.epistemic_status}</span>
            <span style={{ ...styles.badge, background: "#2c3d2c", color: "#9fcf9f" }}>{selected.canonicality}</span>
            <span style={{ ...styles.badge, background: "#22314a", color: "#a9c1e8" }}>{selected.time.certainty}</span>
            <span style={{ ...styles.badge, background: "#332c22", color: "#d8bf92" }}>{selected.time.precision}</span>
          </div>
        </section>
      )}

      <details style={{ maxWidth: 980, margin: "1.5rem auto" }}>
        <summary style={styles.listSummary}>Chronologische Listenansicht ({filtered.length})</summary>
        <div style={{ borderLeft: "2px solid #1e2733", paddingLeft: "2rem", marginTop: "1rem" }}>
          {filtered.map((e) => (
            <button type="button" key={e.id} onClick={() => setSelected(e)} style={{ ...styles.event, textAlign: "left", width: "100%", cursor: "pointer", borderLeftColor: EPI_COLOR[e.epistemic_status] }}>
              <div style={styles.eventDate}>{e.time.display}</div>
              <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem" }}>
                <span style={styles.eventTitle}>{e.title}</span>
                <span style={styles.eventMeta}>{e.universe_or_scope} {e.source_refs.length > 0 ? `· ${e.source_refs.join(", ")}` : ""}</span>
              </div>
            </button>
          ))}
        </div>
      </details>
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
  smallButton: { background: "#111925", color: "#d8dbe0", border: "1px solid #2a3544", minWidth: 34, height: 30, borderRadius: "3px", cursor: "pointer", fontFamily: "Lato, sans-serif" },
  controls: { display: "flex", flexWrap: "wrap", gap: "0.6rem", justifyContent: "center", marginBottom: "1.4rem" },
  chip: { fontFamily: "Lato, sans-serif", fontSize: "0.62rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", padding: "0.4rem 0.85rem", border: "1px solid", borderRadius: "2px", cursor: "pointer" },
  timelineSection: { maxWidth: 1180, margin: "0 auto", background: "#080d14", border: "1px solid #1e2733", borderRadius: "4px", overflow: "hidden" },
  timelineToolbar: { display: "flex", justifyContent: "space-between", alignItems: "center", gap: "1rem", padding: "0.65rem 0.9rem", borderBottom: "1px solid #1e2733", fontFamily: "Lato, sans-serif", fontSize: "0.72rem" },
  timelineShell: { position: "relative", overflow: "hidden", cursor: "grab", touchAction: "none", background: "linear-gradient(180deg, #0a1018 0%, #070b11 100%)" },
  timelineHint: { padding: "0.55rem 0.9rem", borderTop: "1px solid #151d28", color: "#687385", fontFamily: "Lato, sans-serif", fontSize: "0.66rem", textAlign: "center" },
  tickLabel: { position: "absolute", top: 9, transform: "translateX(-50%)", color: "#697589", fontFamily: "Lato, sans-serif", fontSize: "0.58rem", whiteSpace: "nowrap" },
  tickLine: { position: "absolute", top: AXIS_HEIGHT - 1, bottom: 0, borderLeft: "1px solid #182231" },
  laneLabel: { position: "absolute", left: 9, top: 7, zIndex: 2, padding: "0.12rem 0.35rem", background: "rgba(5,7,12,0.78)", color: "#aab2bf", fontFamily: "Lato, sans-serif", fontSize: "0.56rem", letterSpacing: "0.09em", textTransform: "uppercase", pointerEvents: "none" },
  marker: { position: "absolute", top: "55%", border: "2px solid #05070c", borderRadius: "50%", color: "#05070c", fontFamily: "Lato, sans-serif", fontWeight: 800, fontSize: "0.58rem", lineHeight: 1, display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", boxShadow: "0 0 0 1px rgba(255,255,255,0.12)" },
  detailPanel: { maxWidth: 980, margin: "1.2rem auto 0", padding: "1.2rem 1.4rem", background: "#0c1119", border: "1px solid #263244", borderLeft: "3px solid #cba25f", borderRadius: "3px" },
  detailLine: { marginTop: "0.45rem", color: "#9aa3b2", fontSize: "0.82rem" },
  listSummary: { color: "#9aa3b2", cursor: "pointer", fontFamily: "Lato, sans-serif", fontSize: "0.75rem", letterSpacing: "0.08em", textTransform: "uppercase" },
  event: { display: "block", background: "#0c1119", color: "inherit", border: "1px solid #1e2733", borderLeftWidth: "3px", borderLeftStyle: "solid", padding: "1.1rem 1.4rem", marginBottom: "0.9rem", borderRadius: "2px" },
  eventDate: { fontFamily: "Lato, sans-serif", fontSize: "0.62rem", letterSpacing: "0.12em", color: "#cba25f", textTransform: "uppercase", marginBottom: "0.35rem" },
  eventTitle: { fontFamily: "'Crimson Text', serif", fontSize: "1.2rem", color: "#f2ede1" },
  eventMeta: { fontFamily: "Lato, sans-serif", fontSize: "0.58rem", color: "#7b8494" },
  eventDesc: { marginTop: "0.5rem", fontSize: "0.85rem", color: "#9aa3b2", lineHeight: 1.6 },
  badge: { fontSize: "0.58rem", fontFamily: "Lato, sans-serif", padding: "0.15rem 0.5rem", borderRadius: "2px", background: "#22314a", color: "#a9c1e8" },
};
