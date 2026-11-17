#!/usr/bin/env python3
"""Deterministic tests for the KG candidate merge triage and the Canon Conflict queue selection."""
from __future__ import annotations

import base64
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools/research" / file)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


TRIAGE = load("triage_candidates", "triage_candidates.py")
VALIDATE = load("validate_candidates", "validate_candidates.py")

GOOD = """# Titel

Status: candidate / non-canonical

## Forschungsfrage
x
## Kurzfazit
x
## Claim-Klassifikation
x
## Aktualität und Widerspruchsprüfung
x
## Befundlage
x
## Gegenbefunde und Unsicherheit
x
## Claim-Source-Mapping
x
## Quellen
- [Q1] peer-reviewed https://a.example.org/1
- [Q2] https://b.example.net/2
- [Q3] https://c.example.edu/3
## Relevanz für KUEPER-Projekte
x
## Publikationsroute
x
## Offene Fragen
x
"""


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def make_repo(tmp: Path) -> Path:
    kg = tmp / "kg"
    kg.mkdir()
    git(kg, "init", "-q", "-b", "main")
    git(kg, "config", "user.email", "t@t")
    git(kg, "config", "user.name", "t")
    (kg / "research/candidates").mkdir(parents=True)
    (kg / "research/candidates/RES-OLD.md").write_text(GOOD, encoding="utf-8")
    git(kg, "add", ".")
    git(kg, "commit", "-qm", "base")
    # good candidate
    git(kg, "checkout", "-qb", "research/res-test-good", "main")
    (kg / "research/candidates/RES-TEST-GOOD.md").write_text(GOOD, encoding="utf-8")
    git(kg, "add", ".")
    git(kg, "commit", "-qm", "good")
    # candidate that touches another file and lacks a section
    git(kg, "checkout", "-qb", "research/res-test-bad", "main")
    (kg / "research/candidates/RES-TEST-BAD.md").write_text(GOOD.replace("## Offene Fragen", "## Fragen") + "TODO\n", encoding="utf-8")
    (kg / "README.md").write_text("x", encoding="utf-8")
    git(kg, "add", ".")
    git(kg, "commit", "-qm", "bad")
    git(kg, "checkout", "-q", "main")
    return kg


def queue_entry(qdir: Path, rid: str, pr: int, status: str = "candidate-pr") -> None:
    (qdir / f"{rid}.json").write_text(json.dumps({
        "id": rid, "status": status, "source_project": "ota", "evidence_profile": "ota-archive-evidence",
        "candidate_pr": f"https://github.com/x/y/pull/{pr}",
    }), encoding="utf-8")


def test_triage() -> None:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        kg = make_repo(tmp)
        qdir = tmp / "queue"
        qdir.mkdir()
        queue_entry(qdir, "RES-TEST-GOOD", 1)
        queue_entry(qdir, "RES-TEST-BAD", 2)
        on_main = {"RES-OLD"}
        seen = {"RES-TEST-GOOD": [1], "RES-TEST-BAD": [2], "RES-OLD": [3]}
        good = TRIAGE.triage_pr({"number": 1, "head_ref": "research/res-test-good", "head_sha": "research/res-test-good",
                                 "checks_ok": True, "mergeable": True}, kg, qdir, "main", on_main, seen)
        assert good["decision"] == "merge", good
        red = TRIAGE.triage_pr({"number": 1, "head_ref": "research/res-test-good", "head_sha": "research/res-test-good",
                                "checks_ok": False, "mergeable": True}, kg, qdir, "main", on_main, seen)
        assert red["decision"] == "hold" and "CI not green" in red["reasons"], red
        bad = TRIAGE.triage_pr({"number": 2, "head_ref": "research/res-test-bad", "head_sha": "research/res-test-bad",
                                "checks_ok": True, "mergeable": True}, kg, qdir, "main", on_main, seen)
        joined = " ".join(bad["reasons"])
        assert bad["decision"] == "hold"
        assert "changes other files" in joined and "missing sections" in joined and "placeholder" in joined, bad
        old = TRIAGE.triage_pr({"number": 3, "head_ref": "research/res-old", "head_sha": "main",
                                "checks_ok": True, "mergeable": True}, kg, qdir, "main", on_main, seen)
        assert old["decision"] == "close", old
        other = TRIAGE.triage_pr({"number": 4, "head_ref": "research/reconcile-x"}, kg, qdir, "main", on_main, seen)
        assert other["decision"] == "hold", other
        assert TRIAGE.check_text(GOOD.replace("TODO", "") + "| a | TBD |\n", {"evidence_profile": "ota-archive-evidence"}) == []


def test_canon_conflict_skips_unmerged() -> None:
    files = [{"type": "file", "name": f"{rid}.json", "path": f"research/queue/{rid}.json"}
             for rid in ("RES-A-OLD-UNMERGED", "RES-B-MERGED", "RES-C-MERGED")]
    fetched: list[str] = []

    def fake_gh(token, method, path, body=None):
        if path.startswith("/repos/thomaspeterkueper/kueper-ecosystem/contents/research/queue?"):
            return files
        rid = path.split("/")[-1].split(".json")[0]
        fetched.append(rid)
        data = {"id": rid, "status": "candidate-pr", "updated_at": rid}
        return {"sha": "s", "content": base64.b64encode(json.dumps(data).encode()).decode()}

    orig = VALIDATE.gh
    VALIDATE.gh = fake_gh
    try:
        items = VALIDATE.queue("t", {"RES-B-MERGED", "RES-C-MERGED"})
    finally:
        VALIDATE.gh = orig
    assert [i["id"] for i, _ in items] == ["RES-B-MERGED", "RES-C-MERGED"], items
    assert "RES-A-OLD-UNMERGED" not in fetched


def main() -> int:
    test_triage()
    test_canon_conflict_skips_unmerged()
    print("candidate triage tests: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
