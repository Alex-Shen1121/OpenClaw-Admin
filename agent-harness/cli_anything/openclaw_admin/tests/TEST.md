# Test Plan

## Test Inventory Plan

- `test_core.py`: 8 unit tests planned.
- `test_full_e2e.py`: 5 subprocess and workflow tests planned.

## Unit Test Plan

### `core.project`

- Resolve an OpenClaw Admin project root from the repository root.
- Parse package metadata from `package.json`.
- Parse Vue router records from `src/router/routes.ts`.
- Parse Express endpoints from `server/index.js`.
- Load config from `.env.example` when `.env` is absent.
- Mask secret config keys by default.

Expected count: 6 tests.

### `core.session`

- Record config change history.
- Undo and redo a config file mutation.

Expected count: 2 tests.

## E2E Test Plan

- Invoke `cli-anything-openclaw-admin --help` through subprocess.
- Invoke `project info --json` and verify route/API counts.
- Invoke `routes list --json` and verify known admin pages.
- Invoke `api list --json` and verify `/api/health`.
- Run a config set/undo/redo workflow on a temporary copied project fixture.

## Realistic Workflow Scenarios

### Inventory Admin Console

Simulates an agent understanding the web UI before making changes.

Operations chained:

1. `project info --json`
2. `routes list --json`
3. `api list --json`

Verified:

- Project metadata can be read.
- UI pages and backend endpoints are discoverable.

### Safe Gateway Reconfiguration

Simulates changing the OpenClaw Gateway URL for a local deployment.

Operations chained:

1. `config set OPENCLAW_WS_URL ws://127.0.0.1:18789`
2. `config show --json`
3. `session undo`
4. `session redo`

Verified:

- `.env` content changes.
- Undo/redo restores the prior and updated file states.

## Test Results

```text
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0 -- /Library/Developer/CommandLineTools/usr/bin/python3
cachedir: .pytest_cache
rootdir: /Users/shenchenyu/Documents/Codex/2026-04-26/OpenClaw-Admin/agent-harness
plugins: anyio-4.12.1
collecting ... collected 13 items

agent-harness/cli_anything/openclaw_admin/tests/test_core.py::test_resolve_project_root PASSED [  7%]
agent-harness/cli_anything/openclaw_admin/tests/test_core.py::test_project_info_counts_routes_and_endpoints PASSED [ 15%]
agent-harness/cli_anything/openclaw_admin/tests/test_core.py::test_parse_routes_finds_core_pages PASSED [ 23%]
agent-harness/cli_anything/openclaw_admin/tests/test_core.py::test_parse_endpoints_finds_health_and_rpc PASSED [ 30%]
agent-harness/cli_anything/openclaw_admin/tests/test_core.py::test_load_config_falls_back_to_example PASSED [ 38%]
agent-harness/cli_anything/openclaw_admin/tests/test_core.py::test_mask_config_hides_secrets PASSED [ 46%]
agent-harness/cli_anything/openclaw_admin/tests/test_core.py::test_session_records_status PASSED [ 53%]
agent-harness/cli_anything/openclaw_admin/tests/test_core.py::test_session_undo_redo PASSED [ 61%]
agent-harness/cli_anything/openclaw_admin/tests/test_full_e2e.py::test_help PASSED [ 69%]
agent-harness/cli_anything/openclaw_admin/tests/test_full_e2e.py::test_project_info_json PASSED [ 76%]
agent-harness/cli_anything/openclaw_admin/tests/test_full_e2e.py::test_routes_list_json_contains_agents PASSED [ 84%]
agent-harness/cli_anything/openclaw_admin/tests/test_full_e2e.py::test_api_list_json_contains_health PASSED [ 92%]
agent-harness/cli_anything/openclaw_admin/tests/test_full_e2e.py::test_config_set_undo_redo_workflow PASSED [100%]

============================== 13 passed in 0.71s ==============================
```

## Summary Statistics

- Total tests: 13
- Pass rate: 100%
- Execution time: 0.71 seconds

## Coverage Notes

- Covered source inventory, route/API extraction, config masking, CLI subprocess use, and config undo/redo.
- Live Gateway-backed RPC behavior is not covered because it requires an OpenClaw Gateway service.
- Live Express `/api/health` probing is implemented but not asserted in automated tests because the backend service is not started by the harness tests.
