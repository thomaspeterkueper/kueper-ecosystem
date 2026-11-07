#!/usr/bin/env python3
from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import execute as core  # noqa: E402
from usage_observer import install  # noqa: E402

workflow = os.environ.get("GITHUB_WORKFLOW", "")
source_system = os.environ.get("KUEPER_USAGE_SOURCE_SYSTEM") or (
    "ota-workqueue-research" if "OTA Workqueue" in workflow else "targeted-research"
)
install(core, source_system)

if __name__ == "__main__":
    runpy.run_path(str(HERE / "execute-targeted.py"), run_name="__main__")
