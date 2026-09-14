"use client";

import { useEffect, useState } from "react";
import styles from "./ai-usage.module.css";

type UsageSource = {
  source_system: string;
  planned: number;
  executed: number;
  completed: number;
  failed: number;
  blocked: number;
  skipped: number;
  unreconciled_calls: number;
  estimated_cost_usd: number | string | null;
  actual_cost_usd: number | string | null;
};

type UsageItem = {
  id: string;
  created_at: string;
  source_system: string;
  trigger_type: string;
  reason: string;
  provider_requested: string;
  model_requested: string;
  status: string;
  skip_reason: string | null;
  repository: string | null;
  pr_number: number | null;
  research_id: string | null;
  task_id: string | null;
  semantic_key: string;
  attempt_no: number;
  retry_mode: string;
  retry_reason: string | null;
  retry_of_intent_id: string | null;
  failure_class: string | null;
  cost_reconciled: boolean;
  input_tokens: number;
  output_tokens: number;
  estimated_cost_usd: number | string | null;
  actual_cost_usd: number | string | null;
};

type AIUsage = {
  planned: number;
  executed: number;
  completed: number;
  failed: number;
  blocked: number;
  skipped: number;
  deduped: number;
  unreconciled_calls: number;
  input_tokens: number;
  output_tokens: number;
  estimated_cost_usd: number | string | null;
  actual_cost_usd: number | string | null;
  by_source: UsageSource[];
  latest: UsageItem[];
};

function money(value: number | string | null | undefined) {
  if (value === null || value === undefined) return "nicht reconciled";
  const amount = Number(value);
  return `$${amount.toFixed(amount < 1 ? 3 : 2)}`;
}

function timestamp(value: string) {
  return new Date(value).toLocaleString("de-DE", {
    dateStyle: "short",
    timeStyle: "medium",
  });
}

export default function AIUsagePage() {
  const [usage, setUsage] = useState<AIUsage | null>(null);
  const [reason, setReason] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/operations", { cache: "no-store" })
      .then((response) => response.json())
      .then((payload) => {
        setUsage(payload.ai_usage || null);
        setReason(payload.ai_usage_reason || null);
      })
      .catch((error) => setReason(String(error)))
      .finally(() => setLoading(false));
  }, []);

  const totalTokens = Number(usage?.input_tokens || 0) + Number(usage?.output_tokens || 0);

  return (
    <main className={styles.wrap}>
      <header className={styles.header}>
        <div>
          <span className={styles.eyebrow}>KUEPER · Control Plane</span>
          <h1>AI Usage Ledger</h1>
          <p>Semantische Arbeit, Ausführungsversuche, Retry-Gründe und tatsächlich bekannte Providerkosten.</p>
        </div>
        <a href="/dashboard">← Control Room</a>
      </header>

      {loading && <div className={styles.empty}>Ledger wird geladen…</div>}
      {!loading && !usage && (
        <div className={styles.empty}>Ledger noch nicht verfügbar. {reason || "Die Supabase-Migration muss zuerst aktiv sein."}</div>
      )}

      {usage && (
        <>
          <section className={styles.metrics}>
            <article><span>Geplant</span><b>{usage.planned}</b><small>{usage.executed} tatsächlich gestartet</small></article>
            <article><span>Abgeschlossen</span><b>{usage.completed}</b><small>{usage.failed} fehlgeschlagen · {usage.blocked} blockiert</small></article>
            <article><span>Tokens</span><b>{totalTokens.toLocaleString("de-DE")}</b><small>{Number(usage.input_tokens || 0).toLocaleString("de-DE")} in · {Number(usage.output_tokens || 0).toLocaleString("de-DE")} out</small></article>
            <article><span>Kosten heute</span><b>{money(usage.actual_cost_usd)}</b><small>{usage.unreconciled_calls} Calls noch nicht reconciled · {usage.deduped} dedupliziert</small></article>
          </section>

          <section className={styles.panel}>
            <div className={styles.panelHead}><div><span className={styles.eyebrow}>Attribution</span><h2>Verbrauch nach System</h2></div></div>
            <div className={styles.sourceGrid}>
              {usage.by_source.length === 0 ? <div className={styles.empty}>Noch keine Usage-Intents heute.</div> : usage.by_source.map((source) => (
                <article key={source.source_system}>
                  <strong>{source.source_system}</strong>
                  <span>{source.executed}/{source.planned} Calls</span>
                  <span>{source.completed} fertig · {source.blocked} blockiert · {source.skipped} übersprungen</span>
                  <b>{money(source.actual_cost_usd)}</b>
                  <small>{source.unreconciled_calls} unreconciled · {money(source.estimated_cost_usd)} geschätzt</small>
                </article>
              ))}
            </div>
          </section>

          <section className={styles.panel}>
            <div className={styles.panelHead}><div><span className={styles.eyebrow}>Audit trail</span><h2>Letzte Entscheidungen</h2></div><span>{usage.latest.length} Einträge</span></div>
            <div className={styles.tableWrap}>
              <table>
                <thead><tr><th>Zeit</th><th>System</th><th>Grund</th><th>Modell</th><th>Status</th><th>Versuch</th><th>Referenz</th><th>Tokens</th><th>Kosten</th></tr></thead>
                <tbody>
                  {usage.latest.map((row) => (
                    <tr key={row.id}>
                      <td>{timestamp(row.created_at)}</td>
                      <td>{row.source_system}<small>{row.trigger_type}</small></td>
                      <td className={styles.reason}>{row.reason}{row.skip_reason && <small>{row.skip_reason}</small>}{row.failure_class && <small>Fehlerklasse: {row.failure_class}</small>}</td>
                      <td>{row.provider_requested}<small>{row.model_requested}</small></td>
                      <td><span className={`${styles.status} ${styles[row.status] || ""}`}>{row.status}</span></td>
                      <td>#{row.attempt_no}<small>{row.retry_mode !== "none" ? `${row.retry_mode}${row.retry_reason ? ` · ${row.retry_reason}` : ""}` : "Erstversuch"}</small></td>
                      <td>{row.research_id || row.task_id || (row.pr_number ? `PR #${row.pr_number}` : "—")}<small>{row.repository || row.semantic_key}</small></td>
                      <td>{(Number(row.input_tokens || 0) + Number(row.output_tokens || 0)).toLocaleString("de-DE")}</td>
                      <td>{row.cost_reconciled ? money(row.actual_cost_usd) : "nicht reconciled"}<small>{money(row.estimated_cost_usd)} est.</small></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </main>
  );
}
