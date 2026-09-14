"use client";

import { useEffect, useMemo, useState } from "react";
import styles from "./operations-strip.module.css";

type Worker = { id:string; worker_name:string; source:string|null; status:string; dispatch_requested_at:string|null; started_at:string|null; finished_at:string|null; github_run_id:number|null; last_error:string|null; created_at:string; last_success_at:string|null; last_failure_at:string|null };
type Budget = { enabled:boolean; calls:number; max_daily_calls:number; pro_calls:number; max_daily_pro_calls:number; resets_at:string|null };
type UsageSource = { source_system:string; planned:number; executed:number; completed:number; failed:number; blocked:number; skipped:number; estimated_cost_usd:number|string; actual_cost_usd:number|string };
type AIUsage = { planned:number; executed:number; completed:number; failed:number; blocked:number; skipped:number; deduped:number; input_tokens:number; output_tokens:number; estimated_cost_usd:number|string; actual_cost_usd:number|string; by_source:UsageSource[]; latest:any[] };
type Operations = { available:boolean; generated_at:string; reason?:string; workers:Worker[]; queue:Record<string,number>; providers:Record<string,string>; llm_budget?:Record<string,Budget>; blocked_tasks?:number; ai_usage?:AIUsage|null; ai_usage_reason?:string|null };

function age(iso:string|null) { if(!iso)return "—"; const mins=Math.max(0,Math.floor((Date.now()-new Date(iso).getTime())/60000)); if(mins<1)return "jetzt"; if(mins<60)return `${mins} min`; const hours=Math.floor(mins/60); return hours<24?`${hours} h`:`${Math.floor(hours/24)} d`; }
function tone(status:string) { if(["succeeded","success","available"].includes(status))return styles.ok; if(["failed","error","critical"].includes(status))return styles.error; if(["paused","blocked","warning"].includes(status))return styles.warning; return styles.neutral; }
function label(worker:string) { if(worker==="agent-worker-v7")return "Agent Worker"; if(worker==="pr-review-agent")return "PR Reviewer"; return worker; }
function attemptLabel(worker:Worker) { return worker.status==="skipped"&&worker.last_error==="recent execution cooldown"?"skipped · cooldown":worker.status; }
function usd(value:number|string|undefined) { const n=Number(value||0); return `$${n.toFixed(n<1?3:2)}`; }

export default function OperationsStrip() {
  const [data,setData]=useState<Operations|null>(null);
  useEffect(()=>{ let cancelled=false; fetch("/api/operations",{cache:"no-store"}).then(res=>res.json()).then(json=>{if(!cancelled)setData(json)}).catch(()=>{if(!cancelled)setData(null)}); return()=>{cancelled=true}; },[]);
  const workerMap=useMemo(()=>new Map((data?.workers||[]).map(worker=>[worker.worker_name,worker])),[data]);
  const agent=workerMap.get("agent-worker-v7"); const reviewer=workerMap.get("pr-review-agent");
  const waiting=(data?.queue?.pending||0)+(data?.queue?.review_pending||0); const deepseek=data?.providers?.deepseek||"unknown"; const budget=data?.llm_budget?.deepseek; const usage=data?.ai_usage;
  const topSource=usage?.by_source?.[0];

  if(!data)return <section className={styles.shell}><span className={styles.eyebrow}>Operations</span><div className={styles.loading}>Control-Plane-Telemetrie wird geladen…</div></section>;
  if(!data.available)return <section className={styles.shell}><div className={styles.head}><span className={styles.eyebrow}>Operations</span><span className={`${styles.badge} ${styles.neutral}`}>Telemetry fallback</span></div><p className={styles.reason}>{data.reason||"Live-Control-Plane-Daten sind in diesem Deployment nicht verfügbar."}</p></section>;
  const cards=[agent,reviewer].filter(Boolean) as Worker[];

  return <section className={styles.shell}>
    <div className={styles.head}><div><span className={styles.eyebrow}>Operations</span><h2>Autonomous Control Plane</h2></div><span className={`${styles.badge} ${tone(deepseek)}`}>DeepSeek {deepseek}</span></div>
    <div className={styles.grid}>
      {cards.map(worker=><article className={styles.card} key={worker.worker_name}><div className={styles.cardTop}><span>{label(worker.worker_name)}</span><span className={`${styles.state} ${tone(worker.status)}`}>{attemptLabel(worker)}</span></div><div className={styles.value}>{age(worker.last_success_at||worker.finished_at||worker.started_at||worker.created_at)}</div><div className={styles.caption}>seit letztem Erfolg · letzter Versuch {age(worker.finished_at||worker.started_at||worker.created_at)}</div>{worker.last_error&&worker.status!=="skipped"&&<div className={styles.errorText}>{worker.last_error}</div>}</article>)}
      <article className={styles.card}><div className={styles.cardTop}><span>Queue</span><span className={`${styles.state} ${waiting?styles.warning:styles.ok}`}>{waiting?"work pending":"clear"}</span></div><div className={styles.value}>{waiting}</div><div className={styles.caption}>{data.queue.review_pending||0} Review · {data.queue.pending||0} Pending</div></article>
      <article className={styles.card}><div className={styles.cardTop}><span>DeepSeek Budget</span><span className={`${styles.state} ${budget&&budget.calls>=budget.max_daily_calls?styles.warning:styles.ok}`}>{budget?.enabled===false?"disabled":"UTC daily"}</span></div><div className={styles.value}>{budget?`${budget.calls}/${budget.max_daily_calls}`:"—"}</div><div className={styles.caption}>{budget?`Pro ${budget.pro_calls}/${budget.max_daily_pro_calls} · Reset ${budget.resets_at?new Date(budget.resets_at).toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit"}):"—"}`:"keine Budgettelemetrie"}</div></article>
      <article className={styles.card}><div className={styles.cardTop}><span>AI Usage heute</span><span className={`${styles.state} ${usage&&usage.failed?styles.warning:styles.ok}`}>{usage?`${usage.executed}/${usage.planned} ausgeführt`:"ledger"}</span></div><div className={styles.value}>{usage?usd(usage.actual_cost_usd):"—"}</div><div className={styles.caption}>{usage?`${usage.completed} fertig · ${usage.blocked} blockiert · ${usage.skipped} übersprungen · ${usage.deduped} dedupliziert`:data.ai_usage_reason||"Ledger wird nach DB-Migration verfügbar"}</div><a className={styles.ledgerLink} href="/dashboard/ai-usage">Ledger öffnen →</a></article>
      <article className={styles.card}><div className={styles.cardTop}><span>Top AI-Verbraucher</span><span className={`${styles.state} ${styles.neutral}`}>heute</span></div><div className={styles.value}>{topSource?.source_system||"—"}</div><div className={styles.caption}>{topSource?`${topSource.executed}/${topSource.planned} Calls · ${usd(topSource.actual_cost_usd)} tatsächlich · ${usd(topSource.estimated_cost_usd)} geschätzt`:"noch keine Nutzungsdaten"}</div></article>
      <article className={styles.card}><div className={styles.cardTop}><span>Blocker</span><span className={`${styles.state} ${(data.blocked_tasks||0)?styles.warning:styles.ok}`}>{(data.blocked_tasks||0)?"attention":"clear"}</span></div><div className={styles.value}>{data.blocked_tasks||0}</div><div className={styles.caption}>aktive Tasks mit explizitem Blocker</div></article>
    </div>
  </section>;
}
