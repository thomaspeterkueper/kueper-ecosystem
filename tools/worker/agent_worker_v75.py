#!/usr/bin/env python3
"""KUEPER V7.5 worker: compact provider blocker persistence.

The provider pause record keeps the bounded provider diagnostic in `p_error_message`,
but task rescheduling must not copy that diagnostic into `blocked_reason`. V7.3 uses
`str(ProviderUnavailable)` for the task reason, so V7.5 gives that exception a stable,
compact string representation while retaining `.message` for provider diagnostics.
"""
from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import agent_worker as worker  # noqa: E402
import agent_worker_v74 as v74  # noqa: E402


def canonical_provider_reason(exc: worker.ProviderUnavailable) -> str:
    return f"Provider unavailable: {exc.provider} / {exc.code}"


def _provider_unavailable_str(self: worker.ProviderUnavailable) -> str:
    return canonical_provider_reason(self)


def main() -> int:
    worker.ProviderUnavailable.__str__ = _provider_unavailable_str
    return v74.main()


if __name__ == "__main__":
    raise SystemExit(main())
