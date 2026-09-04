import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const revalidate = 0;
export const runtime = "nodejs";

const DEFAULT_SUPABASE_URL = "https://ehuoafluxkmizvatmyzt.supabase.co";

const SELECT = [
  "id",
  "external_id",
  "type",
  "source_project",
  "target_project",
  "status",
  "priority",
  "repository",
  "branch",
  "pr_url",
  "parent_task_id",
  "root_task_id",
  "created_at",
  "claimed_at",
  "started_at",
  "completed_at",
  "updated_at",
  "blocked_reason",
  "attempt_count",
].join(",");

export async function GET() {
  const url = process.env.SUPABASE_URL || DEFAULT_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SECRET_KEY;

  if (!key) {
    return NextResponse.json({
      available: false,
      generated_at: new Date().toISOString(),
      reason: "Control-Plane-Zugriff ist im Deployment noch nicht konfiguriert.",
      tasks: [],
    });
  }

  const endpoint = new URL(`${url}/rest/v1/tasks`);
  endpoint.searchParams.set("select", SELECT);
  endpoint.searchParams.set("order", "updated_at.desc");
  endpoint.searchParams.set("limit", "120");

  try {
    const response = await fetch(endpoint, {
      headers: {
        apikey: key,
        Authorization: `Bearer ${key}`,
        "Accept-Profile": "ecosystem",
      },
      cache: "no-store",
    });

    if (!response.ok) {
      const detail = (await response.text()).slice(0, 300);
      return NextResponse.json({
        available: false,
        generated_at: new Date().toISOString(),
        reason: `Control-Plane Data API nicht verfügbar (HTTP ${response.status}).`,
        detail,
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
