import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const revalidate = 0;
export const runtime = "nodejs";

const API = "https://api.github.com";
const REGISTRY_REPO = process.env.REGISTRY_REPO || "thomaspeterkueper/kueper-ecosystem";
const REGISTRY_PATH = "registry/projects.json";
const PRODUCT_REGISTRY_PATH = "registry/products.json";

type Json = any;

async function gh(path: string, token: string): Promise<Response> {
  return fetch(API + path, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
    },
    cache: "no-store",
  });
}

async function ghJson(path: string, token: string): Promise<{ status: number; data: Json }> {
  const res = await gh(path, token);
  if (!res.ok) return { status: res.status, data: null };
  return { status: res.status, data: await res.json() };
}

async function pathExists(repo: string, branch: string, p: string, token: string): Promise<boolean> {
  const res = await gh(`/repos/${repo}/contents/${p}?ref=${branch}`, token);
  return res.status === 200;
}

function decode(b64: string): string {
  return Buffer.from(b64, "base64").toString("utf-8");
}

function parseFrontmatter(text: string): Record<string, any> {
  if (!text.startsWith("---")) return {};
  const end = text.indexOf("\n---", 3);
  if (end === -1) return {};
  const block = text.slice(3, end);
  const fm: Record<string, any> = {};
  for (const raw of block.split("\n")) {
    const line = raw.trim();
    if (!line || !line.includes(":")) continue;
    const idx = line.indexOf(":");
    const key = line.slice(0, idx).trim();
    let val: any = line.slice(idx + 1).trim();
    if (val.startsWith("[") && val.endsWith("]")) {
      val = val.slice(1, -1).split(",").map((s: string) => s.trim()).filter(Boolean);
    }
    fm[key] = val;
  }
  return fm;
}

async function resolveVersion(repo: string, branch: string, vs: Json, token: string): Promise<string | null> {
  if (!vs?.candidates) return null;
  for (const c of vs.candidates) {
    const r = await ghJson(`/repos/${repo}/contents/${c.path}?ref=${branch}`, token);
    if (r.status === 200 && r.data?.content) {
      const raw = decode(r.data.content);
      if (c.type === "package-json") {
        try {
          const j = JSON.parse(raw);
          const ptr = String(c.json_pointer || "/version").split("/").filter(Boolean);
          let cur: any = j;
          for (const k of ptr) cur = cur?.[k];
          if (cur != null) return String(cur);
        } catch {
          // ignore malformed candidate and continue
        }
      } else if (c.type === "text") {
        const t = raw.trim();
        if (t) return t.split("\n")[0].trim();
      }
    }
  }
  return null;
}

const ORDER: Record<string, number> = { ok: 0, not_applicable: 0, unknown: 1, warning: 2, error: 3 };

function overall(states: string[]): "healthy" | "degraded" | "critical" | "unknown" {
  if (states.some((s) => s === "error")) return "critical";
  if (states.some((s) => s === "unknown")) return states.some((s) => s === "warning") ? "degraded" : "unknown";
  if (states.some((s) => s === "warning")) return "degraded";
  return "healthy";
}

