# mslib.plugins — flight-track I/O plugins

Purpose: import/export of flight tracks in foreign formats (csv, kml, gpx,
text, flitestar). The reference implementations for user-supplied plugins.
Global map: ../../ARCHITECTURE.md

## Layout

- `io/csv.py`, `io/text.py`, `io/flitestar.py` — read/write via
  `mslib.msui.flighttrack.Waypoint` (grandfathered import)
- `io/kml.py`, `io/gpx.py` — read-only importers

## Contract

Each importer exposes `load_from_<fmt>(filename)` returning
`(name, [Waypoint])`; each exporter `save_to_<fmt>(filename, name, waypoints)`.
Users register them in the settings JSON under `import_plugins` /
`export_plugins` as `[extension, module, function(, pickertype)]` — keep
signatures stable, third-party configs reference them.

## Verify

`pixi run -e dev test-plugins` (pure I/O round-trips, seconds).
