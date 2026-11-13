#!/usr/bin/env bash
# Heartbeat-Ping für Workflows und geplante Läufe (ECO-OPS-20261028-heartbeats).
#
#   tools/ops/heartbeat.sh HEARTBEAT_GOVERNANCE_SWEEP          # Erfolg melden
#   tools/ops/heartbeat.sh HEARTBEAT_GOVERNANCE_SWEEP fail     # Fehler melden (/fail)
#
# Erstes Argument ist der NAME der Umgebungsvariablen mit der Heartbeat-URL,
# nicht die URL selbst. Fehlt die Variable, tut das Skript nichts und endet
# mit 0 – Workflows ohne gesetztes Secret laufen unverändert.
# Die URL wird nie ausgegeben. Ein fehlgeschlagener Ping bricht nichts ab.
set -u

var="${1:-}"
mode="${2:-success}"

if [ -z "$var" ]; then
  echo "heartbeat: Variablenname fehlt" >&2
  exit 0
fi
case "$var" in
  *[!A-Z0-9_]*) echo "heartbeat: ungültiger Variablenname" >&2; exit 0 ;;
esac

url="${!var:-}"
if [ -z "$url" ]; then
  echo "heartbeat: $var nicht gesetzt – übersprungen"
  exit 0
fi

case "$mode" in
  success) target="$url" ;;
  fail)    target="${url%/}/fail" ;;
  *) echo "heartbeat: Modus muss success oder fail sein" >&2; exit 0 ;;
esac

if curl -fsS -m 10 --retry 2 -o /dev/null "$target" 2>/dev/null; then
  echo "heartbeat: $var ($mode) gemeldet"
else
  echo "heartbeat: $var ($mode) nicht erreichbar – ignoriert" >&2
fi
exit 0