async function collectProject(p: Json, ids: Set<string>, token: string) {
  const repo: string = p.repository;
  const checks: Record<string, { state: string; detail: any }> = {};
  const tasks: any[] = [];
  const { status, data } = await ghJson(`/repos/${repo}`, token);

  if (status !== 200) {
    return {
      id: p.id, name: p.name, repository: repo, repository_url: `https://github.com/${repo}`,
      production_url: p.production_url || null, role: p.role, integrations: p.integrations || [],
      overall: "critical" as const, branch: null, version: null, last_push: null, open_tasks: 0, open_prs: null,
      checks: { repository_reachable: { state: "error", detail: `HTTP ${status}` } }, tasks,
    };
  }

  const branch: string = data.default_branch;
  checks.repository_reachable = { state: "ok", detail: branch };

  const prs = await ghJson(`/repos/${repo}/pulls?state=open&per_page=100`, token);
  const openPrs = Array.isArray(prs.data) ? prs.data.length : null;
  checks.open_pull_requests = { state: prs.status === 200 ? "ok" : "unknown", detail: openPrs };

  const reqPaths: string[] = p.governance?.required_paths || [];
  const missing: string[] = [];
  for (const rp of reqPaths) if (!(await pathExists(repo, branch, rp, token))) missing.push(rp);
  checks.governance_required_paths = { state: missing.length ? "error" : "ok", detail: { missing, checked: reqPaths.length } };

  const listing = await ghJson(`/repos/${repo}/contents/external-tasks/open?ref=${branch}`, token);
  let openCount = 0;
  if (listing.status === 200 && Array.isArray(listing.data)) {
    const mdFiles = listing.data.filter((f: Json) => f.name.endsWith(".md"));
    openCount = mdFiles.length;
    const parsed = await Promise.all(mdFiles.map(async (f: Json) => {
      let fm: Record<string, any> = {};
      try {
        const c = await ghJson(`/repos/${repo}/contents/${f.path}?ref=${branch}`, token);
        if (c.status === 200 && c.data?.content) fm = parseFrontmatter(decode(c.data.content));
      } catch {
        // fall back to filename
      }
      return {
        project_id: p.id,
        project_name: p.name,
        repository: repo,
        file: f.name,
        html_url: f.html_url,
        canonical: /^EXT-[A-Z]+-[A-Z]+-\d{8}-\d{3}\.md$/.test(f.name),
        id: fm.id || f.name.replace(/\.md$/, ""),
        title: fm.title || null,
        source: fm.source || null,
        target: fm.target || null,
        priority: fm.priority || null,
        created: fm.created || null,
      };
    }));
    tasks.push(...parsed);
  }
  checks.external_tasks_open = { state: openCount ? "warning" : "ok", detail: { count: openCount } };

  const integ = (p.integrations || []).map((it: Json) => ({
    target: it.target,
    required: it.required,
    state: ids.has(it.target) ? "ok" : it.required ? "error" : "warning",
  }));
  checks.integrations = {
    state: integ.length ? integ.map((r: Json) => r.state).sort((a: string, b: string) => ORDER[b] - ORDER[a])[0] : "not_applicable",
    detail: integ,
  };

  return {
    id: p.id,
    name: p.name,
    repository: repo,
    repository_url: data.html_url,
    production_url: p.production_url || null,
    role: p.role,
    integrations: p.integrations || [],
    overall: overall(Object.values(checks).map((c) => c.state)),
    branch,
    version: await resolveVersion(repo, branch, p.version_source, token),
    last_push: data.pushed_at,
    open_tasks: openCount,
    open_prs: openPrs,
    checks,
    tasks,
  };
}

async function collectProduct(p: Json, token: string) {
  const { status, data } = await ghJson(`/repos/${p.repository}`, token);
  if (status !== 200) {
    return { ...p, repository_url: `https://github.com/${p.repository}`, overall: "critical", branch: null, last_push: null, open_prs: null };
  }
  const prs = await ghJson(`/repos/${p.repository}/pulls?state=open&per_page=100`, token);
  return {
    ...p,
    repository_url: data.html_url,
    overall: "healthy",
    branch: data.default_branch,
    last_push: data.pushed_at,
    open_prs: Array.isArray(prs.data) ? prs.data.length : null,
  };
}

async function loadRegistry(path: string, token: string): Promise<Json | null> {
  const reg = await ghJson(`/repos/${REGISTRY_REPO}/contents/${path}`, token);
  if (reg.status !== 200 || !reg.data?.content) return null;
  try {
    return JSON.parse(decode(reg.data.content));
  } catch {
    return null;
  }
}

export async function GET() {
  const token = process.env.GH_TOKEN;
  if (!token) return NextResponse.json({ error: "GH_TOKEN ist nicht gesetzt." }, { status: 500 });

  const registry = await loadRegistry(REGISTRY_PATH, token);
  if (!registry) return NextResponse.json({ error: `Registry konnte nicht geladen werden (${REGISTRY_REPO}/${REGISTRY_PATH}).` }, { status: 502 });

  const projectsIn: Json[] = (registry.projects || []).filter((p: Json) => p.enabled !== false);
  const ids = new Set<string>(projectsIn.map((p) => p.id));
  const projects = await Promise.all(projectsIn.map((p) => collectProject(p, ids, token)));

  const productRegistry = await loadRegistry(PRODUCT_REGISTRY_PATH, token);
  const productsIn: Json[] = (productRegistry?.products || []).filter((p: Json) => p.enabled !== false);
  const products = await Promise.all(productsIn.map((p) => collectProduct(p, token)));

  const allTasks = projects.flatMap((p) => p.tasks);
  const counts: Record<string, number> = {};
  for (const p of projects) counts[p.overall] = (counts[p.overall] || 0) + 1;

  return NextResponse.json({
    generated_at: new Date().toISOString(),
    registry_repo: REGISTRY_REPO,
    summary: {
      projects: projects.length,
      products: products.length,
      overall_counts: counts,
      open_external_tasks_total: allTasks.length,
      open_pull_requests_total: projects.reduce((sum, p) => sum + (p.open_prs || 0), 0),
    },
    projects: projects.map(({ tasks, ...rest }) => rest),
    products,
    tasks: allTasks,
  });
}
