"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import OperationsStrip from "./OperationsStrip";

type Task = {
  project_id: string;
  project_name: string;
  repository: string;
  file: string;
  html_url: string;
  canonical: boolean;
  id: string;
  title: string | null;
  source: string | null;
  target: string | null;
  priority: string | null;
  created: string | null;
};

type LiveTask = {
  id: string;
  external_id: string | null;
  type: string;
  source_project: string | null;
  target_project: string | null;
  status: string;
  priority: string | null;
  blocked_reason: string | null;
  repository: string | null;
  pr_url: string | null;
};

type Integration = { target: string; required: boolean };

type Project = {
  id: string;
  name: string;
  repository: string;
  repository_url: string;
  production_url: string | null;
  role: string;
  integrations: Integration[];
  overall: "healthy" | "degraded" | "critical" | "unknown";
  branch: string | null;
  version: string | null;
  last_push: string | null;
  open_tasks: number;
  open_prs: number | null;
};

type Product = {
  id: string;
  name: string;
  repository: string;
  repository_url: string;
  production_url: string | null;
  category: string;
  description?: string;
  overall: "healthy" | "critical";
  branch: string | null;
  last_push: string | null;
  open_prs: number | null;
};

type Status = {
  generated_at: string;
  summary: {
    projects: number;
    products: number;
    overall_counts: Record<string, number>;
    open_external_tasks_total: number;
    open_pull_requests_total: number;
  };
  projects: Project[];
  products: Product[];
  tasks: Task[];
};

type Point = { x: number; y: number };
type EdgeSummary = { source: Project; target: Project; count: number; priority: string; blocked: boolean };

const PRIO_RANK: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
const PROJECT_ALIASES: Record<string, string> = {
  eco: "ecosystem",
  ecosystem: "ecosystem",
  eng: "engineering",
  engineering: "engineering",
  nox: "noxia",
  noxia: "noxia",
  ssf: "ssf",
  kg: "knowledge-graph",
  knowledgegraph: "knowledge-graph",
  ota: "ota",
  kue: "kueper-com",
  kuepercom: "kueper-com",
  tkd: "thomas-kueper-de",
  thomaskueperde: "thomas-kueper-de",
  nxu: "noxia-universe",
  noxiauniverse: "noxia-universe",
  mish: "mishkenaz",
  mishkenaz: "mishkenaz",
  omni: "omnizedenz",
  omnizedenz: "omnizedenz",
  avi: "avi-modell",
  avimodell: "avi-modell",
  kon: "contracomology",
  contracomology: "contracomology",
  archive: "kueper-archive-schema",
  kueperarchiveschema: "kueper-archive-schema",
  endia: "endia",
  zereya: "zereya",
  davaru: "davaru",
  fluidehermeneutik: "fluide-hermeneutik",
  resonanzethik: "resonanz-ethik",
};

function norm(value: string | null | undefined) {
  return (value || "").toLowerCase().replace(/[^a-z0-9]/g, "");
}

function fmtAge(iso: string | null): string {
  if (!iso) return "—";
  const mins = Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
  if (mins < 1) return "gerade eben";
  if (mins < 60) return `vor ${mins} min`;
  const h = Math.floor(mins / 60);
  if (h < 24) return `vor ${h} h`;
  return `vor ${Math.floor(h / 24)} d`;
}

function resolveProject(projects: Project[], ref: string | null) {
  if (!ref) return null;
  const variants = [ref, ref.includes(":") ? ref.split(":").pop() || ref : ref];
  for (const variant of variants) {
    const n = norm(variant);
    const alias = PROJECT_ALIASES[n];
    if (alias) {
      const matched = projects.find((p) => p.id === alias);
      if (matched) return matched;
    }
    const matched = projects.find((p) => norm(p.id) === n || norm(p.name) === n || norm(p.repository.split("/")[1]) === n);
    if (matched) return matched;
  }
  return null;
}

