import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const revalidate = 0;
export const runtime = "nodejs";

const DEFAULT_SUPABASE_URL = "https://ehuoafluxkmizvatmyzt.supabase.co";

function config() {
  const url = process.env.SUPABASE_URL || DEFAULT_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SECRET_KEY;
  return { url: url.replace(/\/$/, ""), key: key || null };
}

async function rpc(url: string, key: string, name: string) {
  const response = await fetch(`${url}/rest/v1/rpc/${name}`, {
    method: "POST",
    headers: { apikey: key, Authorization: `Bearer ${key}`, "Content-Type": "application/json", Accept: "application/json" },
    body: "{}",
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`${name} RPC ${response.status}`);
  return response.json();
}

export async function GET() {
  const { url, key } = config();
  if (!key) {
    return NextResponse.json({ available: false, generated_at: new Date().toISOString(), reason: "Supabase server credentials are not configured for this deployment.", workers: [], queue: {}, providers: {}, llm_budget: {}, ai_usage: null });
  }

  try {
    const payload = await rpc(url, key, "kueper_control_room_operations");
    let aiUsage: any = null;
    let aiUsageReason: string | null = null;
    try {
      aiUsage = await rpc(url, key, "kueper_ai_usage_dashboard");
    } catch (error: any) {
      // The operations view remains usable during rollout or migration lag.
      aiUsageReason = error?.message || "AI usage ledger unavailable.";
    }

    return NextResponse.json({
      available: true,
      generated_at: new Date().toISOString(),
      workers: Array.isArray(payload?.workers) ? payload.workers : [],
      queue: payload?.queue && typeof payload.queue === "object" ? payload.queue : {},
      providers: payload?.providers && typeof payload.providers === "object" ? payload.providers : {},
      llm_budget: payload?.llm_budget && typeof payload.llm_budget === "object" ? payload.llm_budget : {},
      blocked_tasks: Number(payload?.blocked_tasks || 0),
      ai_usage: aiUsage && typeof aiUsage === "object" ? aiUsage : null,
      ai_usage_reason: aiUsageReason,
    });
  } catch (error: any) {
    return NextResponse.json({ available: false, generated_at: new Date().toISOString(), reason: error?.message || "Control-plane telemetry unavailable.", workers: [], queue: {}, providers: {}, llm_budget: {}, ai_usage: null });
  }
}
