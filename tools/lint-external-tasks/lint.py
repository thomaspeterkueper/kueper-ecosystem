#!/usr/bin/env python3
"""
KUEPER Ecosystem — External-Task-Linter (ECO-ARC-0006 / ECO-ARC-0019)

Prueft eine kanonische External-Task-Datei:
  1. Dateiname folgt EXT-{SOURCE}-{TARGET}-{YYYYMMDD}-{NNN}.md
  2. YAML-Frontmatter erfuellt schemas/external-task.schema.json
  3. Pflicht-Sektionen im Body vorhanden
  4. id im Frontmatter passt zum Dateinamen
  5. source != target
  6. optionale execution_class ist A, B oder C

Nutzung:
  python3 tools/lint-external-tasks/lint.py <datei.md> [<datei2.md> ...]
  python3 tools/lint-external-tasks/lint.py --all <repo-root>

Exit-Code 0 = alle gueltig, 1 = mind. ein Verstoss. Reine Syntax-/
Struktur-Pruefung ohne Netzwerk. Kein jsonschema-Paket noetig (nur stdlib).
"""
import sys, os, re, json, glob

CODES = {"ECO", "KG", "SSF", "NOXIA", "NXU", "MISH", "OMNI", "AVI", "CONTRA", "ARCH", "ENDIA", "ZEREYA", "DAVARU", "FLHERM", "RESETH", "KUE", "OTA", "TKD"}
FILENAME_RE = re.compile(
    r"^EXT-(ECO|KG|SSF|NOXIA|NXU|MISH|OMNI|AVI|CONTRA|ARCH|ENDIA|ZEREYA|DAVARU|FLHERM|RESETH|KUE|OTA|TKD)-(ECO|KG|SSF|NOXIA|NXU|MISH|OMNI|AVI|CONTRA|ARCH|ENDIA|ZEREYA|DAVARU|FLHERM|RESETH|KUE|OTA|TKD)-\d{8}-\d{3}\.md$"
)
ID_RE = re.compile(
    r"^EXT-(ECO|KG|SSF|NOXIA|NXU|MISH|OMNI|AVI|CONTRA|ARCH|ENDIA|ZEREYA|DAVARU|FLHERM|RESETH|KUE|OTA|TKD)-(ECO|KG|SSF|NOXIA|NXU|MISH|OMNI|AVI|CONTRA|ARCH|ENDIA|ZEREYA|DAVARU|FLHERM|RESETH|KUE|OTA|TKD)-\d{8}-\d{3}$"
)
REQUIRED_FM = ["id", "status", "source", "target", "created", "requested_by"]
STATUS = {"open", "done", "rejected", "parked"}
PRIORITY = {"low", "medium", "high", "critical"}
EXECUTION_CLASS = {"A", "B", "C"}
REQUIRED_SECTIONS = [
    "## Anlass",
    "## Gewünschte Änderung",
    "## Begründung",
    "## Betroffene Repositories",
    "## Erwartetes Ergebnis",
]


def parse_frontmatter(text):
    """Minimaler YAML-Frontmatter-Parser (flache key: value + einfache Listen)."""
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text
    block = text[3:end].strip("\n")
    body = text[end + 4:]
    fm = {}
    cur_list_key = None
    for line in block.splitlines():
        if not line.strip():
            continue
        if cur_list_key and line.lstrip().startswith("- "):
            fm[cur_list_key].append(line.lstrip()[2:].strip())
            continue
        cur_list_key = None
        if ":" in line:
            k, v = line.split(":", 1)
            k, v = k.strip(), v.strip()
            if v == "":
                fm[k] = []
                cur_list_key = k
            else:
                fm[k] = v
    return fm, body


def lint_file(path):
    errors = []
    name = os.path.basename(path)
    if not FILENAME_RE.match(name):
        errors.append(f"Dateiname folgt nicht EXT-SOURCE-TARGET-YYYYMMDD-NNN.md: {name}")

    with open(path, encoding="utf-8") as f:
        text = f.read()

    fm, body = parse_frontmatter(text)
    if fm is None:
        errors.append("Kein YAML-Frontmatter (--- ... ---) am Dateianfang.")
        return errors

    for k in REQUIRED_FM:
        if k not in fm:
            errors.append(f"Frontmatter-Pflichtfeld fehlt: {k}")

    fid = fm.get("id", "")
    if fid and not ID_RE.match(fid):
        errors.append(f"id ungueltig: {fid}")
    if fid and name.startswith("EXT-") and fid != name[:-3]:
        errors.append(f"id ({fid}) != Dateiname ({name[:-3]})")

    if fm.get("status") not in STATUS:
        errors.append(f"status ungueltig: {fm.get('status')}")
    if fm.get("source") not in CODES:
        errors.append(f"source ungueltig: {fm.get('source')}")
    if fm.get("target") not in CODES:
        errors.append(f"target ungueltig: {fm.get('target')}")
    if fm.get("source") and fm.get("source") == fm.get("target"):
        errors.append("source und target duerfen nicht gleich sein.")
    if "priority" in fm and fm["priority"] not in PRIORITY:
        errors.append(f"priority ungueltig: {fm['priority']}")
    if "execution_class" in fm and fm["execution_class"] not in EXECUTION_CLASS:
        errors.append(f"execution_class ungueltig: {fm['execution_class']}")
    if "created" in fm and not re.match(r"^\d{4}-\d{2}-\d{2}$", str(fm["created"])):
        errors.append(f"created ist kein ISO-Datum: {fm['created']}")

    for sec in REQUIRED_SECTIONS:
        if sec not in body:
            errors.append(f"Pflicht-Sektion fehlt: {sec}")

    return errors


def iter_task_files(root):
    for state in ("open", "done", "rejected", "parked"):
        yield from glob.glob(os.path.join(root, "external-tasks", state, "*.md"))


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == "--all":
        files = list(iter_task_files(argv[1] if len(argv) > 1 else "."))
    else:
        files = argv

    total = 0
    for path in files:
        errs = lint_file(path)
        total += len(errs)
        if errs:
            print(f"FAIL {path}")
            for e in errs:
                print(f"     - {e}")
        else:
            print(f"OK   {path}")
    print(f"\n{len(files)} Datei(en), {total} Verstoss(e).")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
