# cli-anything-openclaw-admin

CLI-Anything harness for the OpenClaw Admin Vue/Express management console.

The harness gives agents a stable command line interface for inspecting the admin
console, editing runtime config safely, listing GUI routes and Express endpoints,
and probing a running backend.

## Install

```bash
cd agent-harness
pip install -e .
```

## Usage

```bash
cli-anything-openclaw-admin --project /path/to/OpenClaw-Admin project info
cli-anything-openclaw-admin --project /path/to/OpenClaw-Admin routes list
cli-anything-openclaw-admin --project /path/to/OpenClaw-Admin api list --method POST
cli-anything-openclaw-admin --project /path/to/OpenClaw-Admin api health --base-url http://127.0.0.1:3001
cli-anything-openclaw-admin --project /path/to/OpenClaw-Admin config show
cli-anything-openclaw-admin --project /path/to/OpenClaw-Admin config set OPENCLAW_WS_URL ws://127.0.0.1:18789
cli-anything-openclaw-admin --project /path/to/OpenClaw-Admin session undo
```

Add `--json` for machine-readable output:

```bash
cli-anything-openclaw-admin --json project info
```

With no subcommand, the CLI enters a small REPL for repeated inspection:

```bash
cli-anything-openclaw-admin
```

## Command Groups

- `project`: package metadata and npm scripts.
- `routes`: Vue router page inventory.
- `api`: Express API endpoint inventory and live probes.
- `config`: `.env` init/show/set with token/password masking.
- `backend`: delegate to real `npm run` scripts.
- `session`: status, undo, and redo for config edits.

## Backend Notes

OpenClaw Admin depends on a running OpenClaw Gateway for most real data. This
harness intentionally does not fake Gateway responses. Commands that inspect the
source tree work offline; live `api health/status` commands require the Express
backend to be running.
