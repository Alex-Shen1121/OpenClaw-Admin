---
name: openclaw-admin
description: Use this CLI to inspect, configure, test, and operate an OpenClaw Admin repository from an agent-friendly command line.
---

# OpenClaw Admin CLI

Use `cli-anything-openclaw-admin` when working with an OpenClaw Admin checkout.

## Core Commands

```bash
cli-anything-openclaw-admin --json project info
cli-anything-openclaw-admin routes list
cli-anything-openclaw-admin api list
cli-anything-openclaw-admin config show
cli-anything-openclaw-admin config set OPENCLAW_WS_URL ws://127.0.0.1:18789
cli-anything-openclaw-admin session undo
```

## Live Backend Probes

Start the app's backend first:

```bash
npm run dev:server
```

Then probe it:

```bash
cli-anything-openclaw-admin api health --base-url http://127.0.0.1:3001
cli-anything-openclaw-admin api status --base-url http://127.0.0.1:3001
```

## Safety

Token and password values are masked by default. Use `config show --include-secrets`
only when an explicit human request requires exact values.
