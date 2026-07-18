# mslib.mswms — WMS server

Purpose: OGC Web Map Service rendering horizontal/vertical/linear sections of
forecast NetCDF data with matplotlib. Consumed by the GUI over HTTP only.
Global map: ../../ARCHITECTURE.md

## Layout

- `wms.py` — `WMSServer`: layer registries, GetCapabilities/GetMap; module-level
  `server = WMSServer()` built at import from the `mswms_settings` module
- `mss_plot_driver.py` — `{Horizontal,Vertical,Linear}SectionDriver`: load data,
  drive a style's `plot()`
- `mpl_hsec.py` / `mpl_vsec.py` / `mpl_lsec.py` — style base classes
- `mpl_hsec_styles.py` / `mpl_vsec_styles.py` / `mpl_lsec_styles.py` — concrete
  styles; plugin authors subclass the bases and register via
  `mswms_settings.register_{horizontal,vertical,linear}_layers`
- `dataaccess.py` — `DefaultDataAccess`: scans the data dir (at `setup()`),
  maps CF variable names to files
- `demodata.py` / `seed.py` — demo data + server config generation
- `app/`, `blueprints/` — Flask assembly; `gallery_builder.py` — docs gallery

## May import

`mslib.utils` only. Never `mslib.msui` (exception: `blueprints/docs` icons,
grandfathered) or `mslib.mscolab`. Enforced: `wms-isolation` contract.

## Invariants

- Configuration comes from a user-supplied `mswms_settings` module (tests
  generate one in conftest); there is no config_loader here.
- `WMSServer.__init__` scans data dirs — test data must exist before import
  (root conftest guarantees this; don't move that seeding).
- New styles: subclass a base from `mpl_{h,v,l}sec.py`, set `name`/`title`/
  `styles`, implement `_plot_style()`; register per `(dataset, name)` —
  duplicates raise `ValueError`.

## Verify

`pixi run -e dev test-mswms`; a single style renders via
`pixi run -e dev env QT_QPA_PLATFORM=offscreen pytest tests/_test_mswms/test_wms.py -q`.
