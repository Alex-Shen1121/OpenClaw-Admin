"""Project inspection and safe config editing for OpenClaw Admin."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SECRET_KEYS = {"OPENCLAW_AUTH_TOKEN", "OPENCLAW_AUTH_PASSWORD", "AUTH_PASSWORD"}
DEFAULT_ENV = {
    "VITE_APP_TITLE": "OpenClaw-Admin",
    "OPENCLAW_WS_URL": "ws://localhost:18789",
    "OPENCLAW_AUTH_TOKEN": "",
    "OPENCLAW_AUTH_PASSWORD": "",
    "PORT": "3001",
    "DEV_FRONTEND_URL": "http://localhost:3000",
    "AUTH_USERNAME": "",
    "AUTH_PASSWORD": "",
    "LOG_LEVEL": "INFO",
}


@dataclass(frozen=True)
class RouteInfo:
    path: str
    name: str
    component: str
    title_key: str
    hidden: bool
    public: bool


@dataclass(frozen=True)
class EndpointInfo:
    method: str
    path: str
    auth_required: bool


def resolve_project_root(path: str | os.PathLike[str] | None = None) -> Path:
    """Resolve an OpenClaw Admin repository root from a path or cwd."""

    start = Path(path or os.getcwd()).expanduser().resolve()
    candidates = [start] if start.is_dir() else [start.parent]
    candidates.extend(candidates[0].parents)
    for candidate in candidates:
        if (candidate / "package.json").exists() and (candidate / "server" / "index.js").exists():
            return candidate
    raise FileNotFoundError(
        f"Could not find OpenClaw Admin root from {start}. Expected package.json and server/index.js."
    )


def read_package(root: Path) -> dict[str, Any]:
    with (root / "package.json").open("r", encoding="utf-8") as fh:
        return json.load(fh)


def parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    result: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def render_env(values: dict[str, str]) -> str:
    lines = [f"{key}={value}" for key, value in values.items()]
    return "\n".join(lines) + "\n"


def mask_config(values: dict[str, str], include_secrets: bool = False) -> dict[str, str]:
    if include_secrets:
        return dict(values)
    masked = dict(values)
    for key in SECRET_KEYS:
        if masked.get(key):
            value = masked[key]
            masked[key] = value[:2] + "***" + value[-2:] if len(value) > 4 else "***"
    return masked


def load_config(root: Path, env_file: str = ".env") -> dict[str, str]:
    path = root / env_file
    if path.exists():
        return parse_env_file(path)
    example = root / ".env.example"
    if example.exists():
        return parse_env_file(example)
    return dict(DEFAULT_ENV)


def write_config(root: Path, values: dict[str, str], env_file: str = ".env") -> Path:
    path = root / env_file
    path.write_text(render_env(values), encoding="utf-8")
    return path


def init_config(root: Path, force: bool = False, env_file: str = ".env") -> Path:
    path = root / env_file
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists. Use --force to overwrite.")
    values = dict(DEFAULT_ENV)
    example = root / ".env.example"
    if example.exists():
        values.update(parse_env_file(example))
    return write_config(root, values, env_file)


def set_config_value(root: Path, key: str, value: str, env_file: str = ".env") -> Path:
    values = load_config(root, env_file)
    values[key] = value
    return write_config(root, values, env_file)


def _route_blocks(source: str) -> list[str]:
    return re.findall(r"\{\s*path:\s*['\"][^'\"]+['\"].*?\n\s*\}", source, flags=re.S)


def parse_routes(root: Path) -> list[RouteInfo]:
    source_path = root / "src" / "router" / "routes.ts"
    source = source_path.read_text(encoding="utf-8")
    routes: list[RouteInfo] = []
    for block in _route_blocks(source):
        path_match = re.search(r"path:\s*['\"]([^'\"]+)['\"]", block)
        name_match = re.search(r"name:\s*['\"]([^'\"]+)['\"]", block)
        component_match = re.search(r"import\(['\"]@/views/([^'\"]+)['\"]\)", block)
        title_match = re.search(r"titleKey:\s*['\"]([^'\"]+)['\"]", block)
        if not path_match:
            continue
        routes.append(
            RouteInfo(
                path=path_match.group(1),
                name=name_match.group(1) if name_match else "",
                component=component_match.group(1) if component_match else "",
                title_key=title_match.group(1) if title_match else "",
                hidden="hidden: true" in block,
                public="public: true" in block,
            )
        )
    return routes


def parse_endpoints(root: Path) -> list[EndpointInfo]:
    source = (root / "server" / "index.js").read_text(encoding="utf-8")
    pattern = re.compile(
        r"app\.(get|post|put|delete|patch)\(\s*['\"]([^'\"]+)['\"]\s*,\s*(authMiddleware\s*,)?",
        flags=re.I,
    )
    endpoints: list[EndpointInfo] = []
    for match in pattern.finditer(source):
        endpoints.append(
            EndpointInfo(
                method=match.group(1).upper(),
                path=match.group(2),
                auth_required=bool(match.group(3)),
            )
        )
    return endpoints


def project_info(root: Path) -> dict[str, Any]:
    package = read_package(root)
    routes = parse_routes(root)
    endpoints = parse_endpoints(root)
    env_path = root / ".env"
    return {
        "root": str(root),
        "name": package.get("name"),
        "version": package.get("version"),
        "scripts": package.get("scripts", {}),
        "dependencies": len(package.get("dependencies", {})),
        "devDependencies": len(package.get("devDependencies", {})),
        "routes": len(routes),
        "apiEndpoints": len(endpoints),
        "envExists": env_path.exists(),
        "distExists": (root / "dist" / "index.html").exists(),
    }


def asdict_list(items: list[Any]) -> list[dict[str, Any]]:
    return [item.__dict__.copy() for item in items]
