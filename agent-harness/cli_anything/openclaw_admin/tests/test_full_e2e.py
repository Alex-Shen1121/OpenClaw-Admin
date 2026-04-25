import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


def _resolve_cli(name):
    """Resolve installed CLI command; falls back to python -m for development."""

    force = os.environ.get("CLI_ANYTHING_FORCE_INSTALLED", "").strip() == "1"
    path = shutil.which(name)
    if path:
        return [path]
    if force:
        raise RuntimeError(f"{name} not found in PATH. Install with: pip install -e .")
    return [sys.executable, "-m", "cli_anything.openclaw_admin.openclaw_admin_cli"]


CLI_BASE = _resolve_cli("cli-anything-openclaw-admin")


def run_cli(args, cwd=None, check=True):
    return subprocess.run(
        CLI_BASE + ["--project", str(ROOT), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=check,
    )


def test_help():
    result = subprocess.run(CLI_BASE + ["--help"], text=True, capture_output=True, check=True)
    assert "OpenClaw Admin" in result.stdout


def test_project_info_json():
    result = run_cli(["--json", "project", "info"])
    data = json.loads(result.stdout)
    assert data["name"] == "openclaw-web"
    assert data["routes"] >= 10


def test_routes_list_json_contains_agents():
    result = run_cli(["--json", "routes", "list"])
    routes = json.loads(result.stdout)
    assert any(route["name"] == "Agents" for route in routes)


def test_api_list_json_contains_health():
    result = run_cli(["--json", "api", "list"])
    endpoints = json.loads(result.stdout)
    assert any(endpoint["method"] == "GET" and endpoint["path"] == "/api/health" for endpoint in endpoints)


def test_config_set_undo_redo_workflow(tmp_path):
    fixture = tmp_path / "OpenClaw-Admin"
    shutil.copytree(
        ROOT,
        fixture,
        ignore=shutil.ignore_patterns(".git", "node_modules", "dist", ".openclaw-admin-cli-session.json"),
    )
    base = CLI_BASE + ["--project", str(fixture)]
    subprocess.run(base + ["config", "set", "OPENCLAW_WS_URL", "ws://127.0.0.1:18789"], check=True)
    assert "OPENCLAW_WS_URL=ws://127.0.0.1:18789" in (fixture / ".env").read_text(encoding="utf-8")
    subprocess.run(base + ["session", "undo"], check=True)
    assert not (fixture / ".env").exists()
    subprocess.run(base + ["session", "redo"], check=True)
    assert "OPENCLAW_WS_URL=ws://127.0.0.1:18789" in (fixture / ".env").read_text(encoding="utf-8")
