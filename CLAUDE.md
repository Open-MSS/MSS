# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
- Enter development environment: `pixi shell -e dev`
- Install dependencies: `pixi install`

### Testing
- Run all tests: `pixi run -e dev env QT_QPA_PLATFORM=offscreen pytest -n logical tests`
- Run a specific test file: `pixi run -e dev env QT_QPA_PLATFORM=offscreen pytest tests/test_file.py`
- Run a specific test function: `pixi run -e dev env QT_QPA_PLATFORM=offscreen pytest tests/test_file.py::test_function`

### Linting & Quality
- Lint code: `pixi run -e dev flake8 mslib/ tests/`
- Check spelling: `pixi run -e dev codespell`

## Architecture Overview

The Mission Support System (MSS) is a Python-based suite for planning atmospheric research flights. The codebase is organized as a single package `mslib` containing several distinct applications and shared utilities.

### Core Components (`mslib/`)
- **`msui/`**: The primary GUI application built with PyQt.
- **`mscolab/`**: Collaboration server using Flask and Flask-SocketIO for flight planning.
- **`mswms/`**: Web Map Service System using Flask, providing server-side functionality.
- **`msidp/`**: Identity Provider service for authentication (SAML).
- **`utils/`**: Shared utility functions, including `mssautoplot` for automated plotting.
- **`support/`**: Support modules used across the different applications.
- **`plugins/`**: Extensibility points for adding new functionality.

### Key Technologies
- **GUI**: PyQt
- **Web**: Flask, SQLAlchemy, Flask-SocketIO
- **Scientific Stack**: NumPy, SciPy, Matplotlib, NetCDF4, MetPy, Skyfield
- **Package Management**: Pixi (conda-forge)
