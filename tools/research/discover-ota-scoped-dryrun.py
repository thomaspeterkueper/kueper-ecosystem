#!/usr/bin/env python3
"""Run the cooled OTA discovery algorithm without mutating the research queue.

This wrapper loads the production cooldown wrapper unchanged, blocks only
queue-file PUTs, and rewrites the final report so benchmark proposals are clearly
distinguished from persisted queue items.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
TARGET = HERE / "discover-ota-cooled.py"


def load_module():
    spec = importlib.util.spec_from_file_location("discover_ota_cooled", TARGET)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {TARGET}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_module()
    original_gh = module.core.gh

    def dry_gh(token: str, method: str, path: str, body: dict[str, Any] | None = None):
        if method.upper() == "PUT" and "/contents/research/queue/" in path:
            return {"dry_run": True, "path": path}
        return original_gh(token, method, path, body)

    module.core.gh = dry_gh
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        rc = module.main()

    raw = buffer.getvalue().strip()
    if not raw:
        raise RuntimeError("cooled scoped discovery produced no report")
    report = json.loads(raw)
    proposed = int(report.get("queued", 0) or 0)
    report["dry_run"] = True
    report["proposed"] = proposed
    report["queued"] = 0
    report["reaudit_cooldown_days"] = module.COOLDOWN_DAYS
    for item in report.get("items", []):
        if isinstance(item, dict):
            item["status"] = "proposed-dry-run"

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
