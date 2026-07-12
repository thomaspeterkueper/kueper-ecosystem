import Link from "next/link";

const REPO = "https://github.com/thomaspeterkueper/kueper-ecosystem";

type Tool = {
  title: string;
  desc: string;
  href: string;
  external?: boolean;
  status: "live" | "feed" | "quelle";
};

const TOOLS: Tool[] = [
  {
    title: "Telemetrie-Dashboard",
    desc: "Live-Zustand aller Projekte und alle offenen Cross-Repo-Tasks, sortiert nach Priorität. Mit Aktualisieren-Button.",
    href: "/dashboard",
    status: "live",
  },
  {
    title: "Status-Feed",
    desc: "Der rohe, normalisierte Snapshot als JSON — dieselbe Quelle, die das Dashboard rendert.",
    href: "/api/status",
    status: "feed",
  },
  {
    title: "Entscheidungen (ECO-ARC)",
    desc: "Die verbindlichen Architektur- und Normierungsentscheidungen des Ökosystems.",
    href: `${REPO}/tree/main/decisions`,
    external: true,
    status: "quelle",
  },
  {
    title: "Registry",
    desc: "Das Verzeichnis aller registrierten Projekte, Rollen und Integrationen.",
    href: `${REPO}/blob/main/registry/projects.json`,
    external: true,
    status: "quelle",
  },
];

export default function Hub() {
  return (
    <main className="wrap">
      <header className="console">
        <div className="brand">
          <span className="kicker">KUEPER · Control Plane</span>
          <h1>Werkzeuge des Ökosystems</h1>
          <span className="sub">Zentraler Einstiegspunkt in die Steuerungs- und Normierungswerkzeuge.</span>
        </div>
      </header>

      <div className="hub-grid">
        {TOOLS.map((t) => {
          const inner = (
            <>
              <div className="tool-top">
                <span className="tool-title">{t.title}</span>
                <span className={`tool-tag ${t.status}`}>{t.status}</span>
              </div>
              <p className="tool-desc">{t.desc}</p>
              <span className="tool-go">
                {t.external ? "Auf GitHub öffnen ↗" : "Öffnen →"}
              </span>
            </>
          );
          return t.external ? (
            <a className="tool" key={t.title} href={t.href} target="_blank" rel="noopener noreferrer">
              {inner}
            </a>
          ) : (
            <Link className="tool" key={t.title} href={t.href}>
              {inner}
            </Link>
          );
        })}
      </div>

      <footer className="hub-foot">
        Regeln und Task-Formate: <a href={`${REPO}/tree/main/decisions`} target="_blank" rel="noopener noreferrer">decisions/</a> ·{" "}
        <a href={`${REPO}/tree/main/docs`} target="_blank" rel="noopener noreferrer">docs/</a>
      </footer>
    </main>
  );
}
