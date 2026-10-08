# MSS Architecture Map

This is the global context map for the MSS codebase — read this first, then the
`CLAUDE.md` card inside the package you are changing. The dependency rules below
are machine-enforced by import-linter (`pixi run -e dev lint-imports`, config in
`setup.cfg`); if this file and the code disagree, CI is the arbiter.

## Packages and dependency direction

Arrows mean "may import". Anything not drawn is forbidden.

```
 mslib.autoplot ──┐┌────────────┐
 (headless batch  ▼│ mslib.msui │  PyQt5 desktop client (GUI)
  plotting CLI)    └─────┬──────┘
        ┌──────────────┼───────────────────────┐
        ▼              ▼                       ▼
 mslib.mscolab.api mslib.support         mslib.utils
 (typed REST       (vendored              (shared: config, constants,
  contract, socket  qt_json_view)          coordinates, units,
  vocabulary; stdlib                       netCDF, auth, qt helpers)
  only, ONLY this of                           ▲
  mslib.mscolab)                               │
        ▲                                      │
   mslib.mscolab (server) ─────────────────────┤
   (never imports msui/mswms)                  │
   mslib.mswms ────────────────────────────────┘
   (WMS server; never imports msui/mscolab)

   mslib.plugins  → mslib.msui.flighttrack (grandfathered), mslib.utils
   mslib.msidp    → standalone SAML identity provider: imports no other mslib
                    package, and no other package imports it
```

The servers' `blueprints.docs` still import `msui.icons` — a to-do listed below.

Besides the arrows, the contracts keep third-party stacks where they belong.
"Server stack" means Flask and its extensions, SQLAlchemy, Alembic, Werkzeug
and pysaml2:

- `mslib.utils` imports no Qt, no keyring and no server stack (`utils-base-layer`);
- `mslib.mscolab.api` imports no other mslib package, no Qt, no numpy and no
  server stack (`api-leaf`);
- the servers `mswms`/`mscolab` never import Qt (`servers-without-qt`);
- the client (`msui`, `plugins`, `support`, `autoplot`) never imports the
  server stack (`client-without-server-stack`);
- `mslib.msidp` imports no Qt, numpy or Flask (`msidp-standalone`), and no
  other package imports it (`msidp-not-imported`).

This is what lets the conda recipe ship the packages separately
(`plans/PACKAGE_SPLIT_PLAN.md`).

Grandfathered violations (do not add new ones; the lists live in `setup.cfg`
under `ignore_imports` and must only shrink):

- `plugins.io.{csv,text,flitestar}` import `msui.flighttrack` (all of them
  ship in the `mss-msui` package).
- the deprecation shim `msui/constants.py` re-exports `utils/constants.py`
  (`docs/samples/plugins/navaid.py` uses it).
- To-dos of the package split, each labelled with the decoupling PR of
  `plans/PACKAGE_SPLIT_PLAN.md` that removes it: `{mscolab,mswms}.blueprints.docs`
  import `msui.icons`; `utils` modules import Qt, `mslib.support`, Flask and
  keyring (`utils-base-layer`, `client-without-server-stack`). import-linter
  reports an entry whose import is gone ("No matches for ignored import"), so
  the PR that removes an import has to delete its entry.

## Module index

### mslib/msui — PyQt5 GUI (entry: `msui`)

- `msui.py` / `mss.py` — entry points (GUI / CLI dispatcher)
- `msui_mainwindow.py` — main window; owns flight-track list and open views
- `viewwindows.py` — view base classes (`MSUIViewWindow`, `MSUIMplViewWindow`)
- `topview.py`, `sideview.py`, `tableview.py`, `linearview.py` — the four views
- `viewplotter.py` — shared plotting glue for views
- `mpl_qtwidget.py`, `mpl_map.py`, `mpl_pathinteractor.py` — matplotlib canvas,
  basemap, interactive waypoint editing (the defect-prone interactive core)
- `flighttrack.py` — waypoint table model shared by all views
- `wms_control.py` — WMS client dockwidget + `MSUIWebMapService` + fetcher/cache
- `mscolab.py` — MSColab client (login, operations, permissions; largest class)
- `socket_control.py` — socket.io client; re-emits network events as Qt signals
- `mscolab_*.py` — chat, admin, version-history, merge dialogs
- `*_dockwidget.py` — airdata, autoplot, hexagon, kmloverlay, remotesensing,
  satellite, multiple_flightpath, multilayers dock widgets
- `editor.py` — JSON config editor; `performance_settings.py`, `aircraft.py`
- `constants.py` — deprecated shim; real module is `mslib/utils/constants.py`
- `ui/` — Qt Designer sources; `qt5/` — pyuic5 output, NEVER edit by hand

### mslib/mscolab — collaboration server (Flask + SocketIO; entry: `mscolab`)

