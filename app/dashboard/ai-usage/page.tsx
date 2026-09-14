"use client";

import { useEffect, useMemo, useState } from "react";

type UsageSource = { source_system:string; planned:number; executed:number; completed:number; failed:number; blocked:number; skipped:number; estimated_cost_usd:number|string; actual_cost_usd:number|string };
type UsageItem = { id:string; created_at:string; source_system:string; trigger_type:string; reason:string; provider_requested:string; model_requested:string; status:string; skip_reason:string|null; repository:string|null; pr_number:number|null; research_id:string|null; task_id:string|null; workflow_run_id:number|null; commit_sha:string|null; is_retry:boolean; input_tokens:number; output_tokens:number; estimated_cost_usd:number|string; actual_cost_usd:number|string };
type AIUsage = { planned:number; executed:number; completed:number; failed:number; blocked:number; skipped:number; deduped:number; input_tokens:number; output_tokens:number; estimated_cost_usd:number|string; actual_cost_usd:number|string; by_source:UsageSource[]; latest:UsageItem[] };

function money(value:number|string|undefined) { const n=Number(value||0); return `$${n.toFixed(n<1?3:2)}`; }
function when(value:string) { return new Date(value).toLocaleString("de-DE", { dateStyle:"short", timeStyle:"medium" }); }

