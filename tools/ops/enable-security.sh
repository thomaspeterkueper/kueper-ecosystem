#!/usr/bin/env bash
# Sicherheitsbaseline der KUEPER-Repositories (ECO-OPS-20261028-security-baseline).
#
#   tools/ops/enable-security.sh                 # Soll-Zustand anwenden
#   tools/ops/enable-security.sh --check         # nur lesen, Exit 1 bei Abweichung
#   tools/ops/enable-security.sh --json          # maschinenlesbar (Weekly Health)
#   tools/ops/enable-security.sh --markdown      # Tabelle für SECURITY_BASELINE.md
#   tools/ops/enable-security.sh --repo owner/name [--repo ...]
#
# Öffentliche Repositories:
#   Dependabot-Warnungen, Dependabot-Sicherheitsupdates, Secret Scanning,
#   Secret-Scanning-Push-Schutz und CodeQL im Standard-Setup.
# Private Repositories:
#   Dependabot-Warnungen/-Sicherheitsupdates sowie Prüfung auf einen
#   gitleaks-PR-Workflow und Dependabot-/Renovate-Versionsupdates. Die
#   Workflow-/Konfigurationsdateien werden NICHT aus der Control Plane
#   geschrieben; Vorlagen liegen unter tools/ops/templates/.
#
# Das Skript ist idempotent: Es schreibt nur, wenn der Ist-Zustand vom
# Soll-Zustand abweicht. Es gibt niemals Token-Werte aus. Fehlt ein Secret
# oder ein Recht, wird das je Repository als Fehler gemeldet; andere
# Repositories werden weiter geprüft.
#
# Benötigt: gh CLI, authentifiziert mit Admin-Rechten auf den Ziel-Repos
# (GH_TOKEN/GITHUB_TOKEN oder gh auth login). Scope: Registry plus
# config/security-baseline.json.
#
# Exitcodes: 0 = alles in Ordnung, 1 = Abweichung oder Fehler,
#            2 = Aufruf-, Konfigurations- oder Authentifizierungsfehler.
set -uo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
REGISTRY="$ROOT/registry/projects.json"
CONFIG="$ROOT/config/security-baseline.json"

MODE="apply"
FORMAT="text"
PUSH_PROTECTION=1
REPOS=()

GITLEAKS_PATHS=(
  ".github/workflows/gitleaks.yml"
  ".github/workflows/gitleaks.yaml"
)
DEPENDENCY_UPDATE_PATHS=(
  ".github/dependabot.yml"
  ".github/dependabot.yaml"
  "renovate.json"
  "renovate.json5"
  ".github/renovate.json"
  ".github/renovate.json5"
  ".renovaterc"
  ".renovaterc.json"
)

usage() {
  cat <<'EOF'
Sicherheitsbaseline der KUEPER-Repositories (ECO-OPS-20261028-security-baseline)

Aufruf:
  tools/ops/enable-security.sh [--check] [--json|--markdown] [--repo OWNER/NAME ...]

Optionen:
  --check               Nur prüfen, nichts ändern. Exit 1 bei Abweichung.
  --apply               Soll-Zustand anwenden (Standard).
  --json                Ergebnis als JSON ausgeben.
  --markdown            Ergebnis als Markdown-Tabelle ausgeben.
  --no-push-protection  Secret-Scanning-Push-Schutz nicht aktivieren/prüfen.
  --repo OWNER/NAME     Nur dieses Repository prüfen (mehrfach möglich).
  -h, --help            Diese Hilfe.

Scope ohne --repo: alle aktivierten GitHub-Projekte aus registry/projects.json
plus extra_repositories aus config/security-baseline.json.

Öffentliche Repos: Dependabot-Alerts, Dependabot-Sicherheitsupdates,
Secret Scanning, Push-Schutz und CodeQL-Standard-Setup.
Private Repos: Dependabot-Alerts/-Sicherheitsupdates sowie Prüfung auf
gitleaks-Workflow und Dependabot-/Renovate-Versionsupdates.

Das Skript schreibt keine Dateien in Ziel-Repositories.
EOF
}

