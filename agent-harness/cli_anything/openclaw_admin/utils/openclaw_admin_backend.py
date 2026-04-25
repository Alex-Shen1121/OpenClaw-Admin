"""Wrappers around the real OpenClaw Admin npm/HTTP backend."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def require_executable(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"{name} was not found in PATH. Install it before running backend commands.")
    return path


def npm_run(root: Path, script: str, extra_args: tuple[str, ...] = ()) -> subprocess.CompletedProcess[str]:
    require_executable("npm")
    cmd = ["npm", "run", script]
    if extra_args:
        cmd.extend(["--", *extra_args])
    return subprocess.run(cmd, cwd=root, text=True, capture_output=True, check=False)


def npm_scripts(root: Path) -> dict[str, str]:
    package = json.loads((root / "package.json").read_text(encoding="utf-8"))
    return package.get("scripts", {})


def http_json(method: str, url: str, token: str = "", payload: dict[str, Any] | None = None, timeout: float = 5.0) -> dict[str, Any]:
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url=url, data=body, headers=headers, method=method.upper())
    try:
        with urlopen(request, timeout=timeout) as response:
            text = response.read().decode("utf-8")
            return {
                "ok": 200 <= response.status < 300,
                "status": response.status,
                "url": url,
                "data": json.loads(text) if text else None,
            }
    except HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        return {
            "ok": False,
            "status": exc.code,
            "url": url,
            "error": text,
        }
    except URLError as exc:
        return {
            "ok": False,
            "status": None,
            "url": url,
            "error": str(exc.reason),
        }


def health(base_url: str) -> dict[str, Any]:
    return http_json("GET", base_url.rstrip("/") + "/api/health")


def status(base_url: str, token: str = "") -> dict[str, Any]:
    return http_json("GET", base_url.rstrip("/") + "/api/status", token=token)
