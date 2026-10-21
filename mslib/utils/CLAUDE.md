# mslib.utils — shared utilities

Purpose: the base layer — coordinates, units, time, thermodynamic and NetCDF
helpers and the small helpers the servers share; used by every other package.
The helpers of the desktop client (Qt, the msui configuration, keyring, airdata,
the WMS client) live in `mslib/msui/utils/`.
Global map: ../../ARCHITECTURE.md

## Layout

- `coordinate.py`, `units.py`, `time.py`, `thermolib.py` — pure functions; the
  safest modules to edit; keep them dependency-free
- `netCDF4tools.py` — xarray-based NetCDF read helpers (variable identification
  by CF standard name, `open_mfdataset_commondims()`); `get_projection_params.py`
- `basic_auth.py` — password check of the basic HTTP auth of mswms, mscolab and
  `auth.wsgi` (argon2, deprecated MD5); `python -m mslib.utils.basic_auth` prints a hash
- `file_exists.py`, `get_content.py` — docs pages of the servers;
  `release_info.py` — newest release on GitHub; `loggerdef.py`;
  `verify_waypoint_data.py`
- `__init__.py` — `FatalUserError`, `setup_logging`, `prefix_route`

## May import

Nothing from `mslib` outside `utils`, and no Qt, keyring or server stack
(Flask & co., SQLAlchemy, Werkzeug, pysaml2) — this is the base layer, enforced
by the `gui-isolation` and `utils-base-layer` contracts in setup.cfg, with no
exception. Code that needs Qt or keyring belongs to `mslib/msui/utils/`.

## Invariants

- Everything must stay importable without Qt, keyring or a running server: the
  servers ship with this package, without the desktop client.

## Verify

`pixi run -e dev test-utils` (fast, no servers forked) or
`pixi run -e dev test-fast` for the whole no-server tier.
