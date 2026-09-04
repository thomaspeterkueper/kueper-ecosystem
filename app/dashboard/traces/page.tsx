"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

type TraceTask = {
  id: string;
  external_id: string | null;
  type: string;
  source_project: string | null;
  target_project: string | null;
  status: string;
  priority: string | null;
  repository: string | null;
  branch: string | null;
  pr_url: string | null;
  parent_task_id: string | null;
  root_task_id: string | null;
  created_at: string;
  claimed_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  updated_at: string;
  blocked_reason: string | null;
  attempt_count: number | null;
};

type TraceResponse = {
  available: boolean;
  generated_at: string;
  reason?: string;
  tasks: TraceTask[];
};

type StageState = "done" | "active" | "waiting" | "blocked" | "skipped";

type Stage = {
  label: string;
  state: StageState;
  detail: string;
};

type Trace = {
  key: string;
  root: TraceTask;
  tasks: TraceTask[];
  stages: Stage[];
  active: boolean;
  blocked: boolean;
  latest: string;
};

const TERMINAL = new Set(["completed", "cancelled", "failed", "rejected"]);

function fmtTime(value: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleString("de-DE", { dateStyle: "short", timeStyle: "short" });
}

function stageState(done: boolean, active: boolean, blocked = false): StageState {
  if (blocked) return "blocked";
  if (done) return "done";
  if (active) return "active";
  return "waiting";
}

function buildTrace(tasks: TraceTask[]): Trace {
  const ordered = [...tasks].sort((a, b) => a.created_at.localeCompare(b.created_at));
  const root = ordered.find((t) => !t.parent_task_id) || ordered[0];
  const implementation = ordered.find((t) => t.type !== "PR_REVIEW" && t.type !== "REVIEW_FIX") || root;
  const review = [...ordered].reverse().find((t) => t.type === "PR_REVIEW");
  const fix = [...ordered].reverse().find((t) => t.type === "REVIEW_FIX");
  const prTask = [...ordered].reverse().find((t) => t.pr_url) || implementation;
  const blockedTask = [...ordered].reverse().find((t) => Boolean(t.blocked_reason));
  const terminal = ordered.every((t) => TERMINAL.has(t.status) || t.type === "PR_REVIEW" && t.status === "completed");
  const active = !terminal;

  const workerStarted = Boolean(implementation.started_at || implementation.claimed_at);
  const workerDone = Boolean(prTask.pr_url || implementation.completed_at);
  const hasPr = Boolean(prTask.pr_url);
  const reviewStarted = Boolean(review || implementation.status === "review_pending" || root.status === "review_pending");
  const reviewDone = Boolean(review?.status === "completed" || (terminal && hasPr));
  const fixNeeded = Boolean(fix);
  const fixDone = Boolean(fix && TERMINAL.has(fix.status));
  const done = Boolean(root.completed_at || terminal);

  const stages: Stage[] = [
    { label: "Queue", state: "done", detail: fmtTime(root.created_at) },
    {
      label: "Worker",
      state: root.type === "PR_REVIEW" ? "skipped" : stageState(workerDone, workerStarted, Boolean(blockedTask && !hasPr)),
      detail: root.type === "PR_REVIEW" ? "direkter PR" : workerStarted ? fmtTime(implementation.started_at || implementation.claimed_at) : "wartet",
    },
    {
      label: "PR",
      state: hasPr ? "done" : stageState(false, workerDone, Boolean(blockedTask && !hasPr)),
      detail: hasPr ? "erstellt" : "noch kein PR",
    },
    {
      label: "Review",
      state: stageState(reviewDone, reviewStarted, Boolean(blockedTask && reviewStarted && !reviewDone)),
      detail: review ? review.status : reviewStarted ? "review_pending" : "wartet",
    },
    {
      label: "Fix",
      state: fixNeeded ? stageState(fixDone, !fixDone, Boolean(fix?.blocked_reason)) : "skipped",
      detail: fixNeeded ? fix!.status : "nicht nötig",
    },
    {
      label: "Done",
      state: done ? "done" : "waiting",
      detail: done ? fmtTime(root.completed_at || ordered.map((t) => t.completed_at).filter(Boolean).sort().at(-1) || null) : "offen",
    },
  ];

  return {
    key: root.root_task_id || root.id,
    root,
    tasks: ordered,
    stages,
    active,
    blocked: Boolean(blockedTask),
    latest: ordered.map((t) => t.updated_at).sort().at(-1) || root.updated_at,
  };
}