log() {
  [ "$FORMAT" = "text" ] && printf '%s\n' "$*" >&2
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --check|--dry-run) MODE="check" ;;
    --apply) MODE="apply" ;;
    --json) FORMAT="json" ;;
    --markdown) FORMAT="markdown" ;;
    --no-push-protection) PUSH_PROTECTION=0 ;;
    --repo)
      [ "$#" -ge 2 ] || { printf '%s\n' "--repo erwartet OWNER/NAME" >&2; exit 2; }
      REPOS+=("$2")
      shift
      ;;
    --repo=*) REPOS+=("${1#*=}") ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unbekannte Option: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

if ! command -v gh >/dev/null 2>&1; then
  printf '%s\n' "gh CLI nicht gefunden. Siehe https://cli.github.com/." >&2
  exit 2
fi

if [ -z "${GH_TOKEN:-}" ] && [ -z "${GITHUB_TOKEN:-}" ]; then
  if ! gh auth status >/dev/null 2>&1; then
    printf '%s\n' "gh ist nicht authentifiziert. GH_TOKEN/GITHUB_TOKEN setzen oder 'gh auth login' ausführen." >&2
    exit 2
  fi
fi

if [ ! -r "$REGISTRY" ]; then
  printf 'Registry nicht lesbar: %s\n' "$REGISTRY" >&2
  exit 2
fi
if [ ! -r "$CONFIG" ]; then
  printf 'Security-Konfiguration nicht lesbar: %s\n' "$CONFIG" >&2
  exit 2
fi

if [ "${#REPOS[@]}" -gt 0 ]; then
  mapfile -t SCOPE < <(printf '%s\n' "${REPOS[@]}" | sort -u)
else
  mapfile -t SCOPE < <(python3 - "$REGISTRY" "$CONFIG" <<'PY'
import json
import sys

registry_path, config_path = sys.argv[1], sys.argv[2]
with open(registry_path, encoding="utf-8") as fh:
    registry = json.load(fh)
with open(config_path, encoding="utf-8") as fh:
    config = json.load(fh)

repos = []
seen = set()
for project in registry.get("projects", []):
    repository = project.get("repository")
    if (
        project.get("enabled", True)
        and project.get("provider") == "github"
        and repository
        and repository not in seen
    ):
        seen.add(repository)
        repos.append(repository)
for repository in config.get("extra_repositories", []):
    if repository and repository not in seen:
        seen.add(repository)
        repos.append(repository)
for repository in config.get("excluded_repositories", []):
    if repository in seen:
        seen.remove(repository)
        repos.remove(repository)

for repository in sorted(repos):
    print(repository)
PY
)
fi

if [ "${#SCOPE[@]}" -eq 0 ]; then
  printf '%s\n' "Keine Repositories im Scope." >&2
  exit 2
fi

for repo in "${SCOPE[@]}"; do
  if ! [[ "$repo" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]]; then
    printf 'Ungültiger Repository-Name: %s\n' "$repo" >&2
    exit 2
  fi
done

RECORDS="$(mktemp)"
trap 'rm -f "$RECORDS"' EXIT

# ---------------------------------------------------------------------------
# GitHub-Aufrufe
# ---------------------------------------------------------------------------

GH_STATUS=""
GH_BODY=""

# Ruft `gh api` auf und legt HTTP-Status sowie Antworttext in GH_STATUS/GH_BODY
# ab. gh gibt bei 4xx/5xx `gh: ... (HTTP NNN)` auf stderr aus; beides wird
# zusammengeführt, damit die Meldung als Detail erhalten bleibt.
gh_api_capture() {
  local out rc
  out="$(gh api "$@" 2>&1)"
  rc=$?
  GH_BODY="$out"
  if [ "$rc" -eq 0 ]; then
    GH_STATUS="200"
    return 0
  fi
  if [[ "$out" =~ \(HTTP\ ([0-9]{3})\) ]]; then
    GH_STATUS="${BASH_REMATCH[1]}"
  else
    GH_STATUS="000"
  fi
  return 1
}