- `server.py` — thin app assembly (auth handlers, blueprint registration)
- `app/__init__.py` — Flask app factory; `blueprints/{operation,auth,chat,user,docs}`
- `file_manager.py` — operations, permissions, git-backed versioning (core logic)
- `chat_manager.py` — chat persistence; `sockets_manager.py` — socket.io events
- `models.py` — SQLAlchemy models; `migrations/` — Alembic, NEVER edit by hand
- `api/schemas.py` — request/response dataclasses per migrated REST route
  (type hints only, not checked at runtime); `api/endpoints.py` —
  endpoint-name registry (contract, growing)
- `api/events.py` — `SocketEvents` name registry (shared with client — contract)
- `api/message_type.py` — chat message enum (shared with client — contract)
- `conf.py` — `DefaultSettings`; `mscolab.py` — CLI (db init/seed/reset)
- `seed.py` — demo users/operations; `utils.py`, `auth.py`, `forms.py`

### mslib/mswms — WMS server (entry: `mswms`)

- `wms.py` — `WMSServer`, layer registration, GetMap/GetCapabilities handling
- `mss_plot_driver.py` — section drivers feeding data to styles
- `mpl_hsec*.py`, `mpl_vsec*.py`, `mpl_lsec*.py` — plot bases + style classes
  (horizontal/vertical/linear sections); plugin authors subclass these
- `dataaccess.py` — NetCDF file discovery/access; `generics.py` — generic styles
- `demodata.py` / `seed.py` — demo data generation; `gallery_builder.py` — docs gallery
- `app/`, `blueprints/` — Flask assembly; `mswms.py` — entry point

### mslib/utils — shared utilities (the base layer)

- `config.py` — `MSUIDefaultConfig` defaults + `config_loader` (THE config API)
- `constants.py` — MSUI config paths (moved here from msui in v11.1)
- `coordinate.py`, `units.py`, `time.py`, `thermolib.py` — pure science helpers
- `netCDF4tools.py` — NetCDF helpers; `ogcwms.py` — OWSLib WMS subclass
- `auth.py` — keyring/password handling; `qt.py` — Qt helpers
- `colordialog.py` — CustomColorDialog; `airdata.py` — airport/airspace download
- `migration/` — config-format migrations between major versions

### Smaller packages

- `mslib/autoplot/` — `mssautoplot` CLI: headless batch plotting driving the
  msui plotting stack (lives beside the GUI, not in the base layer)
- `mslib/plugins/io/` — flight-track import/export formats (csv, kml, gpx, text,
  flitestar); registered via config `import_plugins`/`export_plugins`
- `mslib/msidp/` — standalone SAML2 identity provider (entry: `msidp`)
- `mslib/support/qt_json_view/` — vendored JSON tree widget (config editor)

## Invariants

1. Never hand-edit `mslib/msui/qt5/ui_*.py` (pyuic5 output; sources in
   `mslib/msui/ui/`) or `mslib/mscolab/migrations/` (Alembic).
2. Client/server shared vocabulary lives ONLY in `mslib/mscolab/api/` (typed
   REST schemas + endpoint names, plus `events.py`/`message_type.py` for the
   socket vocabulary). Most REST payloads are still implicit dicts — when
   touching one that has no schema yet, update BOTH the blueprint handler and
   the client call site in `mslib/msui/mscolab.py`, and grep for the endpoint
   name. A route with a schema in `mslib/mscolab/api/schemas.py` only needs
   the dataclass changed; run `pixi run -e dev test-api` (schema self-consistency)
   and `tests/_test_mscolab/test_api_contract.py` (schemas against real routes).
3. All configuration access goes through `mslib.utils.config.config_loader`;
   never read the settings JSON directly.
4. Qt imports are allowed only in `mslib/msui` and `mslib/support` — and, until
   decoupling PR 4 moves them to msui, in the `mslib/utils` modules listed in the
   `utils-base-layer` contract (`qt`, `colordialog`, `config`, `airdata`,
   `migration/`).
5. New cross-package imports must satisfy the import-linter contracts in
   `setup.cfg` — never extend an `ignore_imports` list; its entries only shrink.

## Verification ladder (cheapest first)

| Command | Scope | Wall time |
|---|---|---|
| `pixi run -e dev lint` | flake8 | seconds |
| `pixi run -e dev lint-imports` | architecture contracts | seconds |
| `pixi run -e dev codespell` | spelling | seconds |
| `pixi run -e dev test-fast` | api + plugins + utils + meta, no servers | ~30 s |
| `pixi run -e dev test-api` | mscolab contract schema round-trips only | <1 s |
| `pixi run -e dev test-mscolab` / `test-mswms` | one server suite | minutes |
| `pixi run -e dev test-msui` | full GUI suite (offscreen Qt) | ~10 min |
| `pixi run -e dev test` | everything | ~13 min |

Tests live under `tests/_test_<package>/`, mirroring the package layout. The
MSColab server fixture forks only when a collected test needs it; Qt tests
require `QT_QPA_PLATFORM=offscreen` (the tasks set it).
