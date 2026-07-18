# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```
pixi shell -e dev          # activate dev environment (dev + docs features)
```

Python constraint: **< 3.12** (pinned in pixi.toml).

## Commands

```bash
pixi run -e dev lint            # flake8 over tracked .py files
pixi run -e dev lint-imports    # architectural import contracts (setup.cfg)
pixi run -e dev codespell       # spelling
pixi run -e dev test-fast       # plugins + utils + meta; no servers, fastest signal
pixi run -e dev test-msui       # GUI suite (offscreen Qt)
pixi run -e dev test-mscolab    # collaboration-server suite
pixi run -e dev test-mswms      # WMS-server suite
pixi run -e dev test            # full suite (~13 min)

# single test file
pixi run -e dev env QT_QPA_PLATFORM=offscreen pytest tests/_test_msui/test_topview.py -v

# coverage XML
pixi run -e dev coverage xml
```

## Architecture

Start with `ARCHITECTURE.md` (package DAG, module index, invariants,
verification ladder). Each package under `mslib/` has its own `CLAUDE.md`
card with layout, allowed imports, and how to verify changes there.
Dependency direction is enforced by import-linter (`setup.cfg`).

Single package `mslib` with four main subpackages:

- **msui** — PyQt5 desktop GUI (`msui` entrypoint). Main window: `mslib.msui.msui_mainwindow`.
- **mscolab** — Flask collaborative server (`mscolab` entrypoint). Server: `mslib.mscolab.server`. DB models: `mslib.mscolab.models`.
- **mswms** — WMS geospatial service (`mswms` entrypoint). Driver: `mslib.mswms.mss_plot_driver`.
- **utils** — Shared utilities (config, auth, coordinate handling, netCDF tools).

CLI entrypoints (pixi env): `msui`, `mscolab`, `mswms`, `msidp`, `mssautoplot`, `mss`.

Tests mirror the package structure under `tests/` with subdirectories `_test_mscolab/`, `_test_msui/`, `_test_mswms/`, `_test_plugins/`, `_test_utils/`.

## Testing notes

- `conftest.py` auto-generates test config dirs in a temp directory and loads `mswms_settings` / `mscolab_settings` modules dynamically. Tests read from `tests.constants`.
- `tests/fixtures.py` provides session-scoped `mscolab_server`, `mswms_server`, `mscolab_app`, `mscolab_managers` fixtures plus Qt helpers (`qtbot`, `fail_if_open_message_boxes_left`).
- Qt tests require `QT_QPA_PLATFORM=offscreen` on headless machines.
- Keyring is mocked via `TestKeyring` in conftest — no real keyring needed.
- Tests clean config state after every test via `reset_config` autouse fixture.
- MSColab tests fork a real Flask-SocketIO server (multiprocessing fork, random port); the fork happens only in sessions that contain tests needing it.

## Conventions

- Flake8: max-line-length 120. Ignored: E124,E125,E402,W503,W504,A005. Excluded dirs: `mslib/msui/qt5/`, `mslib/mscolab/migrations/`.
- Codespell: exceptions in `codespell-ignored-lines.txt`. Ignore list: PRES, degreeE, doubleClick, indexIn, socio-economic, EMAC, emac.
- Qt UI files (`qt5/ui_*.py`) are generated from `.ui` — do not edit by hand.
- No CRLF in git. Whitespace at EOL in `tests/data/example.txt` and `docs/samples/flight-tracks/example.txt` is intentional.
