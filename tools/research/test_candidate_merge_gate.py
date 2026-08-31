#!/usr/bin/env python3
"""Deterministic tests for the Phase-A research candidate merge gate."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("research_execute", ROOT / "tools/research/execute.py")
assert SPEC and SPEC.loader
EXECUTE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXECUTE)


def expect_runtime_error(item: dict, fragment: str) -> None:
    try:
        EXECUTE.validate_source_contract(item)
    except RuntimeError as exc:
        assert fragment in str(exc), str(exc)
    else:
        raise AssertionError(f"expected RuntimeError containing {fragment!r}")


def main() -> int:
    assert EXECUTE.POLICY.get("auto_merge_candidates") is False

    ota_base = {
        "id": "RES-TEST-OTA",
        "source_project": "ota",
        "evidence_profile": "ota-archive-evidence",
    }
    expect_runtime_error(ota_base, "requires source_path")
    expect_runtime_error({**ota_base, "source_path": "src/content/documents/example.md"}, "requires source_repository")
    expect_runtime_error({
        **ota_base,
        "source_path": "src/content/documents/example.md",
        "source_repository": "thomaspeterkueper/overtime-archive.org",
    }, "requires pinned source_ref")
    expect_runtime_error({
        **ota_base,
        "source_path": "src/content/documents/example.md",
        "source_repository": "thomaspeterkueper/overtime-archive.org",
        "source_ref": "0123456789abcdef",
    }, "requires pinned source_blob_sha")

    profile_name, profile = EXECUTE.validate_source_contract({
        **ota_base,
        "source_path": "src/content/documents/example.md",
        "source_repository": "thomaspeterkueper/overtime-archive.org",
        "source_ref": "0123456789abcdef",
        "source_blob_sha": "abcdef0123456789",
    })
    assert profile_name == "ota-archive-evidence"
    assert profile["require_source_path"] is True
    assert profile["pin_source_revision"] is True

    general_name, _ = EXECUTE.validate_source_contract({
        "id": "RES-TEST-GENERAL",
        "source_project": "kueper-com",
        "evidence_profile": "general",
    })
    assert general_name == "general"

    source = (ROOT / "tools/research/execute.py").read_text(encoding="utf-8")
    assert "gh pr merge" not in source
    assert "auto-merge-queued" not in source
    assert '"draft":True' in source
    assert 'merge="draft-review-required"' in source
    assert '"draft":True' in source
    assert "never marks it ready" in source

    print("candidate merge gate tests: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
