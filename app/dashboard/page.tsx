"use client";

import { useCallback, useEffect, useState } from "react";

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

type Project = {
  id: string;
  name: string;
  repository: string;
  role: string;
  overall: "healthy" | "degraded" | "critical" | "unknown";
  branch: string | null;
  version: string | null;
  last_push: string | null;
  open_tasks: number;
};

type Status = {
  generated_at: string;
  summary: { projects: number; overall_counts: Record<string, number>; open_external_tasks_total: number };
  projects: Project[];
  tasks: Task[];
};

const PRIO_RANK: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };

function fmtAge(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso).getTime();
  const mins = Math.floor((Date.now() - d) / 60000);
  if (mins < 1) return "gerade eben";
  if (mins < 60) return `vor ${mins} min`;
  const h = Math.floor(mins / 60);
  if (h < 24) return `vor ${h} h`;
  const days = Math.floor(h / 24);
  return `vor ${days} d`;
}

export default function Page() {
  const [data, setData] = useState<Status | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<string>("all");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/status", { cache: "no-store" });
      const json = await res.json();
      if (!res.ok) throw new Error(json?.error || `HTTP ${res.status}`);
      setData(json);
    } catch (e: any) {
      setError(e?.message || "Unbekannter Fehler");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const tasks = (data?.tasks || [])
    .filter((t) => filter === "all" || t.project_id === filter)
    .sort((a, b) => {
      const pa = PRIO_RANK[a.priority || ""] ?? 4;
      const pb = PRIO_RANK[b.priority || ""] ?? 4;
      if (pa !== pb) return pa - pb;
      return (a.created || "").localeCompare(b.created || "");
    });

  const counts = data?.summary.overall_counts || {};

  return (
    <main className="wrap">
      <header className="console">
        <div className="brand">
          <span className="kicker">KUEPER · Control Plane</span>
          <h1>Ökosystem-Telemetrie</h1>
          <span className="sub">Live-Zustand und offene Cross-Repo-Aufgaben aller registrierten Projekte.</span>
        </div>
        <div className="controls">
          <div className="stamp">
            {data ? (
              <>
                Stand {new Date(data.generated_at).toLocaleTimeString("de-DE")}
                <br />
                {new Date(data.generated_at).toLocaleDateString("de-DE")}
              </>
            ) : (
              "—"
            )}
          </div>
          <button className="refresh" onClick={load} disabled={loading}>
            {loading ? "Lädt…" : "Aktualisieren"}
          </button>
        </div>
      </header>

      {error && (
        <div className="errbox">
          Konnte den Status nicht laden. <span className="mono">{error}</span>
          <br />
          Prüfe, ob <span className="mono">GH_TOKEN</span> in den Vercel-Env-Variablen gesetzt ist.
        </div>
      )}

      {data && (
        <>
          <section className="summary">
            <div className="metric">
              <span className="val mono">{data.summary.projects}</span>
              <span className="lbl">Projekte</span>
            </div>
            <div className="metric">
              <span className="val mono">{data.summary.open_external_tasks_total}</span>
              <span className="lbl">Offene Tasks</span>
            </div>
            <div className="metric" style={{ justifyContent: "flex-end" }}>
              <div className="leds">
                <span className="led"><span className="dot healthy" />{counts.healthy || 0}</span>
                <span className="led"><span className="dot degraded" />{counts.degraded || 0}</span>
                <span className="led"><span className="dot critical" />{counts.critical || 0}</span>
                {counts.unknown ? <span className="led"><span className="dot unknown" />{counts.unknown}</span> : null}
              </div>
              <span className="lbl" style={{ marginTop: 6 }}>Zustand</span>
            </div>
          </section>

          <div className="section-head">
            <h2>Projekte</h2>
            <span className="count">{data.projects.length} registriert</span>
          </div>
          <div className="grid">
            {data.projects.map((p) => (
              <div className="card" key={p.id}>
                <div className="top">
                  <span className={`dot ${p.overall}`} />
                  <span className="name">{p.name}</span>
                  <span className="role">{p.role}</span>
                </div>
                <div className="meta">
                  <span>Branch</span>
                  <b>{p.branch || "—"}</b>
                  <span>Version</span>
                  <b>{p.version || "—"}</b>
                  <span>Letzter Push</span>
                  <b>{fmtAge(p.last_push)}</b>
                </div>
                <div className="taskline">
                  {p.open_tasks > 0 ? (
                    <><b>{p.open_tasks}</b> offene Task{p.open_tasks === 1 ? "" : "s"}</>
                  ) : (
                    "keine offenen Tasks"
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="section-head">
            <h2>Offene Tasks</h2>
            <span className="count">{tasks.length} angezeigt · nach Priorität sortiert</span>
          </div>
          <div className="filters">
            <button className={`chip ${filter === "all" ? "active" : ""}`} onClick={() => setFilter("all")}>
              alle
            </button>
            {data.projects
              .filter((p) => p.open_tasks > 0)
              .map((p) => (
                <button
                  key={p.id}
                  className={`chip ${filter === p.id ? "active" : ""}`}
                  onClick={() => setFilter(p.id)}
                >
                  {p.name} · {p.open_tasks}
                </button>
              ))}
          </div>

          {tasks.length === 0 ? (
            <div className="tasks">
              <div className="empty">Keine offenen Tasks in dieser Auswahl.</div>
            </div>
          ) : (
            <div className="tasks">
              {tasks.map((t) => (
                <a className="trow" key={t.html_url} href={t.html_url} target="_blank" rel="noopener noreferrer">
                  <span className={`pri ${t.priority || "none"}`} />
                  <div className="t-main">
                    <div className="t-title">{t.title || t.file.replace(/\.md$/, "")}</div>
                    <div className="t-id">{t.id}{t.canonical ? "" : " · legacy-Format"}</div>
                  </div>
                  <div className="t-route">
                    {t.source && t.target ? (
                      <>{t.source} <span className="arr">→</span> {t.target}</>
                    ) : (
                      t.project_name
                    )}
                  </div>
                  <div className="t-date">{t.created || "—"}</div>
                  <div className="t-open">Öffnen ↗</div>
                </a>
              ))}
            </div>
          )}
        </>
      )}

      {!data && !error && <div className="empty">Telemetrie wird geladen…</div>}
    </main>
  );
}