json_value() {
  local path="$1"
  python3 -c '
import json
import sys

path = sys.argv[1].split(".") if sys.argv[1] else []
try:
    value = json.load(sys.stdin)
except Exception:
    sys.exit(3)
for key in path:
    if isinstance(value, dict) and key in value:
        value = value[key]
    else:
        sys.exit(4)
if value is True:
    print("true")
elif value is False:
    print("false")
elif value is None:
    print("null")
elif isinstance(value, (dict, list)):
    print(json.dumps(value, ensure_ascii=False, separators=(",", ":")))
else:
    print(value)
' "$path"
}

clean_detail() {
  local text="${1:-}"
  text="${text//$'\t'/ }"
  text="${text//$'\n'/ }"
  text="${text//$'\r'/ }"
  printf '%s' "${text:0:240}"
}

META_PRIVATE=""
META_SECRET=""
META_PUSH=""

read_repo_meta() {
  local repo="$1"
  gh_api_capture "repos/$repo" || return 1
  META_PRIVATE="$(printf '%s' "$GH_BODY" | json_value private)"
  META_SECRET="$(printf '%s' "$GH_BODY" | json_value 'security_and_analysis.secret_scanning.status')"
  META_PUSH="$(printf '%s' "$GH_BODY" | json_value 'security_and_analysis.secret_scanning_push_protection.status')"
  return 0
}

# ---------------------------------------------------------------------------
# Einzelne Kontrollen. Jede Funktion setzt <prefix>_state und <prefix>_detail.
# ---------------------------------------------------------------------------

da_state=""; da_detail=""
ensure_dependabot_alerts() {
  local repo="$1"
  da_state=""; da_detail=""
  gh_api_capture "repos/$repo/vulnerability-alerts"
  case "$GH_STATUS" in
    200|204) da_state="enabled"; return 0 ;;
    404) da_state="disabled"; da_detail="nicht aktiviert" ;;
    *) da_state="error"; da_detail="GET HTTP $GH_STATUS: $GH_BODY"; return 0 ;;
  esac
  if [ "$MODE" = "apply" ]; then
    gh_api_capture --method PUT "repos/$repo/vulnerability-alerts"
    case "$GH_STATUS" in
      200|204) da_state="enabled"; da_detail="aktiviert" ;;
      *) da_state="error"; da_detail="PUT HTTP $GH_STATUS: $GH_BODY" ;;
    esac
  fi
}

su_state=""; su_detail=""
ensure_security_updates() {
  local repo="$1" enabled
  su_state=""; su_detail=""
  gh_api_capture "repos/$repo/automated-security-fixes"
  if [ "$GH_STATUS" = "200" ]; then
    enabled="$(printf '%s' "$GH_BODY" | json_value enabled)"
    case "$enabled" in
      true) su_state="enabled"; return 0 ;;
      false) su_state="disabled"; su_detail="nicht aktiviert" ;;
      *) su_state="unknown"; su_detail="Antwort nicht lesbar"; return 0 ;;
    esac
  elif [ "$GH_STATUS" = "404" ]; then
    su_state="disabled"; su_detail="nicht aktiviert oder nicht verfügbar"
  else
    su_state="error"; su_detail="GET HTTP $GH_STATUS: $GH_BODY"
    return 0
  fi
  if [ "$MODE" = "apply" ]; then
    gh_api_capture --method PUT "repos/$repo/automated-security-fixes"
    case "$GH_STATUS" in
      200|204) su_state="enabled"; su_detail="aktiviert" ;;
      *) su_state="error"; su_detail="PUT HTTP $GH_STATUS: $GH_BODY" ;;
    esac
  fi
}