function effectiveLiveSource(task: LiveTask) {
  const current = norm(task.source_project);
  if ((current === "eco" || current === "ecosystem") && task.type !== "PR_REVIEW" && task.external_id) {
    const match = task.external_id.match(/^([A-Z]+)-([A-Z]+)-/);
    if (match?.[1] && PROJECT_ALIASES[norm(match[1])]) return match[1];
  }
  return task.source_project;
}

function strongestPriority(a: string, b: string) {
  return (PRIO_RANK[a] ?? 4) <= (PRIO_RANK[b] ?? 4) ? a : b;
}

function aggregateEdges(projects: Project[], items: { source: string | null; target: string | null; priority: string | null; blocked?: boolean }[]) {
  const map = new Map<string, EdgeSummary>();
  for (const item of items) {
    const source = resolveProject(projects, item.source);
    const target = resolveProject(projects, item.target);
    if (!source || !target || source.id === target.id) continue;
    const key = `${source.id}->${target.id}`;
    const priority = item.priority || "medium";
    const existing = map.get(key);
    if (existing) {
      existing.count += 1;
      existing.priority = strongestPriority(existing.priority, priority);
      existing.blocked = existing.blocked || Boolean(item.blocked);
    } else {
      map.set(key, { source, target, count: 1, priority, blocked: Boolean(item.blocked) });
    }
  }
  return [...map.values()];
}

