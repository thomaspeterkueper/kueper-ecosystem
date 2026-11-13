#!/usr/bin/env python3
"""Credential-Check der Control Plane (ECO-OPS-20261028-secret-health).

Prüft die Secrets aus docs/operations/SECRETS_INVENTORY.md mit je einem
lesenden Aufruf und gibt nur Status, Ablaufdatum und Restguthaben aus –
niemals Werte. Nur stdlib.

    python3 tools/ops/credential_health.py [--json] [--alert-file PFAD]

Umgebungsvariablen (fehlende werden als ``missing`` gemeldet, nicht als Fehler):
    KUEPER_BOT_TOKEN, KUEPER_WORKFLOW_TOKEN   GitHub-PATs
    DEEPSEEK_API_KEY                          DeepSeek
    AI_GATEWAY_API_KEY                        Vercel AI Gateway
    SUPABASE_URL + SUPABASE_SECRET_KEY        Supabase
Schwellwerte:
    KUEPER_CREDENTIAL_WARN_DAYS      (Standard 14)
    KUEPER_DEEPSEEK_MIN_BALANCE      (Standard 2.0, Kontowährung)
    KUEPER_GATEWAY_MIN_BALANCE       (Standard 2.0, USD)

Exit 1, wenn mindestens ein Check ``error``, ``expiring`` oder ``low`` meldet.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

OK = "ok"
MISSING = "missing"
ERROR = "error"
EXPIRING = "expiring"
LOW = "low"
UNKNOWN = "unknown"
PROBLEM_STATES = {ERROR, EXPIRING, LOW}

ALERT_TASK_ID = "ECO-OPS-credential-alert"


@dataclass
class Result:
    name: str
    status: str
    detail: str = ""
    expires_at: str | None = None
    balance: str | None = None


# --------------------------------------------------------------------------
# Auswertelogik (rein, ohne Netz – getestet in test_credential_health.py)
# --------------------------------------------------------------------------

def parse_github_expiration(header: str | None) -> datetime | None:
    """Header ``github-authentication-token-expiration`` lesen.

    GitHub liefert z. B. ``2026-12-01 10:00:00 UTC`` oder ``2026-12-01 10:00:00 +0100``.
    """
    if not header:
        return None
    text = header.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S %Z", "%Y-%m-%d %H:%M:%S %z"):
        try:
            parsed = datetime.strptime(text, fmt)
        except ValueError:
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    return None


def evaluate_github(name: str, status_code: int | None, expiration_header: str | None,
                    now: datetime, warn_days: int) -> Result:
    if status_code is None:
        return Result(name, UNKNOWN, "keine Antwort von GitHub")
    if status_code == 401:
        return Result(name, ERROR, "401 – Token ungültig oder abgelaufen")
    if status_code == 403:
        return Result(name, ERROR, "403 – Token ohne Zugriff auf kueper-ecosystem")
    if status_code != 200:
        return Result(name, UNKNOWN, f"HTTP {status_code}")
    expires = parse_github_expiration(expiration_header)
    if expires is None:
        return Result(name, OK, "gültig, kein Ablaufdatum gemeldet")
    days = (expires - now).total_seconds() / 86400
    iso = expires.astimezone(timezone.utc).date().isoformat()
    if days <= 0:
        return Result(name, ERROR, "abgelaufen", expires_at=iso)
    if days < warn_days:
        return Result(name, EXPIRING, f"läuft in {int(days)} Tagen ab", expires_at=iso)
    return Result(name, OK, "gültig", expires_at=iso)


def _to_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def evaluate_deepseek(status_code: int | None, body: dict | None, min_balance: float) -> Result:
    name = "DEEPSEEK_API_KEY"
    if status_code is None:
        return Result(name, UNKNOWN, "keine Antwort von DeepSeek")
    if status_code == 401:
        return Result(name, ERROR, "401 – Schlüssel ungültig")
    if status_code == 402:
        return Result(name, LOW, "402 – Guthaben erschöpft", balance="0")
    if status_code != 200 or not isinstance(body, dict):
        return Result(name, UNKNOWN, f"HTTP {status_code}")
    infos = body.get("balance_infos") or []
    balances = [(i.get("currency", "?"), _to_float(i.get("total_balance"))) for i in infos if isinstance(i, dict)]
    shown = ", ".join(f"{amount:.2f} {cur}" for cur, amount in balances if amount is not None) or None
    if body.get("is_available") is False:
        return Result(name, LOW, "Konto meldet is_available=false", balance=shown)
    highest = max((amount for _, amount in balances if amount is not None), default=None)
    if highest is None:
        return Result(name, UNKNOWN, "Guthaben nicht lesbar")
    if highest < min_balance:
        return Result(name, LOW, f"Guthaben unter {min_balance:.2f}", balance=shown)
    return Result(name, OK, "Guthaben ausreichend", balance=shown)


def evaluate_gateway(status_code: int | None, body: dict | None, min_balance: float) -> Result:
    name = "AI_GATEWAY_API_KEY"
    if status_code is None:
        return Result(name, UNKNOWN, "keine Antwort vom AI Gateway")
    if status_code in (401, 403):
        return Result(name, ERROR, f"{status_code} – Schlüssel ungültig oder ohne Zugriff")
    if status_code != 200 or not isinstance(body, dict):
        return Result(name, UNKNOWN, f"HTTP {status_code}")
    balance = _to_float(body.get("balance"))
    if balance is None:
        return Result(name, OK, "Schlüssel gültig, Guthaben nicht lesbar")
    shown = f"{balance:.2f} USD"
    if balance < min_balance:
        return Result(name, LOW, f"Guthaben unter {min_balance:.2f} USD", balance=shown)
    return Result(name, OK, "Guthaben ausreichend", balance=shown)


def evaluate_supabase(status_code: int | None) -> Result:
    name = "SUPABASE_SECRET_KEY"
    if status_code is None:
        return Result(name, UNKNOWN, "keine Antwort von Supabase")
    if status_code in (401, 403):
        return Result(name, ERROR, f"{status_code} – Schlüssel ungültig")
    if 200 <= status_code < 300:
        return Result(name, OK, "Lesezugriff möglich")
    return Result(name, UNKNOWN, f"HTTP {status_code}")


def has_problem(results: list[Result]) -> bool:
    return any(r.status in PROBLEM_STATES for r in results)


def render_alert(results: list[Result], today: str) -> str:
    """Inhalt der einen rollierenden Alert-Task. Enthält keine Secret-Werte."""
    rows = "\n".join(
        f"| `{r.name}` | {r.status} | {r.detail} | {r.expires_at or '–'} | {r.balance or '–'} |"
        for r in results if r.status in PROBLEM_STATES
    )
    return (
        "---\n"
        f"id: {ALERT_TASK_ID}\n"
        "title: Credential-Warnung – Secret ungültig, läuft ab oder Guthaben niedrig\n"
        "status: open\n"
        f"created: {today}\n"
        "requested_by: tools/ops/credential_health.py\n"
        "priority: high\n"
        "type: operations / credentials\n"
        "---\n\n"
        f"# {ALERT_TASK_ID} — Credential-Warnung\n\n"
        f"Letzte Prüfung: {today}. Diese Datei wird bei jedem Lauf überschrieben, nicht neu angelegt.\n\n"
        "| Secret | Status | Befund | Ablauf | Guthaben |\n"
        "| --- | --- | --- | --- | --- |\n"
        f"{rows}\n\n"
        "## Owner-Handlung\n\n"
        "Secret im jeweiligen Anbieter-Konto erneuern oder Guthaben aufladen, dann in GitHub "
        "unter Settings → Secrets aktualisieren. Siehe `docs/operations/SECRETS_INVENTORY.md`.\n"
    )


# --------------------------------------------------------------------------
# Netzaufrufe
# --------------------------------------------------------------------------

def _request(url: str, headers: dict[str, str], timeout: int = 20):
    req = urllib.request.Request(url, headers={"User-Agent": "kueper-credential-health", **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return resp.status, dict(resp.headers), raw
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers or {}), b""
    except (urllib.error.URLError, TimeoutError, OSError):
        return None, {}, b""


def _json(raw: bytes):
    try:
        return json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None


def _header(headers: dict[str, str], key: str) -> str | None:
    for k, v in headers.items():
        if k.lower() == key.lower():
            return v
    return None


def run_checks(env: dict[str, str], now: datetime) -> list[Result]:
    warn_days = int(env.get("KUEPER_CREDENTIAL_WARN_DAYS", "14"))
    results: list[Result] = []

    for name in ("KUEPER_BOT_TOKEN", "KUEPER_WORKFLOW_TOKEN"):
        token = env.get(name)
        if not token:
            results.append(Result(name, MISSING, "nicht gesetzt"))
            continue
        status, headers, _ = _request(
            "https://api.github.com/repos/thomaspeterkueper/kueper-ecosystem",
            {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        )
        results.append(evaluate_github(name, status, _header(headers, "github-authentication-token-expiration"), now, warn_days))

    key = env.get("DEEPSEEK_API_KEY")
    if key:
        status, _, raw = _request("https://api.deepseek.com/user/balance",
                                  {"Authorization": f"Bearer {key}", "Accept": "application/json"})
        results.append(evaluate_deepseek(status, _json(raw), float(env.get("KUEPER_DEEPSEEK_MIN_BALANCE", "2"))))
    else:
        results.append(Result("DEEPSEEK_API_KEY", MISSING, "nicht gesetzt"))

    key = env.get("AI_GATEWAY_API_KEY")
    if key:
        status, _, raw = _request("https://ai-gateway.vercel.sh/v1/credits",
                                  {"Authorization": f"Bearer {key}", "Accept": "application/json"})
        results.append(evaluate_gateway(status, _json(raw), float(env.get("KUEPER_GATEWAY_MIN_BALANCE", "2"))))
    else:
        results.append(Result("AI_GATEWAY_API_KEY", MISSING, "nicht gesetzt"))

    url, key = env.get("SUPABASE_URL"), env.get("SUPABASE_SECRET_KEY")
    if url and key:
        status, _, _ = _request(url.rstrip("/") + "/rest/v1/", {"apikey": key, "Accept": "application/json"})
        results.append(evaluate_supabase(status))
    else:
        results.append(Result("SUPABASE_SECRET_KEY", MISSING, "SUPABASE_URL oder SUPABASE_SECRET_KEY nicht gesetzt"))

    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="Ergebnis als JSON ausgeben")
    parser.add_argument("--alert-file", help="rollierende Alert-Task bei Problemen schreiben/überschreiben")
    args = parser.parse_args(argv)

    now = datetime.now(timezone.utc)
    results = run_checks(dict(os.environ), now)

    if args.json:
        print(json.dumps([asdict(r) for r in results], ensure_ascii=False, indent=2))
    else:
        for r in results:
            extra = " ".join(x for x in (f"Ablauf {r.expires_at}" if r.expires_at else "",
                                          f"Guthaben {r.balance}" if r.balance else "") if x)
            print(f"{r.status:9} {r.name:22} {r.detail} {extra}".rstrip())

    problem = has_problem(results)
    if problem and args.alert_file:
        with open(args.alert_file, "w", encoding="utf-8") as fh:
            fh.write(render_alert(results, now.date().isoformat()))
    return 1 if problem else 0


if __name__ == "__main__":
    sys.exit(main())