ss_state=""; ss_detail=""
ensure_secret_scanning() {
  local repo="$1" current="$2"
  ss_state=""; ss_detail=""
  case "$current" in
    enabled)
      ss_state="enabled"
      return 0
      ;;
    disabled)
      ss_state="disabled"; ss_detail="nicht aktiviert"
      ;;
    ""|null)
      ss_state="unknown"
      ss_detail="Sicherheitsanalyse nicht sichtbar (Admin-Rechte erforderlich?)"
      return 0
      ;;
    *)
      ss_state="unknown"; ss_detail="Status $current"
      return 0
      ;;
  esac
  if [ "$MODE" = "apply" ]; then
    gh_api_capture --method PATCH "repos/$repo" --input - <<'JSON'
{"security_and_analysis":{"secret_scanning":{"status":"enabled"}}}
JSON
    case "$GH_STATUS" in
      200|202|204)
        if read_repo_meta "$repo" && [ "$META_SECRET" = "enabled" ]; then
          ss_state="enabled"; ss_detail="aktiviert"
        else
          ss_state="error"
          ss_detail="PATCH erfolgreich, Status weiterhin ${META_SECRET:-unbekannt}"
        fi
        ;;
      *)
        ss_state="error"; ss_detail="PATCH HTTP $GH_STATUS: $GH_BODY"
        ;;
    esac
  fi
}

pp_state=""; pp_detail=""
ensure_push_protection() {
  local repo="$1" current="$2"
  pp_state=""; pp_detail=""
  if [ "$PUSH_PROTECTION" -eq 0 ]; then
    pp_state="skipped"; pp_detail="per --no-push-protection nicht geprüft"
    return 0
  fi
  case "$current" in
    enabled)
      pp_state="enabled"
      return 0
      ;;
    disabled)
      pp_state="disabled"; pp_detail="nicht aktiviert"
      ;;
    ""|null)
      pp_state="unknown"
      pp_detail="Push-Schutz nicht sichtbar (Admin-Rechte erforderlich?)"
      return 0
      ;;
    *)
      pp_state="unknown"; pp_detail="Status $current"
      return 0
      ;;
  esac
  if [ "$MODE" = "apply" ]; then
    gh_api_capture --method PATCH "repos/$repo" --input - <<'JSON'
{"security_and_analysis":{"secret_scanning_push_protection":{"status":"enabled"}}}
JSON
    case "$GH_STATUS" in
      200|202|204)
        if read_repo_meta "$repo" && [ "$META_PUSH" = "enabled" ]; then
          pp_state="enabled"; pp_detail="aktiviert"
        else
          pp_state="error"
          pp_detail="PATCH erfolgreich, Status weiterhin ${META_PUSH:-unbekannt}"
        fi
        ;;
      *)
        pp_state="error"; pp_detail="PATCH HTTP $GH_STATUS: $GH_BODY"
        ;;
    esac
  fi
}

