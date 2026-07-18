# MSS Architecture Map

This is the global context map for the MSS codebase — read this first, then the
`CLAUDE.md` card inside the package you are changing. The dependency rules below
are machine-enforced by import-linter (`pixi run -e dev lint-imports`, config in
`setup.cfg`); if this file and the code disagree, CI is the arbiter.

## Packages and dependency direction

Arrows mean "may import". Anything not drawn is forbidden.

```
                 ┌────────────┐
                 │ mslib.msui │  PyQt5 desktop client (GUI)
                 └─────┬──────┘
        ┌──────────────┼───────────────────────┐
        ▼              ▼                       ▼
 mslib.mscolab   mslib.support           mslib.utils
 (events/message_ (vendored qt_json_view) (shared: config,
  type constants                           coordinates, units,
  ONLY)                                    netCDF, auth, qt helpers)
                                               ▲
   mslib.mswms ────────────────────────────────┘
   (WMS server; never imports msui/mscolab)

   mslib.plugins  → mslib.msui.flighttrack (grandfathered), mslib.utils
   mslib.msidp    → standalone SAML identity provider
```

Grandfathered violations (do not add new ones; the lists live in `setup.cfg`
under `ignore_imports` and must only shrink):

- `utils.{config,auth,airdata,migration.*}` import `msui.constants` (path constants).
- `utils.mssautoplot` drives the GUI plotting stack headlessly.
- `plugins.io.{csv,text,flitestar}` import `msui.flighttrack`.
- `{mscolab,mswms}.blueprints.docs` import `msui.icons` — invisible to the
  linter (`blueprints/` are namespace packages without `__init__.py`), but
  equally discouraged.

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
- `constants.py` — MSUI config paths (imported by utils — grandfathered)
- `ui/` — Qt Designer sources; `qt5/` — pyuic5 output, NEVER edit by hand

### mslib/mscolab — collaboration server (Flask + SocketIO; entry: `mscolab`)

- `server.py` — thin app assembly (auth handlers, blueprint registration)
- `app/__init__.py` — Flask app factory; `blueprints/{operation,auth,chat,user,docs}`
- `file_manager.py` — operations, permissions, git-backed versioning (core logic)
- `chat_manager.py` — chat persistence; `sockets_manager.py` — socket.io events
- `models.py` — SQLAlchemy models; `migrations/` — Alembic, NEVER edit by hand
- `events.py` — `SocketEvents` name registry (shared with client — contract)
- `message_type.py` — chat message enum (shared with client — contract)
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

### mslib/utils — shared utilities (entry: `mssautoplot`)

- `config.py` — `MSUIDefaultConfig` defaults + `config_loader` (THE config API)
- `coordinate.py`, `units.py`, `time.py`, `thermolib.py` — pure science helpers
- `netCDF4tools.py` — NetCDF helpers; `ogcwms.py` — OWSLib WMS subclass
- `auth.py` — keyring/password handling; `qt.py` — Qt helpers
- `colordialog.py` — CustomColorDialog; `airdata.py` — airport/airspace download
- `mssautoplot.py` — headless batch plotting CLI (drives msui plotting stack)
- `migration/` — config-format migrations between major versions

### Smaller packages

- `mslib/plugins/io/` — flight-track import/export formats (csv, kml, gpx, text,
  flitestar); registered via config `import_plugins`/`export_plugins`
- `mslib/msidp/` — standalone SAML2 identity provider (entry: `msidp`)
- `mslib/support/qt_json_view/` — vendored JSON tree widget (config editor)

## Invariants

1. Never hand-edit `mslib/msui/qt5/ui_*.py` (pyuic5 output; sources in
   `mslib/msui/ui/`) or `mslib/mscolab/migrations/` (Alembic).
2. Client/server shared vocabulary lives ONLY in `mslib/mscolab/events.py` and
   `mslib/mscolab/message_type.py`. REST payloads are implicit dicts today —
   when touching one, update BOTH the blueprint handler and the client call
   site in `mslib/msui/mscolab.py`, and grep for the endpoint name.
3. All configuration access goes through `mslib.utils.config.config_loader`;
   never read the settings JSON directly.
4. Qt imports are allowed only in `mslib/msui`, `mslib/utils/{qt,colordialog}.py`,
   and `mslib/support`.
5. New cross-package imports must satisfy the import-linter contracts in
   `setup.cfg` — never extend an `ignore_imports` list.

## Verification ladder (cheapest first)

| Command | Scope | Wall time |
|---|---|---|
| `pixi run -e dev lint` | flake8 | seconds |
| `pixi run -e dev lint-imports` | architecture contracts | seconds |
| `pixi run -e dev codespell` | spelling | seconds |
| `pixi run -e dev test-fast` | plugins + utils + meta, no servers | ~30 s |
| `pixi run -e dev test-mscolab` / `test-mswms` | one server suite | minutes |
| `pixi run -e dev test-msui` | full GUI suite (offscreen Qt) | ~10 min |
| `pixi run -e dev test` | everything | ~13 min |

Tests live under `tests/_test_<package>/`, mirroring the package layout. The
MSColab server fixture forks only when a collected test needs it; Qt tests
require `QT_QPA_PLATFORM=offscreen` (the tasks set it).
