# OpenClaw Admin Harness

This harness turns the OpenClaw Admin web console into an agent-friendly CLI surface.
It does not reimplement the OpenClaw Gateway. Instead, it wraps the real project files,
the Express API surface, and the npm/Node runtime used by the admin console.

## Backend Mapping

- Frontend routes are read from `src/router/routes.ts`.
- Express API endpoints are read from `server/index.js`.
- Runtime configuration is read from `.env` or `.env.example`.
- Live backend probes call the running Express service, normally
  `http://127.0.0.1:3001`.
- Project scripts are delegated to npm via `npm run <script>`.

## Command Groups

- `project`: inspect repository metadata and npm scripts.
- `routes`: list web console pages and their Vue components.
- `api`: list Express endpoints and probe live backend health/status.
- `config`: initialize, read, and update `.env` with secret masking and undo/redo.
- `backend`: inspect available npm scripts and run npm delegated commands.
- `session`: inspect and manage CLI session history.

## Safety

Config commands mask token/password values by default. Mutating config operations
save a session snapshot so `session undo` and `session redo` can restore prior
`.env` content.
