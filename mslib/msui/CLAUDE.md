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
- `ui/` — Qt Designer `.ui` sources; `qt5/` — pyuic5 OUTPUT, never edit

## May import

`mslib.utils`, `mslib.support`, and ONLY `mslib.mscolab.{events,message_type}`
from the server package (enforced: `server-isolation` contract in setup.cfg).
Never `mslib.mswms` — WMS is consumed over HTTP.

## Invariants

- Never edit `qt5/ui_*.py`; change the `.ui` file and regenerate with pyuic5.
- REST payloads to MSColab are implicit dicts: when changing a call in
  `mscolab.py`, update the matching blueprint in
  `mslib/mscolab/blueprints/` in the same commit.
- Config access via `mslib.utils.config.config_loader`; per-widget Qt state
  via `save_settings_qsettings`/`load_settings_qsettings`.
- Message boxes in tests are mocked; an unhandled QMessageBox fails the test.

## Verify

`pixi run -e dev test-msui` (~10 min) or a single file:
`pixi run -e dev env QT_QPA_PLATFORM=offscreen pytest tests/_test_msui/test_<x>.py -q`
Known flaky: `test_topview.py::Test_TopViewWMS::test_server_getmap`.
