"""Click CLI for the OpenClaw Admin CLI-Anything harness."""

from __future__ import annotations

import json as jsonlib
import shlex
from pathlib import Path

import click

from .core.project import (
    asdict_list,
    init_config,
    load_config,
    mask_config,
    parse_endpoints,
    parse_routes,
    project_info,
    resolve_project_root,
    set_config_value,
)
from .core.session import SessionState
from .utils import openclaw_admin_backend as backend
from .utils.repl_skin import ReplSkin


def emit(payload, as_json: bool) -> None:
    if as_json:
        click.echo(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
    elif isinstance(payload, str):
        click.echo(payload)
    else:
        click.echo(jsonlib.dumps(payload, ensure_ascii=False, indent=2))


def ctx_root(ctx: click.Context) -> Path:
    return ctx.obj["root"]


def ctx_json(ctx: click.Context) -> bool:
    return bool(ctx.obj.get("json"))


def print_kv(data: dict) -> None:
    width = max((len(str(key)) for key in data), default=0)
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            value = jsonlib.dumps(value, ensure_ascii=False)
        click.echo(f"{str(key).ljust(width)}  {value}")


def print_rows(rows: list[dict], columns: list[str]) -> None:
    if not rows:
        click.echo("No rows.")
        return
    widths = {column: len(column) for column in columns}
    for row in rows:
        for column in columns:
            widths[column] = max(widths[column], len(str(row.get(column, ""))))
    header = "  ".join(column.ljust(widths[column]) for column in columns)
    click.echo(header)
    click.echo("  ".join("-" * widths[column] for column in columns))
    for row in rows:
        click.echo("  ".join(str(row.get(column, "")).ljust(widths[column]) for column in columns))


@click.group(invoke_without_command=True)
@click.option("--project", "project_path", default=".", help="OpenClaw Admin project root or a path inside it.")
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON.")
@click.pass_context
def cli(ctx: click.Context, project_path: str, as_json: bool) -> None:
    """Agent-friendly CLI harness for OpenClaw Admin."""

    root = resolve_project_root(project_path)
    ctx.obj = {"root": root, "json": as_json}
    if ctx.invoked_subcommand is None:
        ctx.invoke(repl)


@cli.group()
def project() -> None:
    """Inspect repository metadata."""


@project.command("info")
@click.pass_context
def project_info_command(ctx: click.Context) -> None:
    """Show package, route, endpoint, and runtime config summary."""

    info = project_info(ctx_root(ctx))
    if ctx_json(ctx):
        emit(info, True)
    else:
        print_kv(info)


@project.command("scripts")
@click.pass_context
def project_scripts_command(ctx: click.Context) -> None:
    """List npm scripts available in package.json."""

    scripts = backend.npm_scripts(ctx_root(ctx))
    if ctx_json(ctx):
        emit(scripts, True)
    else:
        print_kv(scripts)


@cli.group()
def routes() -> None:
    """Inspect frontend routes."""


@routes.command("list")
@click.option("--include-hidden", is_flag=True, help="Include hidden routes and redirects.")
@click.pass_context
def routes_list_command(ctx: click.Context, include_hidden: bool) -> None:
    """List Vue router pages mapped from src/router/routes.ts."""

    items = asdict_list(parse_routes(ctx_root(ctx)))
    if not include_hidden:
        items = [item for item in items if not item["hidden"]]
    if ctx_json(ctx):
        emit(items, True)
    else:
        print_rows(items, ["path", "name", "component", "title_key", "public"])


@cli.group()
def api() -> None:
    """Inspect and probe the Express API surface."""


@api.command("list")
@click.option("--method", type=str, help="Filter by HTTP method.")
@click.pass_context
def api_list_command(ctx: click.Context, method: str | None) -> None:
    """List Express endpoints from server/index.js."""

    items = asdict_list(parse_endpoints(ctx_root(ctx)))
    if method:
        items = [item for item in items if item["method"] == method.upper()]
    if ctx_json(ctx):
        emit(items, True)
    else:
        print_rows(items, ["method", "path", "auth_required"])


@api.command("health")
@click.option("--base-url", default="http://127.0.0.1:3001", show_default=True)
@click.pass_context
def api_health_command(ctx: click.Context, base_url: str) -> None:
    """Call a running backend's /api/health endpoint."""

    result = backend.health(base_url)
    emit(result, ctx_json(ctx))


@api.command("status")
@click.option("--base-url", default="http://127.0.0.1:3001", show_default=True)
@click.option("--token", default="", help="Bearer token for auth-enabled backend.")
@click.pass_context
def api_status_command(ctx: click.Context, base_url: str, token: str) -> None:
    """Call a running backend's /api/status endpoint."""

    result = backend.status(base_url, token=token)
    emit(result, ctx_json(ctx))


@cli.group()
def config() -> None:
    """Read and safely edit OpenClaw Admin .env configuration."""


@config.command("show")
@click.option("--env-file", default=".env", show_default=True)
@click.option("--include-secrets", is_flag=True, help="Do not mask token/password values.")
@click.pass_context
def config_show_command(ctx: click.Context, env_file: str, include_secrets: bool) -> None:
    """Show config values from .env, or .env.example/defaults when missing."""

    values = mask_config(load_config(ctx_root(ctx), env_file), include_secrets)
    if ctx_json(ctx):
        emit(values, True)
    else:
        print_kv(values)


@config.command("init")
@click.option("--env-file", default=".env", show_default=True)
@click.option("--force", is_flag=True, help="Overwrite an existing env file.")
@click.pass_context
def config_init_command(ctx: click.Context, env_file: str, force: bool) -> None:
    """Create .env from project defaults."""

    root = ctx_root(ctx)
    path = root / env_file
    before = path.read_text(encoding="utf-8") if path.exists() else None
    written = init_config(root, force=force, env_file=env_file)
    after = written.read_text(encoding="utf-8")
    SessionState.load(root).record_config_change(root, f"init {env_file}", env_file, before, after)
    emit({"ok": True, "path": str(written)}, ctx_json(ctx))


@config.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--env-file", default=".env", show_default=True)
@click.pass_context
def config_set_command(ctx: click.Context, key: str, value: str, env_file: str) -> None:
    """Set one .env key and record an undo snapshot."""

    root = ctx_root(ctx)
    path = root / env_file
    before = path.read_text(encoding="utf-8") if path.exists() else None
    written = set_config_value(root, key, value, env_file=env_file)
    after = written.read_text(encoding="utf-8")
    SessionState.load(root).record_config_change(root, f"set {key}", env_file, before, after)
    shown = "***" if "TOKEN" in key or "PASSWORD" in key else value
    emit({"ok": True, "path": str(written), "key": key, "value": shown}, ctx_json(ctx))


@cli.group(name="backend")
def backend_group() -> None:
    """Delegate to the real npm/Node backend."""


@backend_group.command("scripts")
@click.pass_context
def backend_scripts_command(ctx: click.Context) -> None:
    """List npm scripts that can be delegated to."""

    scripts = backend.npm_scripts(ctx_root(ctx))
    if ctx_json(ctx):
        emit(scripts, True)
    else:
        print_kv(scripts)


@backend_group.command("run")
@click.argument("script")
@click.argument("args", nargs=-1)
@click.pass_context
def backend_run_command(ctx: click.Context, script: str, args: tuple[str, ...]) -> None:
    """Run npm script through the real project backend/toolchain."""

    result = backend.npm_run(ctx_root(ctx), script, args)
    payload = {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    if ctx_json(ctx):
        emit(payload, True)
    else:
        click.echo(result.stdout, nl=False)
        if result.stderr:
            click.echo(result.stderr, err=True, nl=False)
        raise click.exceptions.Exit(result.returncode)


@cli.group()
def session() -> None:
    """Inspect and manage harness undo/redo state."""


@session.command("status")
@click.pass_context
def session_status_command(ctx: click.Context) -> None:
    """Show undo/redo session status."""

    status = SessionState.load(ctx_root(ctx)).status()
    emit(status, ctx_json(ctx))


@session.command("undo")
@click.pass_context
def session_undo_command(ctx: click.Context) -> None:
    """Undo the latest config mutation."""

    item = SessionState.load(ctx_root(ctx)).undo(ctx_root(ctx))
    emit({"ok": True, "undone": item["label"], "envFile": item["envFile"]}, ctx_json(ctx))


@session.command("redo")
@click.pass_context
def session_redo_command(ctx: click.Context) -> None:
    """Redo the latest undone config mutation."""

    item = SessionState.load(ctx_root(ctx)).redo(ctx_root(ctx))
    emit({"ok": True, "redone": item["label"], "envFile": item["envFile"]}, ctx_json(ctx))


@cli.command()
@click.pass_context
def repl(ctx: click.Context) -> None:
    """Start the stateful OpenClaw Admin REPL."""

    root = ctx_root(ctx)
    skin = ReplSkin("openclaw-admin", version="0.1.0")
    skin.print_banner()
    skin.info(f"Project: {root}")
    repl_commands = {
        "info": "Show project summary",
        "routes": "List visible frontend routes",
        "api": "List Express endpoints",
        "config": "Show masked config",
        "health": "Probe http://127.0.0.1:3001/api/health",
        "undo": "Undo latest config change",
        "redo": "Redo latest undone config change",
        "quit": "Exit",
    }
    skin.help(repl_commands)
    while True:
        try:
            line = input("openclaw-admin> ").strip()
        except (EOFError, KeyboardInterrupt):
            click.echo()
            break
        if not line:
            continue
        if line in {"quit", "exit"}:
            break
        try:
            args = shlex.split(line)
            command = args[0]
            if command == "info":
                print_kv(project_info(root))
            elif command == "routes":
                print_rows([item for item in asdict_list(parse_routes(root)) if not item["hidden"]], ["path", "name", "component"])
            elif command == "api":
                print_rows(asdict_list(parse_endpoints(root)), ["method", "path", "auth_required"])
            elif command == "config":
                print_kv(mask_config(load_config(root)))
            elif command == "health":
                emit(backend.health("http://127.0.0.1:3001"), False)
            elif command == "undo":
                item = SessionState.load(root).undo(root)
                skin.success(f"Undid {item['label']}")
            elif command == "redo":
                item = SessionState.load(root).redo(root)
                skin.success(f"Redid {item['label']}")
            elif command == "help":
                skin.help(repl_commands)
            else:
                skin.warning("Unknown REPL command. Use normal subcommands outside the REPL for advanced options.")
        except Exception as exc:  # noqa: BLE001 - REPL should stay alive.
            skin.error(str(exc))
    skin.print_goodbye()


if __name__ == "__main__":
    cli()
