# -*- coding: utf-8 -*-
"""

    tests.fixtures
    ~~~~~~~~~~~~~~

    This module provides utils for pytest to test mslib modules

    This file is part of MSS.

    :copyright: Copyright 2023-2026 by the MSS team, see AUTHORS.
    :license: APACHE-2.0, see LICENSE for details.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
import copy
import multiprocessing
import multiprocessing.queues
import time
import urllib.parse
from contextlib import contextmanager
from pathlib import Path

import pytest

from tests.server_setup import ensure_mscolab_config, ensure_mswms_testdata

# The server fixtures of all suites. Root conftest.py loads this module for every test session, so it imports
# nothing but the standard library and pytest at module level: mslib.mscolab, mslib.mswms, socketio and
# werkzeug are imported inside the fixtures that need them. That keeps importing this module cheap and free of
# side effects (mslib.mscolab.server and mslib.mswms.mswms bind their configuration at import time), and it lets
# the suite of every package run with only that package installed. The fixtures of the desktop client
# (keyring, msui configuration, Qt) are in tests/msui_fixtures.py.


@pytest.fixture(scope="session")
def mscolab_session_app():
    """Session-scoped fixture that provides the WSGI app instance MSColab is served with.

    This fixture should not be used in tests. Instead use :func:`mscolab_server_app`,
    which handles per-test cleanup as well.
    """
    # mslib.mscolab.server binds its SQLAlchemy URI from mscolab_settings at import time
    ensure_mscolab_config()
    from mslib.mscolab.server import create_server_app
    return create_server_app()


# TODO: This fixture used to be autouse here, which is a crutch. It seems like if it is not autouse
# some tests can bring the pytest processes objects into a state in which the MSColab server will have
# trouble starting the Flask-SocketIO server once it is forked. With autouse the fork happens first,
# before any test runs. After that, the pytest process can no longer affect the now-running server, thus
# mitigating the issue. This is my understanding at time of writing.
#
# It's no longer unconditionally autouse here (that forked a server even for sessions that never touch
# mscolab/msui, e.g. test-fast). Instead, root conftest.py's `_ensure_mscolab_server_if_needed` fixture
# is autouse and forces this fixture -- still as the very first thing in the session, before any test
# touches Qt or multiprocessing state -- whenever the collected tests actually need it (checked via
# `mscolab_session_server` appearing in some item's fixture closure). That check has to live in root
# conftest.py rather than a directory-scoped one: fixture autouse-ness only applies within its own
# directory subtree, but the fork-before-Qt ordering constraint is a whole-session/whole-process concern
# that can't be satisfied if some other directory's test runs first in the same worker.
#
# This issue would also be avoided if the background server process wasn't started with multiprocessing and a fork, but
# with a real subprocess, which would solve some other issues (e.g. testing on Windows) as well.
@pytest.fixture(scope="session")
def mscolab_session_server(mscolab_session_app):
    """Session-scoped fixture that provides a running MSColab server.

    This fixture should not be used in tests. Instead use :func:`mscolab_server`, which
    handles per-test cleanup as well.
    """
    import socketio
    with _running_server(mscolab_session_app) as url:
        # Wait until the Flask-SocketIO server is ready for connections
        sio = socketio.Client()
        sio.connect(url, retry=True, wait_timeout=60)
        sio.disconnect()
        del sio
        yield url


@pytest.fixture
def reset_mscolab(mscolab_session_app):
    """Cleans up before every test that uses MSColab.

    This fixture is not explicitly needed in tests, it is used in the other fixtures to
    do the cleanup actions.
    """
    from mslib.mscolab.mscolab import handle_db_reset
    with mscolab_session_app.app_context():
        handle_db_reset(verbose=False)


def _isolated_mscolab_settings(tmp_path):
    """Build a copy of the MSColab settings with every path below ``tmp_path``.

    An app created from these settings has a database and an operations data directory
    of its own, so it shares no state with any other app.
    """
    from mslib.mscolab.conf import mscolab_settings
    settings = copy.copy(mscolab_settings)
    data_dir = tmp_path / "mscolab"
    settings.DATA_DIR = str(data_dir)
    settings.OPERATIONS_DATA = str(data_dir / "filedata")
    settings.UPLOAD_FOLDER = str(data_dir / "filedata" / "uploads")
    settings.SSO_DIR = str(data_dir / "datasso")
    settings.SQLALCHEMY_DATABASE_URI = "sqlite:///" + str(data_dir / "mscolab.db")
    return settings


@pytest.fixture
def mscolab_app(tmp_path):
    """Fixture that provides an MSColab WSGI app instance of its own.

    The app is created freshly for every test and brings its own, empty database along,
    so tests using it are independent of each other. Tests that need to look into the
    database of the server started by :func:`mscolab_server` have to use
    :func:`mscolab_server_app` instead.

    :returns: A WSGI app instance.
    """
    # the settings are loaded already: by tests/_test_mscolab/conftest.py, the only suite using this fixture
    from mslib.mscolab.models import db
    from mslib.mscolab.server import create_server_app
    settings = _isolated_mscolab_settings(tmp_path)
    Path(settings.DATA_DIR).mkdir(parents=True, exist_ok=True)
    app = create_server_app(settings)
    yield app
    # Release the connections this app's engine holds, they would otherwise stay open
    # until the app is garbage collected.
    with app.app_context():
        db.engine.dispose()


@pytest.fixture
def mscolab_managers(mscolab_app):
    """Fixture that provides the managers of the app of :func:`mscolab_app`.

    :returns: A tuple (SocketIO, ChatManager, FileManager).
    """
    return (mscolab_app.extensions['sockio'],
            mscolab_app.extensions['cm'],
            mscolab_app.extensions['fm'])


@pytest.fixture
def mscolab_server_app(mscolab_session_app, reset_mscolab):
    """Fixture that provides the WSGI app instance MSColab is served with.

    Use this to inspect the state of the server provided by :func:`mscolab_server`; it
    is the same app, so it shares the database with it. Tests that do not need a running
    server should use the independent :func:`mscolab_app` instead.

    :returns: A WSGI app instance.
    """
    return mscolab_session_app


@pytest.fixture
def mscolab_server(mscolab_session_server, reset_mscolab):
    """Fixture that provides a running MSColab server and does cleanup actions.

    The suites of the desktop client extend it, see tests/msui_fixtures.py.

    :returns: The URL where the server is running.
    """
    return mscolab_session_server


@pytest.fixture(scope="session")
def mswms_app():
    """Fixture that provides the MSWMS WSGI app instance."""
    # Must run before mslib.mswms.mswms is imported: it binds its config from
    # mswms_settings (and registers the demo layers) at import time.
    ensure_mswms_testdata()
    import mslib.mswms.mswms

    yield mslib.mswms.mswms.application
    # Close all open NetCDF4 datasets to release file handles
    from mslib.mswms import wms
    wms.server.close_datasets()


@pytest.fixture(scope="session")
def mswms_server(mswms_app):
    """Fixture that provides a running MSWMS server.

    :returns: The URL where the server is running.
    """
    with _running_server(mswms_app) as url:
        yield url


def _start_server(host, port_queue, app):
    """
    Starts a werkzeug server and sends the chosen port back to the parent process.
    """
    from werkzeug.serving import make_server
    srv = make_server(host, 0, app, threaded=True)
    port = srv.server_address[1]
    port_queue.put(port)
    srv.serve_forever()


@contextmanager
def _running_server(app):
    """Context manager that starts the app in a werkzeug server and returns its URL."""
    from tests.utils import is_url_response_ok
    scheme = "http"
    host = "127.0.0.1"

    if "fork" not in multiprocessing.get_all_start_methods():
        pytest.skip("requires the multiprocessing start_method 'fork', which is unavailable on this system")

    ctx = multiprocessing.get_context("fork")
    # We are using a queue to retrieve the port selected in the child process.
    port_queue = ctx.Queue()

    process = ctx.Process(target=_start_server, args=(host, port_queue, app), daemon=True)
    try:
        process.start()
        # Retrieve the port from the queue
        try:
            port = port_queue.get(timeout=10)
        except multiprocessing.queues.Empty:
            raise RuntimeError("Could not retrieve port from server process")

        url = f"{scheme}://{host}:{port}"
        app.config['URL'] = url

        start_time = time.time()
        sleep_time = 0.01
        time_out = 20
        # we check only for the root url, index.html may take longer
        readiness_url = urllib.parse.urljoin(url, "/")
        while not is_url_response_ok(readiness_url):
            if not process.is_alive():
                # show the exitcode for further debugging
                raise RuntimeError(f"Server process exited early with code {process.exitcode} at {url}")
            if (time.time() - start_time) > time_out:
                raise RuntimeError(f"Server did not start within {time_out} seconds at {url}")
            time.sleep(sleep_time)
            sleep_time *= 2
            if sleep_time > 1:
                sleep_time = 1
        yield url
    finally:
        process.terminate()
        process.join(timeout=10)
        if process.is_alive():
            # when it is still alive after 10 seconds, kill it
            process.kill()
            process.join(timeout=5)
        process.close()
