import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const revalidate = 0;
export const runtime = "nodejs";

const API = "https://api.github.com";
const REGISTRY_REPO = "thomaspeterkueper/kueper-ecosystem";
const REGISTRY_PATH = "registry/projects.json";

type Json = any;

async function github(path: string, token?: string | null): Promise<Response> {
  const headers: Record<string, string> = {
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  return fetch(API + path, { headers, cache: "no-store" });
}

async function githubJson(path: string, token?: string | null) {
  let res = await github(path, token);
  let authFallback = false;
  if (res.status === 401 && token) {
    authFallback = true;
    res = await github(path, null);
  }
  if (!res.ok) return { status: res.status, data: null, authFallback };
  return { status: res.status, data: await res.json(), authFallback };
}

function decode(content: string): string {
  return Buffer.from(content, "base64").toString("utf-8");
}

function parseFrontmatter(text: string): Record<string, string> {
  if (!text.startsWith("---")) return {};
  const end = text.indexOf("\n---", 3);
  if (end < 0) return {};
  const out: Record<string, string> = {};
  for (const raw of text.slice(3, end).split("\n")) {
    const i = raw.indexOf(":");
    if (i <= 0) continue;
    out[raw.slice(0, i).trim()] = raw.slice(i + 1).trim().replace(/^['\"]|['\"]$/g, "");
  }
  return out;
}

async function versionFor(repo: string, branch: string, source: Json, token?: string | null) {
  for (const candidate of source?.candidates || []) {
    const r = await githubJson(`/repos/${repo}/contents/${candidate.path}?ref=${branch}`, token);
    if (r.status !== 200 || !r.data?.content) continue;
    const raw = decode(r.data.content);
    if (candidate.type === "package-json") {
      try {
        const j = JSON.parse(raw);
        if (j.version) return String(j.version);
      } catch {}
    } else if (candidate.type === "text") {
      return raw.trim().split("\n")[0] || null;
    }
  }
  return null;
}

async function collectProject(p: Json, token?: string | null) {
  const repo = p.repository;
  const meta = await githubJson(`/repos/${repo}`, token);
  if (meta.status !== 200) {
    return {
      project: {
        id: p.id,
        name: p.name,
        repository: repo,
        role: p.role,
        overall: "critical",
        branch: null,
        version: null,
        last_push: null,
        open_tasks: 0,
      },
      tasks: [],
    };
  }

  const branch = meta.data.default_branch;
  const listing = await githubJson(`/repos/${repo}/contents/external-tasks/open?ref=${branch}`, token);
  const files = listing.status === 200 && Array.isArray(listing.data)
    ? listing.data.filter((f: Json) => f.name.endsWith(".md"))
    : [];

  const tasks = await Promise.all(files.map(async (f: Json) => {
    const task = await githubJson(`/repos/${repo}/contents/${f.path}?ref=${branch}`, token);
    const fm = task.status === 200 && task.data?.content ? parseFrontmatter(decode(task.data.content)) : {};
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

  return {
    project: {
      id: p.id,
      name: p.name,
      repository: repo,
      role: p.role,
      overall: tasks.length ? "degraded" : "healthy",
      branch,
      version: await versionFor(repo, branch, p.version_source, token),
      last_push: meta.data.pushed_at,
      open_tasks: tasks.length,
    },
    tasks,
  };
}

export async function GET() {
  const token = process.env.GH_TOKEN || process.env.KUEPER_BOT_TOKEN || null;
  const registryResponse = await githubJson(`/repos/${REGISTRY_REPO}/contents/${REGISTRY_PATH}`, token);

  if (registryResponse.status !== 200 || !registryResponse.data?.content) {
    return NextResponse.json(
      {
        error: `Registry konnte nicht geladen werden (${REGISTRY_REPO}/${REGISTRY_PATH}, HTTP ${registryResponse.status}).`,
      },
      { status: 502 }
    );
  }

  let registry: Json;
  try {
    registry = JSON.parse(decode(registryResponse.data.content));
  } catch {
    return NextResponse.json({ error: "Registry ist kein gültiges JSON." }, { status: 502 });
  }

  const projectsIn = (registry.projects || []).filter((p: Json) => p.enabled !== false);
  const results = await Promise.all(projectsIn.map((p: Json) => collectProject(p, token)));
  const projects = results.map((r) => r.project);
  const tasks = results.flatMap((r) => r.tasks);
  const counts: Record<string, number> = {};
  for (const p of projects) counts[p.overall] = (counts[p.overall] || 0) + 1;

  return NextResponse.json({
    generated_at: new Date().toISOString(),
    registry_repo: REGISTRY_REPO,
    github_auth: token ? (registryResponse.authFallback ? "public-fallback" : "authenticated") : "public",
    summary: {
      projects: projects.length,
      overall_counts: counts,
      open_external_tasks_total: tasks.length,
    },
    projects,
    tasks,
  });
}