cq_state=""; cq_detail=""
ensure_codeql() {
  local repo="$1" state suite
  cq_state=""; cq_detail=""
  gh_api_capture "repos/$repo/code-scanning/default-setup"
  case "$GH_STATUS" in
    200)
      state="$(printf '%s' "$GH_BODY" | json_value state)"
      case "$state" in
        configured)
          cq_state="enabled"
          suite="$(printf '%s' "$GH_BODY" | json_value query_suite)"
          if [ -n "$suite" ] && [ "$suite" != "null" ]; then
            cq_detail="Suite $suite"
          fi
          return 0
          ;;
        not-configured)
          cq_state="disabled"; cq_detail="Standard-Setup nicht eingerichtet"
          ;;
        *)
          cq_state="unknown"; cq_detail="Status ${state:-unbekannt}"
          return 0
          ;;
      esac
      ;;
    404)
      # 404 belegt kein fehlendes Standard-Setup: GitHub antwortet bei
      # vorhandenem Endpunkt mit 200/not-configured und bei fehlenden
      # Sprachen mit 422. Ein 404 kann auf fehlende Rechte oder ein
      # API-Problem hindeuten. Im Check-Modus bleibt der Zustand deshalb
      # unknown; im Apply-Modus wird der PATCH dennoch versucht.
      cq_state="unknown"
      cq_detail="GET HTTP 404: $GH_BODY (CodeQL-Endpunkt nicht verfügbar; Rechte oder API-Problem?)"
      ;;
    *)
      cq_state="error"; cq_detail="GET HTTP $GH_STATUS: $GH_BODY"
      return 0
      ;;
  esac
  if [ "$MODE" = "apply" ]; then
    gh_api_capture --method PATCH "repos/$repo/code-scanning/default-setup" --input - <<'JSON'
{"state":"configured"}
JSON
    case "$GH_STATUS" in
      200|202|204)
        # Der PATCH ist angenommen. Die erste Analyse läuft asynchron; ein
        # sofortiger GET darf deshalb nicht als Fehler gewertet werden.
        gh_api_capture "repos/$repo/code-scanning/default-setup"
        if [ "$GH_STATUS" = "200" ]; then
          state="$(printf '%s' "$GH_BODY" | json_value state)"
          if [ "$state" = "configured" ]; then
            cq_state="enabled"; cq_detail="Standard-Setup aktiviert"
          else
            cq_state="enabled"
            cq_detail="PATCH angenommen, Status ${state:-unbekannt} (erste Analyse läuft ggf. noch)"
          fi
        else
          cq_state="enabled"
          cq_detail="PATCH angenommen, Verifikation HTTP $GH_STATUS"
        fi
        ;;
      409)
        cq_state="advanced"; cq_detail="Advanced Setup bereits aktiv"
        ;;
      422)
        if printf '%s' "$GH_BODY" | grep -qiE 'language|sprache'; then
          cq_state="not_applicable"; cq_detail="keine analysierbaren Sprachen"
        else
          cq_state="error"; cq_detail="PATCH HTTP 422: $GH_BODY"
        fi
        ;;
      *)
        cq_state="error"; cq_detail="PATCH HTTP $GH_STATUS: $GH_BODY"
        ;;
    esac
  fi
}

FILE_PATH=""
FILE_ERROR=""
find_first_file() {
  local repo="$1" path
  shift
  FILE_PATH=""; FILE_ERROR=""
  for path in "$@"; do
    gh_api_capture "repos/$repo/contents/$path"
    case "$GH_STATUS" in
      200) FILE_PATH="$path"; return 0 ;;
      404) ;;
      *) FILE_ERROR="HTTP $GH_STATUS: $GH_BODY"; return 2 ;;
    esac
  done
  return 1
}

gl_state=""; gl_detail=""
check_gitleaks() {
  local repo="$1" rc
  find_first_file "$repo" "${GITLEAKS_PATHS[@]}"
  rc=$?
  case "$rc" in
    0) gl_state="present"; gl_detail="$FILE_PATH" ;;
    1) gl_state="missing"; gl_detail="kein gitleaks-PR-Workflow (Vorlage tools/ops/templates/gitleaks.yml)" ;;
    *) gl_state="error"; gl_detail="Inhaltsprüfung: $FILE_ERROR" ;;
  esac
}

du_state=""; du_detail=""
check_dependency_updates() {
  local repo="$1" rc
  find_first_file "$repo" "${DEPENDENCY_UPDATE_PATHS[@]}"
  rc=$?
  case "$rc" in
    0) du_state="present"; du_detail="$FILE_PATH" ;;
    1) du_state="missing"; du_detail="keine Dependabot-/Renovate-Konfiguration (Vorlage tools/ops/templates/dependabot.yml)" ;;
    *) du_state="error"; du_detail="Inhaltsprüfung: $FILE_ERROR" ;;
  esac
}

