from pathlib import Path

from cli_anything.openclaw_admin.core.project import (
    load_config,
    mask_config,
    parse_endpoints,
    parse_routes,
    project_info,
    resolve_project_root,
)
from cli_anything.openclaw_admin.core.session import SessionState


ROOT = Path(__file__).resolve().parents[4]


def test_resolve_project_root():
    assert resolve_project_root(ROOT) == ROOT


def test_project_info_counts_routes_and_endpoints():
    info = project_info(ROOT)
    assert info["name"] == "openclaw-web"
    assert info["routes"] >= 10
    assert info["apiEndpoints"] >= 20


def test_parse_routes_finds_core_pages():
    routes = parse_routes(ROOT)
    names = {route.name for route in routes}
    assert {"Dashboard", "Chat", "Agents", "Settings"}.issubset(names)


def test_parse_endpoints_finds_health_and_rpc():
    endpoints = parse_endpoints(ROOT)
    pairs = {(endpoint.method, endpoint.path) for endpoint in endpoints}
    assert ("GET", "/api/health") in pairs
    assert ("POST", "/api/rpc") in pairs


def test_load_config_falls_back_to_example():
    config = load_config(ROOT)
    assert config["OPENCLAW_WS_URL"].startswith("ws://")


def test_mask_config_hides_secrets():
    masked = mask_config({"OPENCLAW_AUTH_TOKEN": "abcdef", "AUTH_PASSWORD": "secret"})
    assert masked["OPENCLAW_AUTH_TOKEN"] == "ab***ef"
    assert masked["AUTH_PASSWORD"] == "se***et"


def test_session_records_status(tmp_path):
    state = SessionState()
    state.record_config_change(tmp_path, "set PORT", ".env", None, "PORT=3001\n")
    loaded = SessionState.load(tmp_path)
    assert loaded.status()["historyCount"] == 1


def test_session_undo_redo(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("PORT=3001\n", encoding="utf-8")
    state = SessionState()
    state.record_config_change(tmp_path, "set PORT", ".env", "PORT=3001\n", "PORT=3999\n")
    env_path.write_text("PORT=3999\n", encoding="utf-8")
    SessionState.load(tmp_path).undo(tmp_path)
    assert env_path.read_text(encoding="utf-8") == "PORT=3001\n"
    SessionState.load(tmp_path).redo(tmp_path)
    assert env_path.read_text(encoding="utf-8") == "PORT=3999\n"
