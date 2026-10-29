#!/usr/bin/env bash
# Pings a heartbeat URL taken from an environment variable.
# Usage: heartbeat.sh HEARTBEAT_VAR_NAME [fail]
# Does nothing (exit 0) if the variable is unset/empty or the request fails.
set -u
var="${1:-}"
[ -n "$var" ] || exit 0
url="${!var:-}"
[ -n "$url" ] || exit 0
[ "${2:-}" = "fail" ] && url="${url%/}/fail"
curl -fsS -m 10 --retry 2 -o /dev/null "$url" || echo "heartbeat: ping failed (ignored)" >&2
exit 0
