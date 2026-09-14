# mslib.mscolab — collaboration server

Purpose: Flask + Flask-SocketIO server for shared flight-track operations:
auth, permissions, chat, versioned waypoint storage.
Global map: ../../ARCHITECTURE.md

## Layout

- `server.py` — thin assembly: `create_server_app()` adds db migration, CORS,
  HTTP basic auth and the socket.io managers to the app
- `app/__init__.py` — `create_app()` factory (config, extensions, blueprints)
  and `initialise_db()`; there is no module level app instance
- `blueprints/{operation,auth,chat,user,docs,admin}/` — all ~50 REST routes; keep
  handlers thin, business logic belongs in the managers. `admin` is
  token-authenticated (`ADMIN_TOKEN`) and localhost-only, not per-user — it's the
  CLI's only way to trigger a socket.io event on the live server (see `cli_notify.py`)
- `file_manager.py` — operations/permissions/versioning (git-backed) — core
- `chat_manager.py`, `sockets_manager.py` — chat + socket.io event handlers;
  `_setup_managers(app)` builds a SocketIO instance per app, never a shared one
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
- No module level state that belongs to one app (app, db engine, SocketIO,
  HTTPBasicAuth, managers). It lives on the app: `app.config` or
  `app.extensions['sockio' | 'cm' | 'fm' | 'basic_auth']`, read via `current_app`.
  Two apps must be able to exist side by side, that is what the tests rely on.
- DB schema changes require an Alembic migration (see docs/development.rst).

## Verify

`pixi run -e dev test-mscolab`; client-side effects:
`pixi run -e dev env QT_QPA_PLATFORM=offscreen pytest tests/_test_msui/test_mscolab.py -q`.
The test server is forked once per session by an autouse fixture in
`tests/fixtures.py`, only when a collected test needs it. Two app fixtures exist
there: `mscolab_app` builds a fresh app with an empty database of its own for
every test, `mscolab_server_app` is the shared app the forked server runs — use
the latter only together with `mscolab_server`.
