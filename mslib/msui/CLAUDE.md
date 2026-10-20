# mslib.msui — PyQt5 desktop client

Purpose: the MSUI GUI. Views (top/side/table/linear) render flight tracks and
WMS layers; dockwidgets add overlays; the MSColab client lives here too.
Global map: ../../ARCHITECTURE.md

## Layout

- `msui_mainwindow.py` — main window, flight-track list, view registry
- `viewwindows.py` — base classes; concrete views multiply-inherit
  `(MSUIMplViewWindow, ui.Ui_<View>Window)` and call `setupUi(self)`
- `topview.py` / `sideview.py` / `tableview.py` / `linearview.py` — views
- `mpl_qtwidget.py` / `mpl_map.py` / `mpl_pathinteractor.py` — matplotlib canvas
  stack; waypoint interaction happens in `mpl_pathinteractor`
- `flighttrack.py` — `WaypointsTableModel`, the shared data model
- `wms_control.py` — WMS client widget + HTTP service + threaded fetcher/cache
- `mscolab.py` + `socket_control.py` + `mscolab_*.py` — MSColab client; network
  events arrive as Qt signals emitted by `socket_control.ConnectionManager`
- `*_dockwidget.py` — per-feature dock widgets
- `utils/` — helpers of the client (moved from `mslib/utils`, same module names):
  `config.py` — `MSUIDefaultConfig` (all config keys as class attributes) +
  `config_loader(dataset=...)` (THE accessor) + JSON settings file IO +
  structural validation registries (`dict_option_structure` etc.);
  `constants.py` — MSUI config/cache paths; `qt.py`, `colordialog.py` — Qt
  helpers; `auth.py` — keyring-backed credentials (tests mock the keyring);
  `ogcwms.py` — thin wrapper around the OWSLib WMS classes (version negotiation,
  capabilities document, all dimensions, proxies; it patches
  `owslib.map.wms111/wms130.ContentMetadata.__init__`); `service_manager.py`; `airdata.py`,
  `find_location.py`; `migration/` — converts settings files between major
  config versions
- `constants.py` — deprecated shim; import `mslib.msui.utils.constants` instead
- `ui/` — Qt Designer `.ui` sources; `qt5/` — pyuic5 OUTPUT, never edit

## May import

`mslib.utils`, `mslib.support`, and ONLY `mslib.mscolab.api.*` from the server
package (enforced: `server-isolation` contract in setup.cfg). Never
`mslib.mswms` — WMS is consumed over HTTP — and never the server stack (Flask,
SQLAlchemy; `client-without-server-stack` contract).

## Invariants

- Never edit `qt5/ui_*.py`; change the `.ui` file and regenerate with pyuic5.
- `icons/16x16/favicon.ico` and `icons/64x64/mss-logo.png` have copies in
  `mslib/{mswms,mscolab}/blueprints/docs/static/icons/` (the servers must not
  import msui); change all three together — `tests/test_meta.py` checks it.
- REST payloads to MSColab are mostly still implicit dicts: when changing a
  call in `mscolab.py`, update the matching blueprint in
  `mslib/mscolab/blueprints/` in the same commit. A handful of routes (see
  `mslib/mscolab/api/endpoints.py`) are migrated to typed dataclasses in
  `mslib/mscolab/api/schemas.py` instead — build/parse via those, don't
  hand-roll a dict for a route that already has a schema.
- Config access via `mslib.msui.utils.config.config_loader`; per-widget Qt state
  via `save_settings_qsettings`/`load_settings_qsettings`.
- New config keys: add the attribute on `MSUIDefaultConfig` AND, if dict/list
  shaped, the matching entry in `dict_option_structure`/`list_option_structure`
  and a line in `config_descriptions`.
- Message boxes in tests are mocked; an unhandled QMessageBox fails the test.
- Texts from servers or other users (WMS capabilities and errors, MSColab names,
  exception messages) never reach Qt as rich text: `QLabel.setTextFormat(Qt.PlainText)`,
  `html.escape` inside own HTML, and for tooltips and message boxes
  `mslib.msui.utils.qt.plain_text_as_html`, `show_popup` or `plain_text_message_box`.
  Qt loads `<img src="file://host/share/x">` from rich text (NTLM leak).
  `tests/_test_msui/test_qt.py` fails for a message box or tooltip whose text is
  not a constant and doesn't go through `plain_text_as_html`.
- Passwords and tokens go only to their own server: check with
  `mslib.msui.utils.auth.same_origin` before sending them to a URL a server named.

## Verify

`pixi run -e dev test-msui` (~10 min) or a single file:
`pixi run -e dev env QT_QPA_PLATFORM=offscreen pytest tests/_test_msui/test_<x>.py -q`
Known flaky: `test_topview.py::Test_TopViewWMS::test_server_getmap`.
