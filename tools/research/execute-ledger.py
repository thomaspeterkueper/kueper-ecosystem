#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import execute as core  # noqa: E402
from usage_observer import install  # noqa: E402

install(core, "knowledge-research")

if __name__ == "__main__":
    raise SystemExit(core.main())