function EcosystemGraph({ projects, tasks, liveTasks, onSelect }: { projects: Project[]; tasks: Task[]; liveTasks: LiveTask[]; onSelect: (p: Project) => void }) {
  const graphProjects = projects;

  const positions = useMemo(() => {
    const map = new Map<string, Point>();
    const control = graphProjects.find((p) => p.id === "ecosystem");
    if (control) map.set(control.id, { x: 600, y: 260 });
    const outer = graphProjects.filter((p) => p.id !== "ecosystem");
    const innerCount = Math.min(8, outer.length);
    const inner = outer.slice(0, innerCount);
    const far = outer.slice(innerCount);
    inner.forEach((p, i) => {
      const angle = -Math.PI / 2 + (i * Math.PI * 2) / Math.max(inner.length, 1);
      map.set(p.id, { x: 600 + Math.cos(angle) * 285, y: 260 + Math.sin(angle) * 142 });
    });
    far.forEach((p, i) => {
      const angle = -Math.PI / 2 + Math.PI / Math.max(far.length, 1) + (i * Math.PI * 2) / Math.max(far.length, 1);
      map.set(p.id, { x: 600 + Math.cos(angle) * 505, y: 260 + Math.sin(angle) * 226 });
    });
    return map;
  }, [graphProjects]);

  const integrationEdges = useMemo(() => {
    const seen = new Set<string>();
    const edges: { source: Project; target: Project; required: boolean }[] = [];
    for (const source of graphProjects) {
      for (const integration of source.integrations || []) {
        const target = graphProjects.find((p) => p.id === integration.target);
        if (!target) continue;
        const key = `${source.id}->${target.id}`;
        if (seen.has(key)) continue;
        seen.add(key);
        edges.push({ source, target, required: integration.required });
      }
    }
    return edges;
  }, [graphProjects]);

  const backlogEdges = useMemo(
    () => aggregateEdges(graphProjects, tasks.map((task) => ({ source: task.source, target: task.target, priority: task.priority }))),
    [tasks, graphProjects],
  );

  const lifecycleTasks = useMemo(
    () => liveTasks.filter((task) => ["pending", "claimed", "running", "review_pending", "blocked"].includes(task.status)),
    [liveTasks],
  );

  const liveEdges = useMemo(
    () => aggregateEdges(graphProjects, lifecycleTasks.map((task) => ({
      source: effectiveLiveSource(task),
      target: task.target_project,
      priority: task.priority,
      blocked: Boolean(task.blocked_reason) || task.status === "blocked",
    }))),
    [lifecycleTasks, graphProjects],
  );

  const liveByProject = useMemo(() => {
    const counts = new Map<string, number>();
    for (const edge of liveEdges) {
      counts.set(edge.source.id, (counts.get(edge.source.id) || 0) + edge.count);
      counts.set(edge.target.id, (counts.get(edge.target.id) || 0) + edge.count);
    }
    return counts;
  }, [liveEdges]);

  return (
    <div className="graph-shell">
      <div className="graph-head">
        <div>
          <span className="eyebrow">Live collaboration map · {graphProjects.length}/{projects.length} Projekte</span>
          <h2>Ecosystem Flow</h2>
        </div>
        <div className="graph-legend">
          <span><i className="legend-line base" /> Integration</span>
          <span><i className="legend-line" /> Request-Backlog</span>
          <span><i className="legend-line active" /> aktiver Lifecycle</span>
        </div>
      </div>
      <svg className="eco-graph" viewBox="0 0 1200 520" style={{ minHeight: 0, height: 410 }} role="img" aria-label="Vollständiger Beziehungs- und Lifecycle-Graph des KUEPER Ecosystems">
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" className="arrow-head" />
          </marker>
          <marker id="arrow-active" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" className="arrow-head active" />
          </marker>
        </defs>

        {integrationEdges.map(({ source, target, required }) => {
          const a = positions.get(source.id)!;
          const b = positions.get(target.id)!;
          return <line key={`integration-${source.id}-${target.id}`} x1={a.x} y1={a.y} x2={b.x} y2={b.y} className={`graph-edge ${required ? "required" : "optional"}`} markerEnd="url(#arrow)" />;
        })}

        {backlogEdges.map(({ source, target, count }) => {
          const a = positions.get(source.id)!;
          const b = positions.get(target.id)!;
          const mx = (a.x + b.x) / 2;
          const my = (a.y + b.y) / 2;
          return (
            <g key={`backlog-${source.id}-${target.id}`} opacity={0.5}>
              <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} className="graph-edge required" markerEnd="url(#arrow)" />
              {count > 1 && <text x={mx} y={my - 4} textAnchor="middle" className="edge-count">{count}</text>}
            </g>
          );
        })}

        {liveEdges.map(({ source, target, count, priority, blocked }) => {
          const a = positions.get(source.id)!;
          const b = positions.get(target.id)!;
          const mx = (a.x + b.x) / 2;
          const my = (a.y + b.y) / 2;
          return (
            <g key={`live-${source.id}-${target.id}`}>
              <line
                x1={a.x}
                y1={a.y}
                x2={b.x}
                y2={b.y}
                className={`request-edge ${priority}`}
                markerEnd="url(#arrow-active)"
                style={blocked ? { animation: "none", opacity: 0.65, strokeDasharray: "4 7" } : undefined}
              />
              <text x={mx} y={my - 7} textAnchor="middle" className="edge-count live">{count}</text>
            </g>
          );
        })}

        {graphProjects.map((p) => {
          const pos = positions.get(p.id)!;
          const isControl = p.id === "ecosystem";
          const liveCount = liveByProject.get(p.id) || 0;
          const title = p.name.length > 18 ? p.name.slice(0, 16) + "…" : p.name;
          return (
            <g key={p.id} className="graph-node" onClick={() => onSelect(p)} role="button" tabIndex={0}>
              <circle cx={pos.x} cy={pos.y} r={isControl ? 41 : 32} className={`node-ring ${p.overall} ${isControl ? "control" : ""}`} />
              <circle cx={pos.x} cy={pos.y} r={isControl ? 35 : 27} className="node-core" />
              <text x={pos.x} y={pos.y - 2} textAnchor="middle" className="node-title">{title}</text>
              <text x={pos.x} y={pos.y + 13} textAnchor="middle" className="node-meta">{liveCount ? `${liveCount} live` : p.open_tasks ? `${p.open_tasks} offen` : p.role}</text>
            </g>
          );
        })}
      </svg>
      <div className="graph-foot">Alle registrierten Projekte · statische Kanten = Beziehungen/Backlog · nur tatsächlich laufende oder reviewende Control-Plane-Vorgänge animieren; blockierte Vorgänge stehen still.</div>
      <style jsx global>{`
        .edge-count { fill: var(--muted-2); font: 9px var(--font-mono); paint-order: stroke; stroke: #171d26; stroke-width: 4px; }
        .edge-count.live { fill: var(--solar); font-weight: 700; }
        @media (max-width: 900px) { .eco-graph { height: 360px !important; } }
        @media (max-width: 640px) { .eco-graph { height: 320px !important; } }
      `}</style>
    </div>
  );
}