result_for_repo() {
  local visibility="$1" state
  if [ "$visibility" = "public" ]; then
    for state in "$da_state" "$su_state" "$ss_state" "$pp_state" "$cq_state"; do
      [ "$state" = "error" ] && { printf '%s\n' "error"; return; }
    done
    for state in "$da_state" "$su_state" "$ss_state" "$pp_state" "$cq_state"; do
      case "$state" in
        disabled|missing|unknown) printf '%s\n' "action_required"; return ;;
      esac
    done
  else
    for state in "$da_state" "$su_state" "$gl_state" "$du_state"; do
      [ "$state" = "error" ] && { printf '%s\n' "error"; return; }
    done
    for state in "$da_state" "$su_state" "$gl_state" "$du_state"; do
      case "$state" in
        disabled|missing|unknown) printf '%s\n' "action_required"; return ;;
      esac
    done
  fi
  printf '%s\n' "ok"
}

record_row() {
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$1" "$2" \
    "$3" "$(clean_detail "$4")" \
    "$5" "$(clean_detail "$6")" \
    "$7" "$(clean_detail "$8")" \
    "$9" "$(clean_detail "${10}")" \
    "${11}" "$(clean_detail "${12}")" \
    "${13}" "$(clean_detail "${14}")" \
    "${15}" "$(clean_detail "${16}")" \
    "${17}" >> "$RECORDS"
}

record_unreachable() {
  local repo="$1" detail="$2"
  record_row "$repo" "unknown" \
    "error" "$detail" \
    "unknown" "" \
    "unknown" "" \
    "unknown" "" \
    "unknown" "" \
    "unknown" "" \
    "unknown" "" \
    "error"
}

# ---------------------------------------------------------------------------
# Hauptschleife
# ---------------------------------------------------------------------------

for repo in "${SCOPE[@]}"; do
  log "prüfe $repo"
  if ! read_repo_meta "$repo"; then
    record_unreachable "$repo" "Metadaten: HTTP $GH_STATUS: $GH_BODY"
    continue
  fi

  case "$META_PRIVATE" in
    true) visibility="private" ;;
    false) visibility="public" ;;
    *)
      record_unreachable "$repo" "Sichtbarkeit nicht lesbar (HTTP $GH_STATUS)"
      continue
      ;;
  esac

  if [ "$visibility" = "private" ]; then
    ensure_dependabot_alerts "$repo"
    ensure_security_updates "$repo"
    check_gitleaks "$repo"
    check_dependency_updates "$repo"
    ss_state="not_applicable"; ss_detail=""
    pp_state="not_applicable"; pp_detail=""
    cq_state="not_applicable"; cq_detail=""
  else
    ensure_dependabot_alerts "$repo"
    ensure_security_updates "$repo"
    ensure_secret_scanning "$repo" "$META_SECRET"
    ensure_push_protection "$repo" "$META_PUSH"
    ensure_codeql "$repo"
    gl_state="not_applicable"; gl_detail=""
    du_state="not_applicable"; du_detail=""
  fi

  record_row "$repo" "$visibility" \
    "$da_state" "$da_detail" \
    "$su_state" "$su_detail" \
    "$ss_state" "$ss_detail" \
    "$pp_state" "$pp_detail" \
    "$cq_state" "$cq_detail" \
    "$gl_state" "$gl_detail" \
    "$du_state" "$du_detail" \
    "$(result_for_repo "$visibility")"
done

python3 - "$MODE" "$FORMAT" "$RECORDS" <<'PY'
import json
import sys
from collections import Counter
from datetime import datetime, timezone

mode, output_format, records_path = sys.argv[1], sys.argv[2], sys.argv[3]

FIELDS = [
    "repository", "visibility",
    "dependabot_alerts", "dependabot_alerts_detail",
    "dependabot_security_updates", "dependabot_security_updates_detail",
    "secret_scanning", "secret_scanning_detail",
    "push_protection", "push_protection_detail",
    "codeql_default_setup", "codeql_default_setup_detail",
    "gitleaks_workflow", "gitleaks_workflow_detail",
    "dependency_updates", "dependency_updates_detail",
    "result",
]

