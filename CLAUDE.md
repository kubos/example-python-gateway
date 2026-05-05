# example-python-gateway

Reference implementation of a Major Tom gateway in Python — the canonical "look here for a working gateway" repo. Connects to Major Tom over WebSocket via the [`majortom_gateway`](https://pypi.org/project/majortom-gateway/) SDK, registers a fake satellite with command definitions, and demonstrates how command/status/telemetry/file flows go between Major Tom and a satellite-side process.

> This repo ships **two coexisting examples**, not one: a *sync* gateway (newer, recommended) and an *async* demo gateway (older, more feature-complete). They are different architectures intentionally kept side-by-side as references for different programming styles.

## Stack
- Python **3.13+** (`.tool-versions` pins `python 3.13.7`; matches the SDK's hard `>=3.13` floor)
- `majortom_gateway>=0.1.4` from PyPI (the local-dev path can substitute a sibling checkout — see Common Tasks)
- `websockets >=13.0,<14.0`, `requests`, `asgiref` — same constraints as the SDK
- `pytest`, `pytest-asyncio`, `pytest-watch`, `pytest-only`, `mock` for tests
- Docker for the canonical run path (and the test-watch path)

## Entry points
- `run.py` — CLI entry. Args: `majortomhost gatewaytoken [-b user:pass] [-l debug|info|error] [--http] [-a|--async]`. Default is the sync gateway; `--async` switches to the older demo.
- `run-docker.sh` — wraps `docker build` + `docker run` against `Dockerfile`. Same args as `run.py`.
- `bin/run-dev.sh` — dev variant that copies `../majortom_gateway_package` (sibling SDK checkout) into the image so changes in the SDK can be tested without a PyPI release.
- `bin/docker-testw.sh` — containerized test watcher.
- `bin/install-majortom-gateway.sh` — Dockerfile-time helper that prefers a local `./majortom_gateway_api` directory if present, otherwise installs from PyPI.

## Layout
The two-pattern split shows up as parallel directory trees:

| Pattern | Code | Style | Notes |
|---|---|---|---|
| Sync gateway (default) | `gateway/` + `satellite/` | Synchronous Python; clear gateway↔satellite separation | Newer, recommended starting point. System name registered with MT: `Example FlatSat`. |
| Async demo | `demo/demo_sat.py`, `demo/demo_telemetry.py` | Async; gateway and fake satellite intermingled | Older, but more feature-complete (telemetry generation, uplink/downlink). System name: `Space Oddity`. |

Other dirs:
- `gateway/stubs.py` — placeholder `translate_command_to_binary` / `packetize` / `encrypt` functions; the spots where a real gateway would plug into actual radio/protocol code.
- `gateway/statuses.py` — `CommandStatus` enum mapping operator-visible states (`PREPARING`, `UPLINKING`, `TRANSMITTED`, `ACKED`, `EXECUTING`, `PROCESSING`, `CANCELLED`, `FAILED`, `DOWNLINKING`, `COMPLETED`) to the strings Major Tom expects (`preparing_on_gateway`, etc.).
- `satellite/satellite.py` — the simulated spacecraft that the sync gateway talks to.
- `satellite/example_commands.json` — pre-baked command definitions; sent to MT via `update_command_definitions` on connect (`run.py:128–132`).
- `tests/gateway/`, `tests/satellite/` — pytest suites.
- `Dockerfile` — production-style image; `docker/Dockerfile.test` — test image.

## Cross-repo touch points
- **`majortom_gateway_package`** is the only direct dependency that matters here. This repo *is* the canonical consumer. Two integration paths:
  1. **Released**: `pip install majortom_gateway` (per `requirements.txt`).
  2. **Local dev**: `bin/install-majortom-gateway.sh` checks for `./majortom_gateway_api/` (a local copy) and `pip install -e`'s it; otherwise falls back to PyPI. `bin/run-dev.sh` populates that copy from `../majortom_gateway_package` before building the image. So changes to the SDK can be validated end-to-end without a release.
- **major-tom** is the runtime peer (the gateway connects *to* a Major Tom instance), not a build/code dependency. Nothing in this repo's source references major-tom code paths directly — the contract is the SDK's WebSocket protocol.
- **No dependency on cosmos / Commander / orbitmodel / xray** — this repo is pure gateway-side reference. Telemetry it sends is *fake*, generated locally in `demo/demo_telemetry.py` or stub paths in `gateway/`.

## Conventions
- **Conventional Commits**: recent history (`feat:`, `fix:`, `chore:`, `docs:`, `ci:`) — match it. Latest example: commit `2c22f12` `fix: pin websockets to <14.0 for compatibility`.
- **Two patterns are intentionally preserved.** When updating one, don't silently drop the other; both are referenced from the README as choice-of-style examples.
- **Logging defaults to debug** in `run.py`. Operators running this for a demo see verbose logs by default; `-l info` or `-l error` quiets it.
- **Test naming**: `tests/gateway/test_*.py` and `tests/satellite/test_*.py`. `pytest-only` is in deps so individual tests can be tagged `@pytest.mark.only` for focused runs.

## Gotchas & safety
- **`pip install majortom-gateway` vs `majortom_gateway`**: PyPI normalizes both, but the codebase uses underscore (`requirements.txt:3`, `bin/install-majortom-gateway.sh`). Don't rewrite to the dashed form on a hunch — leave as-is.
- **Local-dev SDK install requires the sibling layout exactly.** `bin/run-dev.sh` looks for `../majortom_gateway_package`. If your checkout layout differs, the script bails with `"This is a development script. You must have the gateway api cloned in ../majortom_gateway_package"`. Don't symlink past this; fix the directory layout.
- **`run.py` uses `args.async` via `vars(args)['async']`** (`run.py:152`). `async` is a reserved word in modern Python, so `args.async` would be a syntax error — the indirection is deliberate, not a bug. Don't "clean it up."
- **The sync gateway uses `time.sleep(...)` in callbacks** (e.g. `gateway.py:53`), which blocks the asyncio thread. This works because callbacks run on a `sync_to_async` thread (per the SDK; see `majortom_gateway_package/CLAUDE.md`). Don't paste this pattern into an async callback — it would block the event loop.
- **`Space Oddity` and `Example FlatSat`** are the two demo system names registered with MT. Connecting the same gateway token while both demos have run before will leave both system records in MT — clean up via the MT UI if running fresh demos repeatedly.
- **websockets pin (`<14.0`)** mirrors the SDK's pin (commit `2c22f12`). Bumping requires the SDK to bump first.
- **Kubos→Xplore renaming**: as with sibling repos, `kubos/example-python-gateway` and `slack.kubos.com` references in the README are historical; the company is now Xplore (per `major-tom/CLAUDE.md`).

## Common tasks
- **Run the demo (Docker)**: `./run-docker.sh <majortomhost> <gateway_token>` (add `--http` for local on-prem, `-b user:pass` for Basic Auth)
- **Run with a local SDK checkout** (validate SDK changes without a release): `./bin/run-dev.sh host.docker.internal:3001 <token> --http -l info` — requires `../majortom_gateway_package` to exist as a sibling
- **Run tests once**: `pip install -r requirements.txt && pytest tests/`
- **Run tests in watch mode (Docker)**: `./bin/docker-testw.sh`
- **Use the async demo instead of the sync gateway**: append `-a` / `--async` to any `run.py` / `run-docker.sh` invocation
- **Set up locally (no Docker)**: `pip3 install -r requirements.txt && python3 run.py <host> <token>`

## What this repo is *not*
- **Not production code.** It's a reference implementation. The `gateway/stubs.py` "translate / packetize / encrypt" helpers are deliberate placeholders — a real gateway substitutes radio/protocol code there.
- **Not a template generator.** Don't build automation that scaffolds new gateways from this repo's layout; both architectures here are illustrative, not canonical.
- **Not where the SDK lives.** All gateway-API logic (WebSocket handling, reconnection, queueing, callback dispatch) is in `majortom_gateway_package`. This repo only demonstrates *using* it.
- **Not a satellite simulator.** `satellite/satellite.py` and `demo/demo_sat.py` are minimal command-and-telemetry mocks for the demo flow; they don't simulate orbital mechanics, hardware, or any real spacecraft behavior.
