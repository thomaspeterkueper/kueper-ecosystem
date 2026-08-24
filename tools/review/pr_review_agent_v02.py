#!/usr/bin/env python3
"""Hotfix wrapper for KUEPER PR reviewer v0.2.

Claude Code may emit diagnostic JSON objects before/after the requested review
object. The v0.1 parser used a greedy brace match and could therefore feed
multiple JSON objects to json.loads(), producing ``Extra data``. This wrapper
selects the first syntactically valid object that actually has the review
contract shape, then delegates the rest of the lifecycle to v0.1.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REVIEW_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REVIEW_DIR))
import pr_review_agent as base  # noqa: E402


def extract_review_json(text: str) -> dict[str, Any]:
    """Return the first valid JSON object matching the review contract.

    Non-review JSON diagnostics are ignored. Trailing text or additional JSON
    objects are allowed; malformed candidates are skipped. We deliberately do
    not make json.loads globally permissive, so GitHub/Supabase JSON parsing
    elsewhere stays strict.
    """
    decoder = json.JSONDecoder()
    source = text.strip()
    for index, char in enumerate(source):
        if char != "{":
            continue
        try:
            candidate, _ = decoder.raw_decode(source[index:])
        except json.JSONDecodeError:
            continue
        if (
            isinstance(candidate, dict)
            and candidate.get("verdict") in {"PASS", "CHANGES_REQUIRED"}
            and isinstance(candidate.get("findings"), list)
        ):
            return candidate
    raise base.worker.WorkerError("reviewer returned no review-contract JSON object")


# Patch only the review-output extraction boundary. All validation, persistence,
# idempotency and no-auto-merge semantics remain in the original implementation.
base.extract_json = extract_review_json


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
