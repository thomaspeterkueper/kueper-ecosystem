#!/usr/bin/env python3
"""Run deterministic OTA discovery with a per-document re-audit cooldown.

The production scoped selector already suppresses an exact source blob forever.
After an evidence audit, however, the OTA source document is often corrected and
therefore receives a new blob SHA. Without a second guard that corrected document
can immediately become the highest-scoring candidate again.

This wrapper keeps the scoped algorithm unchanged and adds only one selection
rule: a source_path researched recently is skipped for a configurable number of
days even when its blob changed. Set KUEPER_OTA_REAUDIT_COOLDOWN_DAYS=0 to disable
that temporal guard for an intentional immediate re-audit.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import os
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
TARGET = HERE / "discover-ota-scoped.py"
COOLDOWN_DAYS = max(0, int(os.environ.get("KUEPER_OTA_REAUDIT_COOLDOWN_DAYS", "30")))


def load_scoped():
    spec = importlib.util.spec_from_file_location("discover_ota_scoped_base", TARGET)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {TARGET}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


scoped = load_scoped()
# Exposed deliberately: the dry-run wrapper patches core.gh on the loaded module.
core = scoped.core


def parse_created(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip().replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def recently_audited(history: list[dict[str, Any]], path: str) -> bool:
    if COOLDOWN_DAYS <= 0:
        return False
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(days=COOLDOWN_DAYS)
    for item in history:
        if item.get("source_project") != scoped.PROJECT_ID:
            continue
        if item.get("source_path") != path:
            continue
        created = parse_created(item.get("created"))
        if created is not None and cutoff <= created <= now:
            return True
    return False


def main() -> int:
    original_skip = scoped.already_audited_current_revision

    def skip_with_cooldown(
        history: list[dict[str, Any]], path: str, current_blob: str
    ) -> bool:
        # Preserve the permanent exact-revision/legacy guard first.
        if original_skip(history, path, current_blob):
            return True
        return recently_audited(history, path)

    scoped.already_audited_current_revision = skip_with_cooldown
    try:
        return scoped.main()
    finally:
        scoped.already_audited_current_revision = original_skip


if __name__ == "__main__":
    raise SystemExit(main())
