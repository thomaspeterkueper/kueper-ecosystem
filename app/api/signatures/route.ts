import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const revalidate = 0;
export const runtime = "nodejs";

const API = "https://api.github.com";
const REGISTRY_REPO = process.env.REGISTRY_REPO || "thomaspeterkueper/kueper-ecosystem";
const REGISTRY_PATH = "registry/ota-signature-index.json";

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

function decode(b64: string): string {
  return Buffer.from(b64, "base64").toString("utf-8");
}

export async function GET() {
  const token = process.env.GH_TOKEN;
  if (!token) {
    return NextResponse.json(
      { error: "GH_TOKEN nicht konfiguriert (server-seitig)." },
      { status: 500 }
    );
  }

  const res = await gh(`/repos/${REGISTRY_REPO}/contents/${REGISTRY_PATH}?ref=main`, token);
  if (!res.ok) {
    return NextResponse.json(
      { error: `Registry nicht lesbar (Status ${res.status}).` },
      { status: 502 }
    );
  }
  const file = await res.json();
  let registry: unknown;
  try {
    registry = JSON.parse(decode(file.content));
  } catch {
    return NextResponse.json(
      { error: "Registry-Datei ist kein valides JSON." },
      { status: 502 }
    );
  }

  return NextResponse.json({
    fetchedAt: new Date().toISOString(),
    sourceUrl: file.html_url as string,
    registry,
  });
}