export default function AIUsagePage() {
  const [usage,setUsage]=useState<AIUsage|null>(null);
  const [reason,setReason]=useState<string|null>(null);
  const [loading,setLoading]=useState(true);

  useEffect(()=>{ fetch("/api/operations",{cache:"no-store"}).then(r=>r.json()).then(j=>{setUsage(j.ai_usage||null);setReason(j.ai_usage_reason||null)}).catch(e=>setReason(String(e))).finally(()=>setLoading(false)); },[]);
  const totalTokens=useMemo(()=>Number(usage?.input_tokens||0)+Number(usage?.output_tokens||0),[usage]);

  return <main className="ledger-wrap">
    <header className="ledger-head"><div><span className="eyebrow">KUEPER · Control Plane</span><h1>AI Usage Ledger</h1><p>Warum ein Modell aufgerufen werden sollte, was tatsächlich ausgeführt wurde und welcher Verbrauch dabei entstanden ist.</p></div><a href="/dashboard">← Control Room</a></header>

    {loading && <div className="empty">Ledger wird geladen…</div>}
    {!loading && !usage && <div className="empty">Ledger noch nicht verfügbar. {reason||"Die Supabase-Migration muss zuerst aktiv sein."}</div>}
    {usage && <>
      <section className="metrics">
        <article><span>Geplant</span><b>{usage.planned}</b><small>{usage.executed} tatsächlich gestartet</small></article>
        <article><span>Abgeschlossen</span><b>{usage.completed}</b><small>{usage.failed} fehlgeschlagen · {usage.blocked} blockiert</small></article>
        <article><span>Tokens</span><b>{totalTokens.toLocaleString("de-DE")}</b><small>{Number(usage.input_tokens||0).toLocaleString("de-DE")} in · {Number(usage.output_tokens||0).toLocaleString("de-DE")} out</small></article>
        <article><span>Kosten heute</span><b>{money(usage.actual_cost_usd)}</b><small>{money(usage.estimated_cost_usd)} geschätzt · {usage.deduped} dedupliziert</small></article>
      </section>

      <section className="panel"><div className="panel-head"><div><span className="eyebrow">Attribution</span><h2>Verbrauch nach System</h2></div></div>
        <div className="source-grid">{usage.by_source.length===0?<div className="empty">Noch keine Usage-Intents heute.</div>:usage.by_source.map(s=><article key={s.source_system}><strong>{s.source_system}</strong><span>{s.executed}/{s.planned} Calls</span><span>{s.completed} fertig · {s.blocked} blockiert · {s.skipped} übersprungen</span><b>{money(s.actual_cost_usd)}</b><small>{money(s.estimated_cost_usd)} geschätzt</small></article>)}</div>
      </section>

      <section className="panel"><div className="panel-head"><div><span className="eyebrow">Audit trail</span><h2>Letzte Entscheidungen</h2></div><span>{usage.latest.length} Einträge</span></div>
        <div className="table-wrap"><table><thead><tr><th>Zeit</th><th>System</th><th>Grund</th><th>Modell</th><th>Status</th><th>Referenz</th><th>Tokens</th><th>Kosten</th></tr></thead><tbody>{usage.latest.map(row=><tr key={row.id}><td>{when(row.created_at)}</td><td>{row.source_system}<small>{row.trigger_type}</small></td><td className="reason">{row.reason}{row.skip_reason&&<small>{row.skip_reason}</small>}</td><td>{row.provider_requested}<small>{row.model_requested}</small></td><td><span className={`status ${row.status}`}>{row.status}</span></td><td>{row.research_id||row.task_id||(row.pr_number?`PR #${row.pr_number}`):"—"}<small>{row.repository||""}</small></td><td>{(Number(row.input_tokens||0)+Number(row.output_tokens||0)).toLocaleString("de-DE")}</td><td>{money(row.actual_cost_usd)}<small>{money(row.estimated_cost_usd)} est.</small></td></tr>)}</tbody></table></div>
      </section>
    </>}

    <style jsx>{`
      .ledger-wrap{max-width:1500px;margin:0 auto;padding:28px 30px 60px;color:#e5e7eb}.ledger-head{display:flex;justify-content:space-between;gap:30px;align-items:flex-start;margin-bottom:26px}.ledger-head h1{font-size:32px;margin:5px 0 8px}.ledger-head p{color:#94a3b8;max-width:760px;margin:0;line-height:1.55}.ledger-head a{color:#cbd5e1;text-decoration:none;border-bottom:1px solid #475569;padding-bottom:3px}.eyebrow{font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:#7c8aa0}.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:18px}.metrics article,.panel{border:1px solid rgba(148,163,184,.16);background:rgba(15,23,42,.58);border-radius:14px}.metrics article{padding:16px}.metrics span,.metrics small{display:block;color:#7c8aa0;font-size:11px}.metrics b{display:block;font:25px ui-monospace,SFMono-Regular,Menlo,monospace;margin:12px 0 7px;color:#f8fafc}.panel{padding:18px;margin-top:16px}.panel-head{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:14px}.panel-head h2{margin:4px 0 0;font-size:18px}.panel-head>span{font-size:11px;color:#7c8aa0}.source-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}.source-grid article{padding:13px;border-radius:10px;background:rgba(2,6,23,.34);border:1px solid rgba(148,163,184,.1)}.source-grid strong,.source-grid span,.source-grid small,.source-grid b{display:block}.source-grid strong{font-size:12px;margin-bottom:10px}.source-grid span,.source-grid small{font-size:10px;color:#7c8aa0;margin-top:4px}.source-grid b{font:18px ui-monospace,SFMono-Regular,Menlo,monospace;margin-top:12px}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;font-size:11px}th{text-align:left;color:#7c8aa0;font-weight:500;padding:9px;border-bottom:1px solid rgba(148,163,184,.16)}td{vertical-align:top;padding:10px 9px;border-bottom:1px solid rgba(148,163,184,.08);color:#cbd5e1}td small{display:block;color:#64748b;margin-top:4px;max-width:220px}.reason{min-width:280px;max-width:430px}.status{font:10px ui-monospace,SFMono-Regular,Menlo,monospace;padding:3px 6px;border:1px solid #475569;border-radius:999px}.status.completed{color:#86efac;border-color:#166534}.status.failed{color:#fca5a5;border-color:#7f1d1d}.status.blocked,.status.skipped{color:#fcd34d;border-color:#92400e}.empty{padding:22px;color:#94a3b8}@media(max-width:1000px){.metrics,.source-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:640px){.ledger-wrap{padding:20px 14px 40px}.ledger-head{flex-direction:column}.metrics,.source-grid{grid-template-columns:1fr}}
    `}</style>
  </main>;
}
