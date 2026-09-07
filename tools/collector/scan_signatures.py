#!/usr/bin/env python3
"""
KUEPER Ecosystem — Signature Scanner v1
Umsetzung von ECO-ARC-0032.

Aufgabe:
  Durchsucht registrierte GitHub-Repositories nach OTA-*/ENG-*-Signaturen
  (Muster: OTA-[A-Z]+-\\d{4} und ENG-[A-Z]+-\\d{4}) und aktualisiert
  registry/ota-signature-index.json. Schreibt ausschliesslich lesend in
  GitHub, nichts in Ziel-Repositories.

  Der Google-Drive-Anteil (overtime-archive-Ordner) ist NICHT automatisiert
  und muss bis zur Einrichtung eines Drive-Service-Accounts weiterhin von
  Hand gepflegt werden (siehe TODO unten und ECO-ARC-0032, "Nicht entschieden").

Nutzung:
  GH_TOKEN=<token> python3 tools/collector/scan_signatures.py \
      > registry/ota-signature-index.json

Zustandswerte je Signatur: siehe schemas/ota-signature-index.schema.json
"""
import json, os, re, sys, datetime, urllib.request, urllib.error

API = "https://api.github.com"
REG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "registry", "ota-signature-index.json")

# Repos, die nach OTA-*/ENG-*-Signaturen durchsucht werden.
# Ergaenzen, sobald weitere Repos External Tasks oder Dossiers fuehren.
SCAN_REPOS = [
    "thomaspeterkueper/noxiagame",
    "thomaspeterkueper/kueper-engineering",
]

SIGNATURE_PATTERN = re.compile(r"\b(OTA|ENG)-([A-Z]+)-(\d{4})\b")


def _token():
    t = os.environ.get("GH_TOKEN")
    if not t:
        sys.stderr.write("GH_TOKEN nicht gesetzt.\n")
        sys.exit(2)
    return t


def gh(path, token):
    req = urllib.request.Request(API + path)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, None
    except urllib.error.URLError:
        return 0, None


def search_code(query, token):
    """Nutzt die GitHub Code Search API. Rate-limitiert; bei grossen Repos
    ggf. auf Baumtraversierung umstellen."""
    status, data = gh(f"/search/code?q={urllib.parse.quote(query)}", token)
    if status != 200 or not data:
        return []
    return data.get("items", [])


def load_registry():
    with open(REG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def merge_signature(registry, series, number, title, status, location, today):
    s = registry["series"].setdefault(
        series, {"nextFree": None, "signatures": {}, "collisions": []}
    )
    existing = s["signatures"].get(number)
    if existing and existing.get("location") != location and existing.get("title") != title:
        # Moegliche Kollision: gleiche Nummer, unterschiedlicher Inhalt.
        occ = [f"{existing.get('location')} ({existing.get('title')})", f"{location} ({title})"]
        s.setdefault("collisions", []).append({"signature": number, "occurrences": occ})
    s["signatures"][number] = {
        "title": title,
        "status": status,
        "location": location,
        "lastSeen": today,
    }


def recompute_next_free(series_entry):
    nums = [int(n[:4]) for n in series_entry["signatures"].keys() if n[:4].isdigit()]
    if not nums:
        return series_entry.get("nextFree")
    return max(nums) + 1


def main():
    token = _token()
    registry = load_registry()
    today = datetime.date.today().isoformat()

    for repo in SCAN_REPOS:
        for prefix in ("OTA-", "ENG-"):
            for item in search_code(f"{prefix} repo:{repo} extension:md", token):
                path = item.get("path", "")
                name = item.get("name", "")
                m = SIGNATURE_PATTERN.search(name) or SIGNATURE_PATTERN.search(path)
                if not m:
                    continue
                _, series, number = m.groups()
                merge_signature(
                    registry, series, number,
                    title=name, status="UNKNOWN",
                    location=f"{repo}:{path}", today=today,
                )

    for series, entry in registry["series"].items():
        entry["nextFree"] = recompute_next_free(entry)

    registry["lastScanned"] = datetime.datetime.utcnow().isoformat() + "Z"

    # TODO(ECO-ARC-0032): Google-Drive-Anteil (overtime-archive-Ordner,
    # inkl. Eingang-Unterordner und dem veralteten Legacy-OTA-Ordner) ist
    # hier noch NICHT eingebunden. Erfordert einen Drive-Service-Account
    # mit Lesezugriff (siehe ECO-ARC-0032, "Nicht entschieden"). Bis dahin
    # muss der Drive-Anteil der Registry von Hand aktuell gehalten werden.

    print(json.dumps(registry, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    import urllib.parse
    main()
