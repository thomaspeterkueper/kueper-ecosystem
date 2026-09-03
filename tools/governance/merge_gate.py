#!/usr/bin/env python3
"""
KUEPER Ecosystem — Governance Merge Gate

Verhindert, dass die kanonische Code-Menge bzw. der Registry-Eintrag fuer
`buecherwelten` (Code `BW`) gemerged wird, solange die zugrunde liegenden
Architekturentscheidungen ECO-ARC-0030 und ECO-ARC-0031 nicht durch den
Project Owner angenommen sind (Status: accepted). Die Entscheidungen
reservieren domain/canonical-Festlegungen fuer den Owner (ECO-ARC-0027);
deren Umsetzung darf erst nach Annahme wirksam werden.

Prueft deterministisch, ohne Netzwerk:

  1. Status der Entscheidungen ECO-ARC-0030/0031.
  2. Ob der zu mergende Stand die BW-Governance-Objekte enthaelt:
     - schemas/external-task.schema.json (id-Muster, source/target/affects),
     - tools/lint-external-tasks/lint.py (Code-Set),
     - decisions/ECO-ARC-0006-2026-DE.md (Code-Tabelle),
     - registry/projects.json (Eintrag `buecherwelten` / code `BW`).

Sind die Objekte vorhanden, ohne dass beide Entscheidungen `accepted` sind,
ist der Merge gesperrt. Ist eine der Entscheidungen nicht angenommen oder
nicht lesbar, gilt sie als nicht angenommen (konservativ).

Nutzung:
  python3 tools/governance/merge_gate.py [<repo-root>]

Exit-Code 0 = Merge freigegeben, 1 = Merge gesperrt (CI-faehig).
"""
import json
import os
import re
import sys

DECISIONS = [
    ("ECO-ARC-0030", "decisions/ECO-ARC-0030-2026-DE.md"),
    ("ECO-ARC-0031", "decisions/ECO-ARC-0031-2026-DE.md"),
]
SCHEMA_PATH = "schemas/external-task.schema.json"
LINT_PATH = "tools/lint-external-tasks/lint.py"
CODE_TABLE_PATH = "decisions/ECO-ARC-0006-2026-DE.md"
REGISTRY_PATH = "registry/projects.json"

# Kanonische Stellen, an denen der Code BW wirksam wird (ECO-ARC-0031 §4).
STATUS_RE = re.compile(r"^Status:\s*(.+?)\s*$", re.MULTILINE)


def decision_status(path):
    """Status-Zeile (z. B. `proposed`, `accepted`) aus der Entscheidungsdatei."""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return None
    m = STATUS_RE.search(text)
    return m.group(1).strip().lower() if m else None


def decisions_accepted(root):
    for name, rel in DECISIONS:
        status = decision_status(os.path.join(root, rel))
        if status != "accepted":
            return False
    return True


def _schema_has_bw(path):
    try:
        with open(path, encoding="utf-8") as f:
            schema = json.load(f)
    except (OSError, ValueError):
        return False
    def contains(enum_or_pattern):
        if isinstance(enum_or_pattern, list):
            return "BW" in enum_or_pattern
        if isinstance(enum_or_pattern, str):
            return "BW" in enum_or_pattern
        return False
    props = schema.get("properties", {})
    return (
        contains(props.get("id", {}).get("pattern"))
        or contains(props.get("source", {}).get("enum"))
        or contains(props.get("target", {}).get("enum"))
        or contains(props.get("affects", {}).get("items", {}).get("enum"))
    )


def _lint_has_bw(path):
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return False
    return re.search(r'CODES\s*=\s*\{[^}]*"BW"', text) is not None


def _code_table_has_bw(path):
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return False
    return re.search(r"^\|\s*`BW`\s*\|", text, re.MULTILINE) is not None


def _registry_has_bw(path):
    try:
        with open(path, encoding="utf-8") as f:
            reg = json.load(f)
    except (OSError, ValueError):
        return False
    return any(
        p.get("id") == "buecherwelten" or p.get("code") == "BW"
        for p in reg.get("projects", [])
    )


def governed_bw_present(root):
    """Enthaelt der Stand die BW-Governance-Objekte der kanonischen Code-Menge?"""
    return (
        _schema_has_bw(os.path.join(root, SCHEMA_PATH))
        or _lint_has_bw(os.path.join(root, LINT_PATH))
        or _code_table_has_bw(os.path.join(root, CODE_TABLE_PATH))
        or _registry_has_bw(os.path.join(root, REGISTRY_PATH))
    )


def main(argv):
    root = argv[0] if argv else "."

    accepted = decisions_accepted(root)
    governed = governed_bw_present(root)

    if accepted:
        print("OK  ECO-ARC-0030 und ECO-ARC-0031 sind angenommen (Status: accepted).")
        if governed:
            print("OK  BW-Governance-Objekte (Schema/Linter/Code-Tabelle/Registry) duerfen gemerged werden.")
        return 0

    if not governed:
        print("OK  Keine BW-Governance-Objekte im zu mergenden Stand; Merge nicht gesperrt.")
        print("OK  (ECO-ARC-0030/0031 sind weiterhin nicht angenommen.)")
        return 0

    names = ", ".join(name for name, _ in DECISIONS)
    print(f"BLOCK {names}: nicht angenommen (Owner-Abnahme ausstehend).", file=sys.stderr)
    print("BLOCK Der Stand enthaelt BW-Governance-Objekte (Schema/Linter/Code-Tabelle/Registry).", file=sys.stderr)
    print("BLOCK Merge ist gesperrt, bis der Project Owner beide Entscheidungen auf `Status: accepted`", file=sys.stderr)
    print("BLOCK setzt (domain/canonical decision, ECO-ARC-0027; ECO-ARC-0030 Folgeaufgabe 3).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
