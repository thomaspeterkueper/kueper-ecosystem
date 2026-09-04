import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const revalidate = 0;
export const runtime = "nodejs";

const DEFAULT_SUPABASE_URL = "https://ehuoafluxkmizvatmyzt.supabase.co";

export async function GET() {
  const url = (process.env.SUPABASE_URL || DEFAULT_SUPABASE_URL).replace(/\/$/, "");
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SECRET_KEY;

  if (!key) {
    return NextResponse.json({
      available: false,
      generated_at: new Date().toISOString(),
      reason: "Control-Plane-Zugriff ist im Deployment noch nicht konfiguriert.",
      tasks: [],
    });
  }

  try {
    const response = await fetch(`${url}/rest/v1/rpc/kueper_control_room_traces`, {
      method: "POST",
      headers: {
        apikey: key,
        Authorization: `Bearer ${key}`,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ p_limit: 120 }),
      cache: "no-store",
    });

    if (!response.ok) {
      return NextResponse.json({
        available: false,
        generated_at: new Date().toISOString(),
        reason: `Control-Plane RPC nicht verfügbar (HTTP ${response.status}).`,
        tasks: [],
      });
    }

    const tasks = await response.json();
    return NextResponse.json({
      available: true,
      generated_at: new Date().toISOString(),
      tasks: Array.isArray(tasks) ? tasks : [],
    });
  } catch (error) {
    return NextResponse.json({
      available: false,
      generated_at: new Date().toISOString(),
      reason: error instanceof Error ? error.message : "Control-Plane-Abfrage fehlgeschlagen.",
      tasks: [],
    });
  }
}
