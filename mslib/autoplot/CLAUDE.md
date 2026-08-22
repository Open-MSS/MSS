# mslib.autoplot — headless batch plotting

Purpose: the `mssautoplot` CLI: renders top/side view plots from a JSON config
without showing the GUI, by driving the msui plotting stack headlessly.
Global map: ../../ARCHITECTURE.md

## Layout

- `__init__.py` — the whole CLI (click-based `main`, `load_from_ftml`,
  TopView/SideView plotting drivers)

## May import

`mslib.utils` and `mslib.msui` (this package exists precisely so that the
GUI dependency does not sit inside the base layer mslib.utils).
Never `mslib.mscolab` or `mslib.mswms` (enforced in setup.cfg).

## Verify

`pixi run -e dev env QT_QPA_PLATFORM=offscreen pytest tests/_test_utils/test_mssautoplot.py -q`
and `mssautoplot --help` inside the dev env.