export default function TracesPage() {
  const [data, setData] = useState<TraceResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<"active" | "all">("active");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/traces", { cache: "no-store" });
      setData(await response.json());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const traces = useMemo(() => {
    const rows = data?.tasks || [];
    const groups = new Map<string, TraceTask[]>();
    for (const task of rows) {
      const key = task.root_task_id || task.id;
      const group = groups.get(key) || [];
      group.push(task);
      groups.set(key, group);
    }
    return [...groups.values()]
      .map(buildTrace)
      .filter((trace) => mode === "all" || trace.active)
      .sort((a, b) => b.latest.localeCompare(a.latest));
  }, [data, mode]);

  const activeCount = useMemo(() => {
    if (!data) return 0;
    const groups = new Map<string, TraceTask[]>();
    for (const task of data.tasks) {
      const key = task.root_task_id || task.id;
      groups.set(key, [...(groups.get(key) || []), task]);
    }
    return [...groups.values()].map(buildTrace).filter((t) => t.active).length;
  }, [data]);

  return (
    <main className="wrap control-room trace-view">
      <header className="console control-header">
        <div className="brand">
          <span className="kicker">KUEPER · Control Plane</span>
          <h1>Request Traces</h1>
          <span className="sub">Realer Lifecycle aus Queue, Worker, PR, Review, Fix und Abschluss.</span>
        </div>
        <div className="controls">
          <div className="stamp">{data ? <>Stand {new Date(data.generated_at).toLocaleTimeString("de-DE")}<br />{new Date(data.generated_at).toLocaleDateString("de-DE")}</> : "—"}</div>
          <button className="refresh" onClick={load} disabled={loading}>{loading ? "Lädt…" : "Aktualisieren"}</button>
        </div>
      </header>

      {data && !data.available && (
        <div className="trace-unavailable">
          <b>GitHub-Ansicht aktiv, Control-Plane-Trace noch nicht verbunden.</b>
          <span>{data.reason}</span>
          <code>SUPABASE_SERVICE_ROLE_KEY</code>
        </div>
      )}

      {data?.available && (
        <>
          <section className="summary ops-summary trace-summary">
            <div className="metric"><span className="val mono">{activeCount}</span><span className="lbl">aktive Traces</span></div>
            <div className="metric"><span className="val mono">{data.tasks.filter((t) => t.status === "review_pending").length}</span><span className="lbl">Review pending</span></div>
            <div className="metric"><span className="val mono">{data.tasks.filter((t) => Boolean(t.blocked_reason) && !TERMINAL.has(t.status)).length}</span><span className="lbl">blockiert</span></div>
          </section>

          <div className="trace-filters">
            <button className={mode === "active" ? "active" : ""} onClick={() => setMode("active")}>Aktiv</button>
            <button className={mode === "all" ? "active" : ""} onClick={() => setMode("all")}>Aktiv + zuletzt abgeschlossen</button>
          </div>

          <section className="trace-list">
            {traces.length === 0 ? <div className="empty">Keine Traces in dieser Auswahl.</div> : traces.map((trace) => (
              <article className={`trace-card ${trace.blocked ? "blocked" : ""}`} key={trace.key}>
                <div className="trace-card-head">
                  <div>
                    <span className="eyebrow">{trace.root.type}</span>
                    <h2>{trace.root.external_id || trace.root.repository || trace.root.id}</h2>
                    <p>{trace.root.source_project || "?"} <span>→</span> {trace.root.target_project || "?"}</p>
                  </div>
                  <div className="trace-head-meta">
                    <span className={`trace-status ${trace.root.status}`}>{trace.root.status}</span>
                    <span>{fmtTime(trace.latest)}</span>
                  </div>
                </div>

                <div className="trace-pipeline">
                  {trace.stages.map((stage, index) => (
                    <div className={`trace-stage ${stage.state}`} key={stage.label}>
                      <div className="stage-node">{stage.state === "done" ? "✓" : stage.state === "blocked" ? "!" : stage.state === "skipped" ? "–" : index + 1}</div>
                      <div className="stage-copy"><b>{stage.label}</b><span>{stage.detail}</span></div>
                      {index < trace.stages.length - 1 && <i className="stage-line" />}
                    </div>
                  ))}
                </div>

                {(trace.root.pr_url || trace.blocked) && (
                  <div className="trace-footer">
                    {trace.root.pr_url && <a href={trace.root.pr_url} target="_blank" rel="noreferrer">Pull Request öffnen ↗</a>}
                    {trace.tasks.find((t) => t.blocked_reason)?.blocked_reason && <span className="trace-blocker">{trace.tasks.find((t) => t.blocked_reason)!.blocked_reason}</span>}
                  </div>
                )}
              </article>
            ))}
          </section>
        </>
      )}

      {!data && <div className="empty">Control-Plane-Traces werden geladen…</div>}
    </main>
  );
}
