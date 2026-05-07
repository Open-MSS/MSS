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
import pytest
import mock
import os
import subprocess
import sys
import time
import urllib
import socket
import socketio
import requests
import mslib.mswms.mswms
import mslib.mswms.wms
import mslib.mswms.gallery_builder

from PyQt5 import QtWidgets
from contextlib import contextmanager
from mslib.mscolab.server import APP, sockio, cm, fm
from mslib.mscolab.mscolab import handle_db_reset
from mslib.utils.config import modify_config_file
from tests.utils import is_url_response_ok


@pytest.fixture
def fail_if_open_message_boxes_left():
    # Mock every MessageBox widget in the test suite to avoid unwanted freezes on unhandled error popups etc.
    with mock.patch("PyQt5.QtWidgets.QMessageBox.question") as q, \
            mock.patch("PyQt5.QtWidgets.QMessageBox.information") as i, \
            mock.patch("PyQt5.QtWidgets.QMessageBox.critical") as c, \
            mock.patch("PyQt5.QtWidgets.QMessageBox.warning") as w:
        yield

        # Fail a test if there are any Qt message boxes left open at the end
        if any(box.call_count > 0 for box in [q, i, c, w]):
            summary = "\n".join([f"PyQt5.QtWidgets.QMessageBox.{box()._extract_mock_name()}: {box.mock_calls[:-1]}"
                                 for box in [q, i, c, w] if box.call_count > 0])
            pytest.fail(f"An unhandled message box popped up during your test!\n{summary}")


@pytest.fixture
def msui_configs(tmp_path):
    modify_config_file({"mss_dir": str(tmp_path)})


@pytest.fixture
def qtbot(qtbot, fail_if_open_message_boxes_left, msui_configs):
    """Fixture that re-defines the qtbot fixture from pytest-qt with additional checks."""
    yield qtbot
    # Drop any matplotlib figures from Gcf BEFORE scheduling Qt deletion, otherwise
    # matplotlib's atexit Gcf.destroy_all trips over a dead NavigationToolbar2QT at
    # worker shutdown ("wrapped C/C++ object has been deleted").
    try:
        import matplotlib.pyplot as plt
        plt.close("all")
    except ImportError:
        pass
    # Schedule destruction of any leftover top-level widgets BEFORE the drain wait
    # below. Tests often only call hide(), which keeps the widget (and any sockets
    # it owns) alive. deleteLater() queues destruction without firing close events
    # (close() would trigger "save changes?" dialogs); the subsequent qtbot.wait
    # gives the Qt event loop time to actually process the deletions.
    for qobject in set(QtWidgets.QApplication.topLevelWindows() + QtWidgets.QApplication.topLevelWidgets()):
        try:
            delete_later = getattr(qobject, "deleteLater", None)
            if delete_later is not None:
                delete_later()
        # Some objects are already deleted; ignore those.
        except RuntimeError:
            pass
    # Drain the Qt event loop so destruction (and any socket disconnects it triggers)
    # actually completes before the next test starts.
    qtbot.wait(5000)


@pytest.fixture(scope="session")
def mscolab_session_app():
    """Session-scoped fixture that provides the WSGI app instance for MSColab.

    This fixture should not be used in tests. Instead use :func:`mscolab_app`, which
    handles per-test cleanup as well.
    """
    _app = APP
    _app.config['SQLALCHEMY_DATABASE_URI'] = APP.config['SQLALCHEMY_DATABASE_URI']
    _app.config['OPERATIONS_DATA'] = APP.config['OPERATIONS_DATA']
    _app.config['UPLOAD_FOLDER'] = APP.config['UPLOAD_FOLDER']
    return _app


@pytest.fixture(scope="session")
def mscolab_session_managers(mscolab_session_app):
    """Session-scoped fixture that provides the managers for the MSColab app.

    This fixture should not be used in tests. Instead use :func:`mscolab_managers`,
    which handles per-test cleanup as well.
    """
    return sockio, cm, fm


@pytest.fixture(scope="session")
def mscolab_session_server(mscolab_session_app, mscolab_session_managers, mscolab_server_config_dir):
    """Session-scoped fixture that provides a running MSColab server.

    This fixture should not be used in tests. Instead use :func:`mscolab_server`, which
    handles per-test cleanup as well.
    """
    # Use port 0 to let OS assign available port - early failure if unavailable
    cmd = [sys.executable, '-m', 'mslib.mscolab.mscolab', 'start', '--host', '127.0.0.1', '--port', '0']
    with _running_server(mscolab_session_app, cmd,
                         extra_paths=[str(mscolab_server_config_dir)],
                         extra_env={"MSCOLAB_TEST_MODE": "1"}) as url:
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
    with mscolab_session_app.app_context():
        handle_db_reset(verbose=False)
    # In-process socket bookkeeping survives handle_db_reset; clear it so state
    # does not leak across tests that share the imported server module.
    sockio.sm.clear_state()


@pytest.fixture
def mscolab_app(mscolab_session_app, reset_mscolab):
    """Fixture that provides the MSColab WSGI app instance and does cleanup actions.

    :returns: A WSGI app instance.
    """
    return mscolab_session_app


@pytest.fixture
def mscolab_managers(mscolab_session_managers, reset_mscolab):
    """Fixture that provides the MSColab managers and does cleanup actions.

    :returns: A tuple (SocketIO, ChatManager, FileManager).
    """
    return mscolab_session_managers