CONTROLS = [
    ("dependabot_alerts", "Dependabot-Alerts"),
    ("dependabot_security_updates", "Sicherheitsupdates"),
    ("secret_scanning", "Secret-Scanning"),
    ("push_protection", "Push-Schutz"),
    ("codeql_default_setup", "CodeQL"),
    ("gitleaks_workflow", "gitleaks"),
    ("dependency_updates", "Versionsupdates"),
]
PUBLIC_ONLY = {"secret_scanning", "push_protection", "codeql_default_setup"}
PRIVATE_ONLY = {"gitleaks_workflow", "dependency_updates"}

rows = []
with open(records_path, encoding="utf-8") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) != len(FIELDS):
            continue
        rows.append(dict(zip(FIELDS, parts)))

visibility_order = {"public": 0, "private": 1, "unknown": 2}
rows.sort(key=lambda row: (visibility_order.get(row["visibility"], 3), row["repository"]))
counts = Counter(row["result"] for row in rows)
public = sum(1 for row in rows if row["visibility"] == "public")
private = sum(1 for row in rows if row["visibility"] == "private")
unknown = len(rows) - public - private


def state_text(row, control):
    state = row[control] or "unknown"
    detail = row[control + "_detail"]
    if detail and state not in ("enabled", "present"):
        return f"{state} ({detail})"
    return state


def control_applies(row, control):
    if row["visibility"] == "public":
        return control not in PRIVATE_ONLY
    if row["visibility"] == "private":
        return control not in PUBLIC_ONLY
    return True


def render_text():
    print(f"KUEPER Security Baseline — Modus: {mode}")
    for row in rows:
        print(f"{row['result']:16} {row['visibility']:8} {row['repository']}")
        parts = []
        for control, _label in CONTROLS:
            if not control_applies(row, control):
                continue
            parts.append(f"{control}={state_text(row, control)}")
        print("    " + "  ".join(parts))
    noun = "Repository" if len(rows) == 1 else "Repositories"
    print(
        f"\n{len(rows)} {noun}: {public} öffentlich, {private} privat, "
        f"{unknown} unbekannt · {counts.get('ok', 0)} ok · "
        f"{counts.get('action_required', 0)} Handlung nötig · "
        f"{counts.get('error', 0)} Fehler"
    )


def render_markdown():
    header = [
        "Repository", "Sichtbarkeit", "Dependabot-Alerts", "Sicherheitsupdates",
        "Secret-Scanning", "Push-Schutz", "CodeQL", "gitleaks",
        "Versionsupdates", "Ergebnis",
    ]
    print("<!-- erzeugt von tools/ops/enable-security.sh --markdown, "
          + datetime.now(timezone.utc).replace(microsecond=0).isoformat() + " -->")
    print("| " + " | ".join(header) + " |")
    print("|" + "|".join(["---"] * len(header)) + "|")
    for row in rows:
        values = [row["repository"], row["visibility"]]
        for control, _label in CONTROLS:
            if control_applies(row, control):
                value = state_text(row, control).replace("|", "\\|")
            else:
                value = "–"
            values.append(value)
        values.append(row["result"])
        print("| " + " | ".join(values) + " |")


def render_json():
    repositories = []
    for row in rows:
        controls = {}
        for control, _label in CONTROLS:
            controls[control] = {
                "state": row[control] or "unknown",
                "detail": row[control + "_detail"],
            }
        repositories.append({
            "repository": row["repository"],
            "visibility": row["visibility"],
            "result": row["result"],
            "controls": controls,
        })
    document = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "mode": mode,
        "repositories": repositories,
        "summary": {
            "repositories": len(rows),
            "public": public,
            "private": private,
            "unknown": unknown,
            "ok": counts.get("ok", 0),
            "action_required": counts.get("action_required", 0),
            "errors": counts.get("error", 0),
        },
    }
    json.dump(document, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if output_format == "json":
    render_json()
elif output_format == "markdown":
    render_markdown()
else:
    render_text()
PY

problems="$(awk -F'\t' '$17 != "ok" {count++} END {print count + 0}' "$RECORDS")"
if [ "$problems" -gt 0 ]; then
  exit 1
fi
exit 0
