#!/usr/bin/env python3
r"""
KUEPER Ecosystem — Signature Scanner v2
Umsetzung von ECO-ARC-0032. Korrigiert gegenueber v1:

  - Nutzt die Git Trees API statt der GitHub Code Search API. Ein Testlauf
    am 2026-09-07 zeigte, dass /search/code mit dem verwendeten
    Fine-grained-PAT durchgaengig `"incomplete_results": true` und
    `total_count: 0` lieferte -- auch fuer garantiert vorhandene Begriffe
    ("README", "NOXIA"). Die Trees-API (rekursiver Verzeichnisbaum je
    Branch + Datei-Inhalt on demand) liefert zuverlaessige, vollstaendige
    Ergebnisse und wird deshalb stattdessen verwendet.
  - `nextFree` wird nie unter den zuvor bekannten Wert gesetzt (Bugfix:
    v1 ueberschrieb einen von Hand gepflegten hoeheren Wert mit einem aus
    zu wenigen Daten berechneten niedrigeren Wert, weil Signaturen aus dem
    nicht automatisierten Drive-Anteil im GitHub-Scan naturgemaess fehlen).

Aufgabe:
  Durchsucht registrierte GitHub-Repositories nach OTA-*/ENG-*-Signaturen
  (Muster: OTA-[A-Z]+-\d{4} und ENG-[A-Z]+-\d{4}) und aktualisiert
  registry/ota-signature-index.json. Schreibt ausschliesslich lesend in
  GitHub, nichts in Ziel-Repositories.

  Der Google-Drive-Anteil (overtime-archive-Ordner) ist WEITERHIN NICHT
  automatisiert und muss bis zur Einrichtung eines Drive-Service-Accounts
  von Hand gepflegt werden (siehe ECO-ARC-0032, "Nicht entschieden").

Nutzung:
  GH_TOKEN=<token> python3 tools/collector/scan_signatures.py \
      > registry/ota-signature-index.json
"""
import json, os, re, sys, datetime, urllib.request, urllib.error

API = "https://api.github.com"
REG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "registry", "ota-signature-index.json")

SCAN_REPOS = [
    ("thomaspeterkueper/noxiagame", "main"),
    ("thomaspeterkueper/kueper-engineering", "main"),
    ("thomaspeterkueper/overtime-archive.org", "master"),
]

RELEVANT_PATH_HINTS = ("external-tasks/", "requirements/", "spacecraft/", "vehicles/",
                        "systems/", "stations/", "components/", "designs/", "calculations/",
                        "src/content/documents/")

SIGNATURE_PATTERN = re.compile(r"\b(OTA|ENG)-([A-Z]+)-(\d{4})\b")
FRONTMATTER_TITLE = re.compile(r"^title:\s*(.+)$", re.MULTILINE)
FRONTMATTER_STATUS = re.compile(r"^status:\s*(.+)$", re.MULTILINE)
FRONTMATTER_SIGNATURE = re.compile(r"^(?:signature|canonicalId):\s*[\"']?([A-Z]+-[A-Z]+-\d{4})", re.MULTILINE)


def defining_signatures(path, content):
    """Liefert nur Signaturen, die dieses Dokument tatsaechlich DEFINIERT
    (Dateiname oder Frontmatter signature:/canonicalId:-Feld) -- nicht
    jede blosse Erwaehnung im Fliesstext (relatedDocuments, Prosa-Verweise
    auf andere Dossiers). Ein External Task, der z.B. 'OTA-TEC-0082' nur
    in einem Satz erwaehnt, definiert diese Signatur nicht und darf keine
    Kollision ausloesen.

    Abgeschlossene Vorgangsprotokolle unter external-tasks/done/ definieren
    ebenfalls keine Signatur -- sie dokumentieren nur, dass ein frueherer
    Zwischenstand verarbeitet wurde, und verweisen typischerweise explizit
    auf die kanonische Fassung anderswo (Fund vom 2026-09-07: eine solche
    Datei fuer OTA-TEC-0034 loeste faelschlich eine Kollisionsmeldung aus)."""
    if "/done/" in path or path.startswith("done/"):
        return set()
    found = set()
    fname_match = SIGNATURE_PATTERN.search(os.path.basename(path))
    if fname_match:
        found.add(fname_match.groups())
    for m in FRONTMATTER_SIGNATURE.finditer(content):
        full = m.group(1)
        parts = SIGNATURE_PATTERN.match(full)
        if parts:
            found.add(parts.groups())
    return found


def _token():
    t = os.environ.get("GH_TOKEN")
    if not t:
        sys.stderr.write("GH_TOKEN nicht gesetzt.\n")
        sys.exit(2)
    return t


def gh(path, token, raw=False):
    req = urllib.request.Request(API + path)
    req.add_header("Authorization", f"Bearer {token}")
    if raw:
        req.add_header("Accept", "application/vnd.github.raw")
    else:
        req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    try:
        with urllib.request.urlopen(req) as r:
            body = r.read()
            if raw:
                return r.status, body.decode("utf-8", errors="replace")
            return r.status, json.loads(body)
    except urllib.error.HTTPError as e:
        return e.code, None
    except urllib.error.URLError:
        return 0, None


def list_relevant_files(repo, branch, token):
    status, data = gh(f"/repos/{repo}/git/trees/{branch}?recursive=1", token)
    if status != 200 or not data:
        sys.stderr.write(f"WARN: Trees-API fehlgeschlagen fuer {repo}@{branch} (status {status})\n")
        return []
    paths = [t["path"] for t in data.get("tree", [])
             if t.get("type") == "blob"
             and t["path"].endswith(".md")
             and any(t["path"].startswith(h) for h in RELEVANT_PATH_HINTS)]
    return paths


