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
- `basic_auth.py` — password check of the basic HTTP auth of mswms, mscolab and
  `auth.wsgi` (argon2, deprecated MD5); `python -m mslib.utils.basic_auth` prints a hash
- `qt.py`, `colordialog.py` — Qt helpers (the only Qt code outside msui/support)
- `airdata.py` — airport/airspace downloads; `find_location.py`,
  `get_projection_params.py`
- `migration/` — converts settings files between major config versions

## May import

Nothing from `mslib` outside `utils`, and no Qt, keyring or server stack
(Flask & co., SQLAlchemy, Werkzeug, pysaml2) — this is the base layer, enforced
by the `gui-isolation` and `utils-base-layer` contracts in setup.cfg. The
imports that still break this are listed there as to-dos of the package
split (#2307); don't add more:

- Qt: `qt`, `colordialog`, `config`, `airdata` and `migration/` import PyQt5
  (`config` and `migration/` also `mslib.support`), so `find_location` and
  `ogcwms`, which import `config`, need Qt as well;
- keyring: `auth`, `migration/update_json_file_to_version_eight`;
- Flask: `auth` (`send_email`).

## Invariants

- New config keys: add the attribute on `MSUIDefaultConfig` AND, if dict/list
  shaped, the matching entry in `dict_option_structure`/`list_option_structure`
  and a line in `config_descriptions`.
- Everything except the modules above that need Qt (`qt`, `colordialog`,
  `config`, `airdata`, `migration/`, `find_location`, `ogcwms`) must stay
  importable without Qt or a running server.

## Verify

`pixi run -e dev test-utils` (fast, no servers forked) or
`pixi run -e dev test-fast` for the whole no-server tier.
