# MSS (Mission Support System)

## Setup

```
pixi shell          # activate dev environment (dev + docs features)
```

Python constraint: **< 3.12** (pinned in pixi.toml).

## Commands

```
# lint
pixi run -e dev flake8
git ls-files -z | xargs -0 pixi run -e dev codespell --check-filenames

# test (full suite)
pixi run -e dev env QT_QPA_PLATFORM=offscreen pytest -v -n logical --durations=20 --cov=mslib tests

# run a single test file
pixi run -e dev env QT_QPA_PLATFORM=offscreen pytest tests/test_something.py -v

# headless Qt (CI default, required on macOS)
QT_QPA_PLATFORM=offscreen pixi run -e dev -n logical pytest tests/

# coverage XML
pixi run -e dev coverage xml
```

## Architecture

Single package `mslib` with four main subpackages:

- **msui** — PyQt5 desktop GUI (`msui` entrypoint). Main window: `mslib.msui.msui_mainwindow`.
- **mscolab** — Flask collaborative server (`mscolab` entrypoint). Server: `mslib.mscolab.server`. DB models: `mslib.mscolab.models`.
- **mswms** — WMS geospatial service (`mswms` entrypoint). Driver: `mslib.mswms.mss_plot_driver`.
- **utils** — Shared utilities (config, auth, coordinate handling, netCDF tools).

CLI entrypoints (pixi env): `msui`, `mscolab`, `mswms`, `msidp`, `mssautoplot`, `mss`.

## Testing notes

- `conftest.py` auto-generates test config dirs in a temp directory and loads `mswms_settings` / `mscolab_settings` modules dynamically. Tests read from `tests.constants`.
- `tests/fixtures.py` provides session-scoped `mscolab_server`, `mswms_server`, `mscolab_app`, `mscolab_managers` fixtures plus Qt helpers (`qtbot`, `fail_if_open_message_boxes_left`).
- Qt tests require `QT_QPA_PLATFORM=offscreen` on headless machines.
- Keyring is mocked via `TestKeyring` in conftest — no real keyring needed.
- Tests clean config state after every test via `reset_config` autouse fixture.
- MSColab tests spin up a real Flask-SocketIO subprocess on a random port.

## Conventions

- Flake8: max-line-length 120. Ignored: E124,E125,E402,W503,W504,A005. Excluded dirs: `mslib/msui/qt5/`, `mslib/mscolab/migrations/`.
- Codespell: exceptions in `codespell-ignored-lines.txt`. Ignore list: PRES, degreeE, doubleClick, indexIn, socio-economic, EMAC, emac.
- Qt UI files (`qt5/ui_*.py`) are generated from `.ui` — do not edit by hand.
- No CRLF in git. Whitespace at EOL in `tests/data/example.txt` and `docs/samples/flight-tracks/example.txt` is intentional.