def fetch_file(repo, branch, path, token):
    status, content = gh(f"/repos/{repo}/contents/{path}?ref={branch}", token, raw=True)
    if status != 200:
        return None
    return content


def load_registry():
    with open(REG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def reset_scanned_state(registry):
    """Entfernt vor einem neuen Lauf:
    (a) alle Signaturen und Kollisionen aus einem frueheren GitHub-Scan
        (location beginnt mit einem SCAN_REPOS-Praefix), damit veraltete
        Scan-Ergebnisse nicht unbegrenzt weiterbestehen;
    (b) provisorische, von Hand eingetragene Drive-Vermutungen
        ("overtime-archive/Drive:root" bzw. ".../Drive:Eingang"), sobald
        das zugehoerige Objekt jetzt durch den echten Scan von
        overtime-archive.org abgedeckt ist -- diese Vermutungen erzeugten
        sonst systematisch Falsch-Kollisionen durch abweichende
        Titel-Strings fuer dasselbe Objekt (Fund vom 2026-09-07: fast
        alle TEC-Eintraege 0016-0097 wurden so faelschlich als Kollision
        gemeldet, weil der manuelle Kurztitel nicht exakt dem echten
        Frontmatter-Titel entsprach).

    Manuell gepflegte Eintraege, die AUSSCHLIESSLICH in Google Drive und
    NICHT im overtime-archive.org-Repo existieren (z.B. die "Kette vom
    Hexenteich"-Familie im Legacy-Ordner), bleiben unangetastet -- diese
    werden am Ende von main() gegen die frisch gescannten Repo-Daten
    geprueft und nur entfernt, wenn ein Treffer mit identischer Serie/
    Nummer im Scan auftaucht."""
    scanned_prefixes = tuple(f"{repo}:" for repo, _ in SCAN_REPOS)
    for entry in registry.get("series", {}).values():
        entry["signatures"] = {
            n: v for n, v in entry.get("signatures", {}).items()
            if not v.get("location", "").startswith(scanned_prefixes)
        }
        entry["collisions"] = [
            c for c in entry.get("collisions", [])
            if not any(occ.split(" (")[0].startswith(scanned_prefixes) for occ in c.get("occurrences", []))
        ]


def prune_superseded_drive_guesses(registry):
    """Entfernt provisorische 'overtime-archive/Drive:root'/'Drive:Eingang'-
    Eintraege, sobald dieselbe Serie+Nummer jetzt aus dem echten
    overtime-archive.org-Scan vorliegt. Laeuft NACH der Scan-Schleife."""
    for entry in registry.get("series", {}).values():
        git_covered = {
            n for n, v in entry.get("signatures", {}).items()
            if v.get("location", "").startswith("thomaspeterkueper/overtime-archive.org:")
        }
        entry["signatures"] = {
            n: v for n, v in entry.get("signatures", {}).items()
            if not (
                v.get("location", "").startswith(("overtime-archive/Drive:root", "overtime-archive/Drive:Eingang"))
                and n in git_covered
            )
        }
        entry["collisions"] = [
            c for c in entry.get("collisions", [])
            if not (
                len(c["occurrences"]) == 2
                and any(o.startswith(("overtime-archive/Drive:root", "overtime-archive/Drive:Eingang")) for o in c["occurrences"])
                and any(o.startswith("thomaspeterkueper/overtime-archive.org:") for o in c["occurrences"])
            )
        ]


def merge_signature(registry, series, number, title, status, location, today):
    s = registry["series"].setdefault(
        series, {"nextFree": None, "signatures": {}, "collisions": []}
    )
    existing = s["signatures"].get(number)
    if existing and existing.get("location") != location and existing.get("title") != title:
        occ = [f"{existing.get('location')} ({existing.get('title')})", f"{location} ({title})"]
        already = [c for c in s.setdefault("collisions", []) if c["signature"] == number]
        if not already:
            s["collisions"].append({"signature": number, "occurrences": occ})
    s["signatures"][number] = {
        "title": title,
        "status": status,
        "location": location,
        "lastSeen": today,
    }


def recompute_next_free(series_entry):
    nums = []
    for n in series_entry["signatures"].keys():
        digits = "".join(ch for ch in n[:4] if ch.isdigit())
        if len(digits) == 4:
            nums.append(int(digits))
    computed = (max(nums) + 1) if nums else None
    previous = series_entry.get("nextFree")
    if computed is None:
        return previous
    if previous is None:
        return computed
    return max(computed, previous)


def main():
    token = _token()
    registry = load_registry()
    today = datetime.date.today().isoformat()
    reset_scanned_state(registry)

    for repo, branch in SCAN_REPOS:
        for path in list_relevant_files(repo, branch, token):
            content = fetch_file(repo, branch, path, token)
            if content is None:
                continue
            for _, series, number in defining_signatures(path, content):
                title_m = FRONTMATTER_TITLE.search(content)
                status_m = FRONTMATTER_STATUS.search(content)
                title = title_m.group(1).strip() if title_m else path
                status = status_m.group(1).strip().upper() if status_m else "UNKNOWN"
                if status not in ("ENTWURF", "AKTIV", "SUPERSEDED", "REJECTED"):
                    status = "UNKNOWN"
                merge_signature(
                    registry, series, number,
                    title=title, status=status,
                    location=f"{repo}:{path}", today=today,
                )

    for series, entry in registry["series"].items():
        entry["nextFree"] = recompute_next_free(entry)

    prune_superseded_drive_guesses(registry)

    registry["lastScanned"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    print(json.dumps(registry, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