@pytest.fixture
def mscolab_server(mscolab_session_server, reset_mscolab):
    """Fixture that provides a running MSColab server and does cleanup actions.

    :returns: The URL where the server is running.
    """
    # Reset the subprocess server's own database and socket bookkeeping so its
    # SQLAlchemy connection pool sees the freshly migrated schema.  Falling back
    # to the socket-only reset keeps things working if the endpoint is absent.
    try:
        r = requests.post(urllib.parse.urljoin(mscolab_session_server, "/test/reset_db"), timeout=10)
        if r.status_code != 200:
            requests.post(urllib.parse.urljoin(mscolab_session_server, "/test/reset_socket_state"), timeout=5)
    except requests.RequestException:
        pass
    # Update mscolab URL to avoid "Update Server List" message boxes
    modify_config_file({"default_MSCOLAB": [mscolab_session_server]})
    return mscolab_session_server


@pytest.fixture(scope="session")
def mswms_app():
    """Fixture that provides the MSWMS WSGI app instance."""
    yield mslib.mswms.mswms.application
    # Close all open NetCDF4 datasets to release file handles on Windows
    from mslib.mswms import wms
    for drivers in (wms.server.hsec_drivers, wms.server.vsec_drivers, wms.server.lsec_drivers):
        for driver in drivers.values():
            if driver.dataset is not None:
                driver.dataset.close()
                driver.dataset = None


@pytest.fixture(scope="session")
def mswms_server(mswms_app, mswms_server_config_dir):
    """Fixture that provides a running MSWMS server.

    :returns: The URL where the server is running.
    """
    # Use port 0 to let OS assign available port - early failure if unavailable
    cmd = [sys.executable, '-m', 'mslib.mswms.mswms', '--host', '127.0.0.1', '--port', '0']
    with _running_server(mswms_app, cmd,
                         extra_paths=[str(mswms_server_config_dir)]) as url:
        yield url


def is_port_responsive(host, port, timeout=0.5):
    """Check if a port is responsive (accepting connections) with early timeout.

    :returns: True if the port responds within the timeout, False otherwise.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, socket.error, OSError):
        return False


@contextmanager
def _running_server(app, cmd, extra_paths=None, extra_env=None):
    """Context manager that starts the app in a subprocess and returns its URL.

    The subprocess must print the bound port as the first line on stdout.
    """
    scheme = "http"
    host = "127.0.0.1"
    env = os.environ.copy()
    if extra_paths:
        existing = env.get('PYTHONPATH', '')
        env['PYTHONPATH'] = os.pathsep.join(extra_paths) + (os.pathsep + existing if existing else '')
    if extra_env:
        env.update(extra_env)
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    try:
        # Retrieve the port printed by the runner to stdout
        port_line = process.stdout.readline()
        if not port_line:
            stderr_output = process.stderr.read().decode(errors='replace')
            raise RuntimeError(
                f"Could not retrieve port from server process. stderr:\n{stderr_output}"
            )
        port = int(port_line.strip())

        url = f"{scheme}://{host}:{port}"
        app.config['URL'] = url

        # Early port check with short timeout to fail fast if port doesn't respond
        if not is_port_responsive(host, port, timeout=1.0):
            stderr_output = process.stderr.read().decode(errors='replace')
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            pytest.skip(f"Skipping test: server port {host}:{port} not responsive. stderr: {stderr_output}")

        start_time = time.time()
        sleep_time = 0.01
        time_out = 20
        # we check only for the root url, index.html may take longer
        readiness_url = urllib.parse.urljoin(url, "/")
        while not is_url_response_ok(readiness_url):
            if process.poll() is not None:
                # show the exitcode for further debugging
                raise RuntimeError(f"Server process exited early with code {process.returncode} at {url}")
            if (time.time() - start_time) > time_out:
                raise RuntimeError(f"Server did not start within {time_out} seconds at {url}")
            time.sleep(sleep_time)
            sleep_time = min(sleep_time * 2, 1)
        yield url
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


@pytest.fixture
def reset_wms_globals():
    """Fixture to reset WMS module-level globals that can affect test isolation."""
    static_location = mslib.mswms.wms.STATIC_LOCATION
    docs_location = mslib.mswms.wms.DOCS_LOCATION
    gallery_static = mslib.mswms.gallery_builder.STATIC_LOCATION
    gallery_docs = mslib.mswms.gallery_builder.DOCS_LOCATION
    yield
    mslib.mswms.wms.STATIC_LOCATION = static_location
    mslib.mswms.wms.DOCS_LOCATION = docs_location
    mslib.mswms.gallery_builder.STATIC_LOCATION = gallery_static
    mslib.mswms.gallery_builder.DOCS_LOCATION = gallery_docs


@pytest.fixture
def reset_gallery_builders():
    """Fixture to reset gallery_builder module-level mutable state."""
    plots_copy = {k: v.copy() for k, v in mslib.mswms.gallery_builder.plots.items()}
    plot_htmls_copy = mslib.mswms.gallery_builder.plot_htmls.copy()
    begin_copy = mslib.mswms.gallery_builder.begin
    end_copy = mslib.mswms.gallery_builder.end
    yield
    mslib.mswms.gallery_builder.plots.clear()
    mslib.mswms.gallery_builder.plots.update(plots_copy)
    mslib.mswms.gallery_builder.plot_htmls.clear()
    mslib.mswms.gallery_builder.plot_htmls.update(plot_htmls_copy)
    mslib.mswms.gallery_builder.begin = begin_copy
    mslib.mswms.gallery_builder.end = end_copy


@pytest.fixture
def reset_user_options():
    """Fixture to reset user_options global variable."""
    from mslib.utils.config import user_options
    import mslib.utils.config as config_module

    original_options = config_module.copy.deepcopy(user_options)

    try:
        yield
    finally:
        config_module.user_options = config_module.copy.deepcopy(original_options)
