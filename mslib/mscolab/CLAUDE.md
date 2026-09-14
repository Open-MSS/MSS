# mslib.mscolab — collaboration server

Purpose: Flask + Flask-SocketIO server for shared flight-track operations:
auth, permissions, chat, versioned waypoint storage.
Global map: ../../ARCHITECTURE.md

## Layout

- `server.py` — thin assembly: HTTP basic auth hooks, blueprint registration
- `app/__init__.py` — Flask app factory (config, db, socketio bindings)
- `blueprints/{operation,auth,chat,user,docs,admin}/` — all REST routes; keep
  handlers thin, business logic belongs in the managers. `admin` is
  token-authenticated (`ADMIN_TOKEN`) and localhost-only, not per-user — it's the
  CLI's only way to trigger a socket.io event on the live server (see `cli_notify.py`)
- `file_manager.py` — operations/permissions/versioning (git-backed) — core
- `chat_manager.py`, `sockets_manager.py` — chat + socket.io event handlers
- `models.py` — SQLAlchemy models; `migrations/` — Alembic, never edit
- `events.py` (`SocketEvents`) + `message_type.py` (`MessageType`) — the ONLY
  modules the GUI client may import; they define the shared vocabulary
- `conf.py` — `DefaultSettings`; overridden by a `mscolab_settings` module
- `mscolab.py` — CLI (`mscolab start|db --init|--seed|--reset`); `seed.py` — demo data
- `cli_notify.py` — best-effort HTTP call from CLI actions in `seed.py` to the
  running server's `admin` blueprint, so connected clients get the same socket.io
  events a REST-triggered equivalent action would emit; no-ops if the server isn't
  reachable (e.g. `db --seed` before any server has started)

## May import

`mslib.utils` only (plus stdlib/Flask stack). Never `mslib.msui` (exception:
`blueprints/docs` icons, grandfathered) or `mslib.mswms`. Enforced by the
`gui-isolation` contract in setup.cfg.

## Invariants

- Every REST payload has a mirror-image consumer in `mslib/msui/mscolab.py` —
  change both sides in the same commit and grep the endpoint name.
- Socket event names come from `SocketEvents`; never emit a bare string.
- Tokens are validated per request; don't cache auth state in handlers.
- DB schema changes require an Alembic migration (see docs/development.rst).

## Verify

`pixi run -e dev test-mscolab`; client-side effects:
`pixi run -e dev env QT_QPA_PLATFORM=offscreen pytest tests/_test_msui/test_mscolab.py -q`.
The test server is forked once per session by an autouse fixture in
`tests/fixtures.py`, only when a collected test needs it.
