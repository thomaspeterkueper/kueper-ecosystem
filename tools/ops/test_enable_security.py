"""Tests für tools/ops/enable-security.sh.

Ersetzt die gh-CLI durch ein zustandsbehaftetes Fake-Programm im PATH.
Dadurch werden HTTP-Aufrufe, Idempotenz und Fehlerbehandlung deterministisch
geprüft, ohne Netzwerk oder echte Tokens.
"""
from __future__ import annotations

import json
import os
import stat
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).with_name("enable-security.sh")
REGISTRY = ROOT / "registry" / "projects.json"
CONFIG = ROOT / "config" / "security-baseline.json"

PRIVATE_REPOS = {
    "thomaspeterkueper/kueper-knowledge-graph",
    "thomaspeterkueper/buecherwelten",
    "thomaspeterkueper/kueper-engineering",
    "thomaspeterkueper/kueper-products",
    "thomaspeterkueper/noxia-universe",
    "thomaspeterkueper/noxia-realtime",
}

FAKE_GH = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    \"\"\"Fake gh CLI für tools/ops/test_enable_security.py.\"\"\"
    import json
    import os
    import sys

    STATE_PATH = os.environ["FAKE_GH_STATE"]
    LOG_PATH = os.environ["FAKE_GH_LOG"]

    MESSAGES = {
        403: "Forbidden",
        404: "Not Found",
        409: "Conflict",
        422: "Validation Failed",
        500: "Internal Server Error",
    }

    def save(state):
        with open(STATE_PATH, "w", encoding="utf-8") as fh:
            json.dump(state, fh)

    def respond(status, body=None, message=None):
        if status >= 400:
            reason = message or MESSAGES.get(status, "Error")
            print("gh: %s (HTTP %s)" % (reason, status), file=sys.stderr)
            sys.exit(1)
        if body is not None:
            print(json.dumps(body, ensure_ascii=False))
        sys.exit(0)

    def fail_status(entry, route, method):
        failures = entry.get("fail", {})
        for key in (route + ":" + method, route, method + " " + route):
            if key in failures:
                return failures[key]
        return None

    def apply_failure(status):
        if isinstance(status, dict):
            respond(int(status.get("status", 500)), message=status.get("message"))
        respond(int(status))

    def repo_body(entry):
        body = {
            "private": bool(entry.get("private", False)),
            "default_branch": "main",
        }
        secret = entry.get("secret_scanning", "enabled")
        push = entry.get("push_protection", "enabled")
        if secret != "hidden" or push != "hidden":
            analysis = {}
            if secret != "hidden":
                analysis["secret_scanning"] = {"status": secret}
            if push != "hidden":
                analysis["secret_scanning_push_protection"] = {"status": push}
            body["security_and_analysis"] = analysis
        return body

    def main():
        args = sys.argv[1:]
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(args) + "\\n")

        if args[:2] == ["auth", "status"]:
            if os.environ.get("FAKE_GH_AUTH_OK") == "1":
                print("Logged in to github.com as fake")
                sys.exit(0)
            print("You are not logged into any GitHub hosts.", file=sys.stderr)
            sys.exit(1)

        if not args or args[0] != "api":
            print("gh: unsupported command", file=sys.stderr)
            sys.exit(1)

        method = "GET"
        path = None
        input_data = None
        i = 1
        while i < len(args):
            arg = args[i]
            if arg in ("--method", "-X"):
                method = args[i + 1].upper()
                i += 2
                continue
            if arg == "--input":
                if i + 1 < len(args) and args[i + 1] == "-":
                    input_data = sys.stdin.read()
                    i += 2
                    continue
                i += 2
                continue
            if arg in ("--include", "--silent", "--paginate"):
                i += 1
                continue
            if arg in ("--jq", "-q", "--template", "-t"):
                i += 2
                continue
            if arg.startswith("-"):
                i += 1
                continue
            path = arg
            i += 1

        if not path:
            respond(404)

        path = path.lstrip("/")
        if not path.startswith("repos/"):
            respond(404)

        parts = path[len("repos/"):].split("/")
        if len(parts) < 2:
            respond(404)
        repo = parts[0] + "/" + parts[1]
        route = "/".join(parts[2:])

        with open(STATE_PATH, encoding="utf-8") as fh:
            state = json.load(fh)
        entry = state.setdefault("repos", {}).setdefault(
            repo,
            {
                "private": False,
                "secret_scanning": "enabled",
                "push_protection": "enabled",
                "vulnerability_alerts": True,
                "security_updates": True,
                "codeql": "configured",
                "files": [],
            },
        )

        forced = fail_status(entry, route or "repo", method)
        if forced is not None:
            apply_failure(forced)

        if not route:
            if method == "GET":
                respond(200, repo_body(entry))
            if method == "PATCH":
                data = json.loads(input_data or "{}")
                analysis = data.get("security_and_analysis", {})
                if "secret_scanning" in analysis:
                    entry["secret_scanning"] = analysis["secret_scanning"]["status"]
                if "secret_scanning_push_protection" in analysis:
                    entry["push_protection"] = analysis["secret_scanning_push_protection"]["status"]
                save(state)
                respond(200, repo_body(entry))
            respond(404)

        if route == "vulnerability-alerts":
            if method == "GET":
                respond(204 if entry.get("vulnerability_alerts") else 404)
            if method == "PUT":
                entry["vulnerability_alerts"] = True
                save(state)
                respond(204)
            respond(404)

        if route == "automated-security-fixes":
            if method == "GET":
                respond(200, {"enabled": bool(entry.get("security_updates")), "paused": False})
            if method == "PUT":
                entry["security_updates"] = True
                save(state)
                respond(204)
            respond(404)

        if route == "code-scanning/default-setup":
            if method == "GET":
                state_name = entry.get("codeql", "not-configured")
                if state_name == "unavailable":
                    respond(404)
                respond(200, {
                    "state": "configured" if state_name == "configured" else "not-configured",
                    "query_suite": "default",
                    "languages": ["python"],
                })
            if method == "PATCH":
                entry["codeql"] = "configured"
                save(state)
                respond(200, {"state": "configured"})
            respond(404)

        if route.startswith("contents/"):
            wanted = route[len("contents/"):]
            if wanted in entry.get("files", []):
                respond(200, {"name": wanted.rsplit("/", 1)[-1], "path": wanted, "type": "file"})
            respond(404)

        respond(404)

    if __name__ == "__main__":
        main()
    """
)


def healthy_entry(private: bool) -> dict:
    entry = {
        "private": private,
        "secret_scanning": "enabled",
        "push_protection": "enabled",
        "vulnerability_alerts": True,
        "security_updates": True,
        "codeql": "configured",
        "files": [],
    }
    if private:
        entry["files"] = [
            ".github/workflows/gitleaks.yml",
            ".github/dependabot.yml",
        ]
    return entry


def scope_repositories() -> list[str]:
    with open(REGISTRY, encoding="utf-8") as fh:
        registry = json.load(fh)
    with open(CONFIG, encoding="utf-8") as fh:
        config = json.load(fh)
    repos = {
        project["repository"]
        for project in registry.get("projects", [])
        if project.get("enabled", True)
        and project.get("provider") == "github"
        and project.get("repository")
    }
    repos.update(config.get("extra_repositories", []))
    repos.difference_update(config.get("excluded_repositories", []))
    return sorted(repos)


class EnableSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fake_dir = Path(tempfile.mkdtemp(prefix="fake-gh-"))
        fake = cls.fake_dir / "gh"
        fake.write_text(FAKE_GH, encoding="utf-8")
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    @classmethod
    def tearDownClass(cls):
        for child in cls.fake_dir.iterdir():
            child.unlink()
        cls.fake_dir.rmdir()

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="security-test-"))
        self.state_path = self.tmp / "state.json"
        self.log_path = self.tmp / "calls.jsonl"
        self.log_path.touch()
        self.state = {"repos": {}}
        self.write_state()

    def tearDown(self):
        for child in self.tmp.iterdir():
            child.unlink()
        self.tmp.rmdir()

    def write_state(self):
        self.state_path.write_text(json.dumps(self.state), encoding="utf-8")

    def read_state(self):
        with open(self.state_path, encoding="utf-8") as fh:
            return json.load(fh)

    def calls(self) -> list[list[str]]:
        lines = self.log_path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines if line.strip()]

    def methods(self) -> list[str]:
        result = []
        for args in self.calls():
            method = "GET"
            for index, arg in enumerate(args):
                if arg == "--method" and index + 1 < len(args):
                    method = args[index + 1].upper()
            result.append(method)
        return result

    def run_script(self, args, auth_ok=True, token=True):
        env = {
            "PATH": str(self.fake_dir) + os.pathsep + os.environ.get("PATH", ""),
            "FAKE_GH_STATE": str(self.state_path),
            "FAKE_GH_LOG": str(self.log_path),
            "FAKE_GH_AUTH_OK": "1" if auth_ok else "0",
            "HOME": str(self.tmp),
        }
        if token:
            env["GH_TOKEN"] = "test-token"
        return subprocess.run(
            ["bash", str(SCRIPT), *args],
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )

    def json_result(self, result):
        return json.loads(result.stdout)

    # ------------------------------------------------------------------
    # Scope und Standardzustand
    # ------------------------------------------------------------------

    def test_default_scope_includes_extra_and_private_repos(self):
        for repo in scope_repositories():
            self.state["repos"][repo] = healthy_entry(repo in PRIVATE_REPOS)
        self.write_state()

        result = self.run_script(["--check", "--json"])
        self.assertEqual(result.returncode, 0, result.stderr)
        document = self.json_result(result)
        found = {row["repository"] for row in document["repositories"]}
        self.assertEqual(found, set(scope_repositories()))
        self.assertIn("thomaspeterkueper/noxia-realtime", found)
        self.assertEqual(document["summary"]["private"], len(PRIVATE_REPOS & set(scope_repositories())))
        self.assertTrue(all(row["result"] == "ok" for row in document["repositories"]))

    def test_healthy_public_repo_exits_zero(self):
        self.state["repos"]["acme/public"] = healthy_entry(False)
        self.write_state()
        result = self.run_script(["--check", "--repo", "acme/public"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("acme/public", result.stdout)
        self.assertIn("dependabot_alerts=enabled", result.stdout)
        self.assertEqual(self.methods(), ["GET"] * len(self.methods()))

    # ------------------------------------------------------------------
    # Anwenden und Idempotenz
    # ------------------------------------------------------------------

    def test_apply_enables_all_public_controls(self):
        self.state["repos"]["acme/public"] = {
            "private": False,
            "secret_scanning": "disabled",
            "push_protection": "disabled",
            "vulnerability_alerts": False,
            "security_updates": False,
            "codeql": "not-configured",
            "files": [],
        }
        self.write_state()

        result = self.run_script(["--repo", "acme/public"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        entry = self.read_state()["repos"]["acme/public"]
        self.assertTrue(entry["vulnerability_alerts"])
        self.assertTrue(entry["security_updates"])
        self.assertEqual(entry["secret_scanning"], "enabled")
        self.assertEqual(entry["push_protection"], "enabled")
        self.assertEqual(entry["codeql"], "configured")

        methods = self.methods()
        self.assertIn("PUT", methods)
        self.assertIn("PATCH", methods)

    def test_apply_is_idempotent(self):
        self.state["repos"]["acme/public"] = {
            "private": False,
            "secret_scanning": "disabled",
            "push_protection": "disabled",
            "vulnerability_alerts": False,
            "security_updates": False,
            "codeql": "not-configured",
            "files": [],
        }
        self.write_state()

        first = self.run_script(["--repo", "acme/public"])
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertIn("PUT", self.methods())

        self.log_path.write_text("", encoding="utf-8")
        second = self.run_script(["--repo", "acme/public"])
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertNotIn("PUT", self.methods())
        self.assertNotIn("PATCH", self.methods())

    def test_check_mode_never_writes(self):
        self.state["repos"]["acme/public"] = {
            "private": False,
            "secret_scanning": "disabled",
            "push_protection": "disabled",
            "vulnerability_alerts": False,
            "security_updates": False,
            "codeql": "not-configured",
            "files": [],
        }
        self.write_state()

        result = self.run_script(["--check", "--repo", "acme/public"])
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("PUT", self.methods())
        self.assertNotIn("PATCH", self.methods())
        entry = self.read_state()["repos"]["acme/public"]
        self.assertFalse(entry["vulnerability_alerts"])
        self.assertEqual(entry["secret_scanning"], "disabled")

    def test_push_protection_can_be_skipped(self):
        self.state["repos"]["acme/public"] = healthy_entry(False)
        self.state["repos"]["acme/public"]["push_protection"] = "disabled"
        self.write_state()

        result = self.run_script(
            ["--check", "--no-push-protection", "--repo", "acme/public", "--json"]
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        document = self.json_result(result)
        controls = document["repositories"][0]["controls"]
        self.assertEqual(controls["push_protection"]["state"], "skipped")

    # ------------------------------------------------------------------
    # Private Repositories
    # ------------------------------------------------------------------

    def test_private_repo_without_configs_is_action_required(self):
        self.state["repos"]["acme/private"] = healthy_entry(True)
        self.state["repos"]["acme/private"]["files"] = []
        self.write_state()

        result = self.run_script(["--check", "--repo", "acme/private", "--json"])
        self.assertEqual(result.returncode, 1)
        document = self.json_result(result)
        row = document["repositories"][0]
        self.assertEqual(row["visibility"], "private")
        self.assertEqual(row["result"], "action_required")
        self.assertEqual(row["controls"]["gitleaks_workflow"]["state"], "missing")
        self.assertEqual(row["controls"]["dependency_updates"]["state"], "missing")
        self.assertEqual(row["controls"]["secret_scanning"]["state"], "not_applicable")

    def test_private_repo_with_renovate_and_gitleaks_is_ok(self):
        entry = healthy_entry(True)
        entry["files"] = [".github/workflows/gitleaks.yml", "renovate.json"]
        self.state["repos"]["acme/private"] = entry
        self.write_state()

        result = self.run_script(["--check", "--repo", "acme/private"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("gitleaks_workflow=present", result.stdout)
        self.assertIn("dependency_updates=present", result.stdout)

    # ------------------------------------------------------------------
    # CodeQL-Sonderfälle
    # ------------------------------------------------------------------

    def test_codeql_advanced_setup_conflict_is_ok(self):
        self.state["repos"]["acme/public"] = healthy_entry(False)
        self.state["repos"]["acme/public"]["codeql"] = "not-configured"
        self.state["repos"]["acme/public"]["fail"] = {
            "code-scanning/default-setup:PATCH": 409,
        }
        self.write_state()

        result = self.run_script(["--repo", "acme/public", "--json"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        controls = self.json_result(result)["repositories"][0]["controls"]
        self.assertEqual(controls["codeql_default_setup"]["state"], "advanced")

    def test_codeql_without_languages_is_not_applicable(self):
        self.state["repos"]["acme/public"] = healthy_entry(False)
        self.state["repos"]["acme/public"]["codeql"] = "not-configured"
        self.state["repos"]["acme/public"]["fail"] = {
            "code-scanning/default-setup:PATCH": {"status": 422, "message": "No languages found"},
        }
        self.write_state()

        result = self.run_script(["--repo", "acme/public", "--json"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        controls = self.json_result(result)["repositories"][0]["controls"]
        self.assertEqual(controls["codeql_default_setup"]["state"], "not_applicable")

    # ------------------------------------------------------------------
    # Fehler, Ausgabe, Authentifizierung
    # ------------------------------------------------------------------

    def test_repo_error_does_not_stop_other_repos(self):
        self.state["repos"]["acme/broken"] = healthy_entry(False)
        self.state["repos"]["acme/broken"]["fail"] = {"repo:GET": 500}
        self.state["repos"]["acme/healthy"] = healthy_entry(False)
        self.write_state()

        result = self.run_script(
            ["--check", "--repo", "acme/broken", "--repo", "acme/healthy", "--json"]
        )
        self.assertEqual(result.returncode, 1)
        document = self.json_result(result)
        by_repo = {row["repository"]: row for row in document["repositories"]}
        self.assertEqual(by_repo["acme/broken"]["result"], "error")
        self.assertEqual(by_repo["acme/healthy"]["result"], "ok")
        self.assertEqual(document["summary"]["errors"], 1)

    def test_hidden_security_analysis_is_action_required(self):
        self.state["repos"]["acme/public"] = healthy_entry(False)
        self.state["repos"]["acme/public"]["secret_scanning"] = "hidden"
        self.state["repos"]["acme/public"]["push_protection"] = "hidden"
        self.write_state()

        result = self.run_script(["--check", "--repo", "acme/public", "--json"])
        self.assertEqual(result.returncode, 1)
        controls = self.json_result(result)["repositories"][0]["controls"]
        self.assertEqual(controls["secret_scanning"]["state"], "unknown")
        self.assertEqual(controls["push_protection"]["state"], "unknown")

    def test_token_never_appears_in_output(self):
        self.state["repos"]["acme/public"] = healthy_entry(False)
        self.write_state()
        result = self.run_script(["--repo", "acme/public"])
        self.assertNotIn("test-token", result.stdout + result.stderr)

    def test_missing_authentication_exits_two(self):
        result = self.run_script(["--check"], auth_ok=False, token=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("nicht authentifiziert", result.stderr)

    def test_invalid_repository_name_rejected(self):
        result = self.run_script(["--repo", "not-a-repo"])
        self.assertEqual(result.returncode, 2)
        self.assertIn("Ungültiger Repository-Name", result.stderr)

    def test_markdown_output_contains_table(self):
        self.state["repos"]["acme/public"] = healthy_entry(False)
        self.write_state()
        result = self.run_script(["--check", "--markdown", "--repo", "acme/public"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("| Repository | Sichtbarkeit |", result.stdout)
        self.assertIn("| acme/public | public |", result.stdout)


if __name__ == "__main__":
    unittest.main()
