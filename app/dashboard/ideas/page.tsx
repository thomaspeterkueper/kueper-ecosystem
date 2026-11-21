import { headers } from "next/headers";
import { timingSafeEqual } from "node:crypto";
import Link from "next/link";
import seed from "../../../data/idea-workshop-seed.json";

export const dynamic = "force-dynamic";
export const metadata = { title: "Ideen & Forschung | KUEPER Control Room", robots: { index: false, follow: false } };

function authorized(value: string | null, secret: string): boolean {
  if (!value?.startsWith("Bearer ") || !secret) return false;
  const received = Buffer.from(value.slice(7), "utf8");
  const expected = Buffer.from(secret, "utf8");
  return received.length === expected.length && timingSafeEqual(received, expected);
}

export default function IdeasPage() {
  // Fail closed: no secret means no content. Server-only environment variable.
  const secret = process.env.KUEPER_IDEAS_ADMIN_TOKEN || "";
  if (!authorized(headers().get("authorization"), secret)) {
    return <main style={{padding:"2rem",maxWidth:800,margin:"auto"}}><h1>Ideen & Forschung</h1><p>Dieser Bereich ist intern. Der Zugriff ist noch nicht für die bestehende Dashboard-Anmeldung freigeschaltet.</p><p>Keine Inhalte werden ohne serverseitige Berechtigung ausgegeben.</p><Link href="/dashboard">Zur Übersicht</Link></main>;
  }
  const counts = seed.items.reduce<Record<string,number>>((acc, item) => {acc[item.status]=(acc[item.status]||0)+1;return acc;},{});
  return <main style={{padding:"2rem",maxWidth:1100,margin:"auto"}}>
    <p><Link href="/dashboard">← Control Room</Link></p><h1>Ideen & Forschung</h1>
    <p>{seed.note}</p><p><strong>{seed.items.length} Themen</strong> · {Object.entries(counts).map(([k,v])=>`${v} ${k}`).join(" · ")}</p>
    <p>Quelle: <a href="https://github.com/thomaspeterkueper/kueper.com/pull/31">kueper.com Draft #31</a>. Diese Ansicht ist ein geprüfter Snapshot; keine Live-Synchronisation und keine Schreibfunktionen.</p>
    <section aria-label="Ideenliste" style={{display:"grid",gap:12}}>{seed.items.map(item=><article key={item.id} style={{border:"1px solid #8885",borderRadius:10,padding:16}}><small>{item.id} · {item.project} · {item.status}</small><h2 style={{fontSize:"1.15rem",margin:"8px 0"}}>{item.title}</h2><p style={{margin:0}}>Nächster Prüfschritt: {item.next}</p></article>)}</section>
  </main>;
}
