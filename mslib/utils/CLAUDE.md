# mslib.utils — shared utilities

Purpose: the base layer — configuration, coordinates, units, time, thermodynamic
and NetCDF helpers used by every other package.
Global map: ../../ARCHITECTURE.md

## Layout

- `config.py` — `MSUIDefaultConfig` (all config keys as class attributes) +
  `config_loader(dataset=...)` (THE accessor) + JSON settings file IO +
  structural validation registries (`dict_option_structure` etc.)
- `constants.py` — MSUI config/cache paths (`MSUI_CONFIG_PATH`, `MSUI_SETTINGS`)
- `coordinate.py`, `units.py`, `time.py`, `thermolib.py` — pure functions; the
  safest modules to edit; keep them dependency-free
- `netCDF4tools.py` — NetCDF read helpers; `ogcwms.py` — hardened OWSLib WMS
- `auth.py` — keyring-backed credential storage (tests mock the keyring)
- `qt.py`, `colordialog.py` — Qt helpers (the only Qt code outside msui/support)
- `airdata.py` — airport/airspace downloads; `find_location.py`,
  `get_projection_params.py`
- `migration/` — converts settings files between major config versions

## May import

Nothing from `mslib` outside `utils` — this is the base layer, enforced by
the `gui-isolation` contract in setup.cfg.

## Invariants

- New config keys: add the attribute on `MSUIDefaultConfig` AND, if dict/list
  shaped, the matching entry in `dict_option_structure`/`list_option_structure`
  and a line in `config_descriptions`.
- Everything except `qt.py`/`colordialog.py` (Qt)  must stay importable without Qt
  or a running server.

## Verify

`pixi run -e dev test-utils` (fast, no servers forked) or
`pixi run -e dev test-fast` for the whole no-server tier.