export default function Page() {
  const [data, setData] = useState<Status | null>(null);
  const [liveTasks, setLiveTasks] = useState<LiveTask[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState("all");
  const [tab, setTab] = useState<"ecosystem" | "products">("ecosystem");
  const [selected, setSelected] = useState<Project | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [statusRes, tracesRes] = await Promise.all([
        fetch("/api/status", { cache: "no-store" }),
        fetch("/api/traces", { cache: "no-store" }),
      ]);
      const json = await statusRes.json();
      if (!statusRes.ok) throw new Error(json?.error || `HTTP ${statusRes.status}`);
      setData(json);

      if (tracesRes.ok) {
        const traces = await tracesRes.json();
        setLiveTasks(Array.isArray(traces?.tasks) ? traces.tasks : []);
      } else {
        setLiveTasks([]);
      }
    } catch (e: any) {
      setError(e?.message || "Unbekannter Fehler");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const tasks = (data?.tasks || []).filter((t) => filter === "all" || t.project_id === filter).sort((a, b) => {
    const pa = PRIO_RANK[a.priority || ""] ?? 4;
    const pb = PRIO_RANK[b.priority || ""] ?? 4;
    if (pa !== pb) return pa - pb;
    return (a.created || "").localeCompare(b.created || "");
  });

  const counts = data?.summary.overall_counts || {};

  return (
    <main className="wrap control-room">
      <header className="console control-header">
        <div className="brand">
          <span className="kicker">KUEPER · Control Plane</span>
          <h1>Control Room</h1>
          <span className="sub">Projekte, Produkte und die Arbeit, die zwischen ihnen im Hintergrund fließt.</span>
        </div>
        <div className="controls">
          <div className="stamp">{data ? <>Stand {new Date(data.generated_at).toLocaleTimeString("de-DE")}<br />{new Date(data.generated_at).toLocaleDateString("de-DE")}</> : "—"}</div>
          <button className="refresh" onClick={load} disabled={loading}>{loading ? "Lädt…" : "Aktualisieren"}</button>
        </div>
      </header>

      <nav className="view-tabs" aria-label="Dashboard-Bereiche">
        <button className={tab === "ecosystem" ? "active" : ""} onClick={() => setTab("ecosystem")}>Ecosystem</button>
        <button className={tab === "products" ? "active" : ""} onClick={() => setTab("products")}>Products <span>{data?.summary.products || 0}</span></button>
      </nav>

      {error && <div className="errbox">Konnte den Status nicht laden. <span className="mono">{error}</span></div>}

      {data && tab === "ecosystem" && (
        <>
          <section className="summary ops-summary">
            <div className="metric"><span className="val mono">{data.summary.projects}</span><span className="lbl">Projekte</span></div>
            <div className="metric"><span className="val mono">{data.summary.open_external_tasks_total}</span><span className="lbl">Requests unterwegs</span></div>
            <div className="metric"><span className="val mono">{data.summary.open_pull_requests_total}</span><span className="lbl">Offene PRs</span></div>
            <div className="metric health-metric"><div className="leds"><span className="led"><span className="dot healthy" />{counts.healthy || 0}</span><span className="led"><span className="dot degraded" />{counts.degraded || 0}</span><span className="led"><span className="dot critical" />{counts.critical || 0}</span></div><span className="lbl">Systemzustand</span></div>
          </section>

          <OperationsStrip />
          <EcosystemGraph projects={data.projects} tasks={data.tasks} liveTasks={liveTasks} onSelect={setSelected} />

          {selected && (
            <aside className="project-detail">
              <div className="detail-main">
                <span className={`dot ${selected.overall}`} />
                <div><span className="eyebrow">{selected.role}</span><h3>{selected.name}</h3><p>{selected.repository}</p></div>
              </div>
              <div className="detail-stats"><span><b>{selected.open_tasks}</b> Requests</span><span><b>{selected.open_prs ?? "—"}</b> PRs</span><span><b>{fmtAge(selected.last_push)}</b> letzter Push</span></div>
              <div className="detail-actions">
                {selected.production_url && <a href={selected.production_url} target="_blank" rel="noreferrer">Website öffnen ↗</a>}
                <a href={selected.repository_url} target="_blank" rel="noreferrer">Repository ↗</a>
                <button onClick={() => setSelected(null)}>Schließen</button>
              </div>
            </aside>
          )}

          <div className="section-head"><h2>Projektstatus</h2><span className="count">{data.projects.length} registriert</span></div>
          <div className="grid project-grid-modern">
            {data.projects.map((p) => (
              <div className="card project-card" key={p.id}>
                <div className="top"><span className={`dot ${p.overall}`} /><span className="name">{p.name}</span><span className="role">{p.role}</span></div>
                <div className="meta"><span>Branch</span><b>{p.branch || "—"}</b><span>Letzter Push</span><b>{fmtAge(p.last_push)}</b><span>PRs</span><b>{p.open_prs ?? "—"}</b></div>
                <div className="project-actions">
                  {p.production_url && <a href={p.production_url} target="_blank" rel="noreferrer">Website ↗</a>}
                  <a href={p.repository_url} target="_blank" rel="noreferrer">GitHub ↗</a>
                </div>
              </div>
            ))}
          </div>

          <div className="section-head"><h2>Request Stream</h2><span className="count">{tasks.length} angezeigt · nach Priorität</span></div>
          <div className="filters"><button className={`chip ${filter === "all" ? "active" : ""}`} onClick={() => setFilter("all")}>alle</button>{data.projects.filter((p) => p.open_tasks > 0).map((p) => <button key={p.id} className={`chip ${filter === p.id ? "active" : ""}`} onClick={() => setFilter(p.id)}>{p.name} · {p.open_tasks}</button>)}</div>
          <div className="tasks">
            {tasks.length === 0 ? <div className="empty">Keine offenen Tasks in dieser Auswahl.</div> : tasks.map((t) => (
              <a className="trow" key={t.html_url} href={t.html_url} target="_blank" rel="noopener noreferrer">
                <span className={`pri ${t.priority || "none"}`} />
                <div className="t-main"><div className="t-title">{t.title || t.file.replace(/\.md$/, "")}</div><div className="t-id">{t.id}{t.canonical ? "" : " · legacy-Format"}</div></div>
                <div className="t-route">{t.source && t.target ? <>{t.source} <span className="arr">→</span> {t.target}</> : t.project_name}</div>
                <div className="t-date">{t.created || "—"}</div><div className="t-open">Trace ↗</div>
              </a>
            ))}
          </div>
        </>
      )}

      {data && tab === "products" && (
        <section className="products-view">
          <div className="products-intro"><span className="eyebrow">Separate operational layer</span><h2>Products</h2><p>Eigenständige Anwendungen, die vom Ecosystem entwickelt und beobachtet werden, aber nicht Teil seines fachlichen Wissens- und Request-Graphen sind.</p></div>
          <div className="product-grid">
            {data.products.map((p) => (
              <article className="product-card" key={p.id}>
                <div className="product-top"><span className={`dot ${p.overall}`} /><span>{p.category}</span></div>
                <h3>{p.name}</h3><p>{p.description}</p>
                <div className="product-stats"><span><b>{p.open_prs ?? "—"}</b> offene PRs</span><span><b>{fmtAge(p.last_push)}</b> letzter Push</span><span><b>{p.branch || "—"}</b> Branch</span></div>
                <div className="project-actions">{p.production_url && <a href={p.production_url} target="_blank" rel="noreferrer">App öffnen ↗</a>}<a href={p.repository_url} target="_blank" rel="noreferrer">GitHub ↗</a></div>
              </article>
            ))}
          </div>
        </section>
      )}

      {!data && !error && <div className="empty">Control-Room-Telemetrie wird geladen…</div>}
    </main>
  );
}
