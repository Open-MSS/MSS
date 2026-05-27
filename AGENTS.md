# AGENTS.md

## Environment & Toolchain
- **Runtime**: Python < 3.12.
- **Env Manager**: Pixi. Use `pixi shell -e dev` for development.
- **Verification Flow**: `flake8 mslib/` -> `codespell` -> `pytest`.

## Architecture Notes
- **Structure**: Single package `mslib` containing multiple applications.
- **Entrypoints**: Defined in `pyproject.toml` (scripts: `mss`, `mscolab`, `msidp`, `mswms`, `mssautoplot`).
- **Components**: 
  - `msui`: PyQt GUI.
  - `mscolab`/`mswms`/`msidp`: Flask-based services.

## Constraints & Quirks
- **GUI Tests**: Uses `pytest-qt`.
- **Database**: `mscolab` uses `flask-migrate` for schema management.
- **OS Dependencies**: Some dependencies (e.g., `dbus-python`, `libxmlsec1`) are platform-specific in `pixi.toml`.
- **Documentation**: Refer to `CLAUDE.md` for exact developer commands.
