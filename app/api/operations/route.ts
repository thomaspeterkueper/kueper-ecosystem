import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const revalidate = 0;
export const runtime = "nodejs";

type SchedulerRun = {
  id: string;
  worker_name: string;
  source: string | null;
  status: string;
  dispatch_requested_at: string | null;
  started_at: string | null;
  finished_at: string | null;
  github_run_id: number | null;
  last_error: string | null;
  created_at: string;
};

type TaskRow = {
  status: string;
  type: string | null;
  blocked_reason: string | null;
};

function config() {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SECRET_KEY;
  return { url: url?.replace(/\/$/, "") || null, key: key || null };
}

async function rest(path: string, schema = "ecosystem") {
  const { url, key } = config();
  if (!url || !key) return null;
  const res = await fetch(`${url}/rest/v1/${path}`, {
    headers: {
      apikey: key,
      Authorization: `Bearer ${key}`,
      Accept: "application/json",
      "Accept-Profile": schema,
    },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Supabase REST ${res.status}`);
  return res.json();
}

async function providerAvailable(provider: string) {
  const { url, key } = config();
  if (!url || !key) return null;
  const res = await fetch(`${url}/rest/v1/rpc/kueper_provider_available`, {
    method: "POST",
    headers: {
      apikey: key,
      Authorization: `Bearer ${key}`,
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({ p_provider: provider }),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Provider health RPC ${res.status}`);
  return Boolean(await res.json());
}

function latestByWorker(runs: SchedulerRun[]) {
  const latest = new Map<string, SchedulerRun>();
  for (const run of runs) if (!latest.has(run.worker_name)) latest.set(run.worker_name, run);
  return Array.from(latest.values());
}

function counts(rows: TaskRow[]) {
  const out: Record<string, number> = {};
  for (const row of rows) out[row.status] = (out[row.status] || 0) + 1;
  return out;
}

export async function GET() {
  const { url, key } = config();
  if (!url || !key) {
    return NextResponse.json({
      available: false,
      generated_at: new Date().toISOString(),
      reason: "Supabase server credentials are not configured for this deployment.",
      workers: [],
      queue: {},
      providers: {},
    });
  }

  try {
    const runs = (await rest(
      "scheduler_runs?select=id,worker_name,source,status,dispatch_requested_at,started_at,finished_at,github_run_id,last_error,created_at&order=created_at.desc&limit=40",
    )) as SchedulerRun[];
    const tasks = (await rest(
      "tasks?select=status,type,blocked_reason&status=in.(pending,review_pending,blocked,failed)&limit=500",
    )) as TaskRow[];
    const deepseek = await providerAvailable("deepseek");

    return NextResponse.json({
      available: true,
      generated_at: new Date().toISOString(),
      workers: latestByWorker(runs || []),
      queue: counts(tasks || []),
      providers: { deepseek: deepseek ? "available" : "paused" },
      blocked_tasks: (tasks || []).filter((task) => Boolean(task.blocked_reason)).length,
    });
  } catch (error: any) {
    return NextResponse.json({
      available: false,
      generated_at: new Date().toISOString(),
      reason: error?.message || "Control-plane telemetry unavailable.",
      workers: [],
      queue: {},
      providers: {},
    });
  }
}
