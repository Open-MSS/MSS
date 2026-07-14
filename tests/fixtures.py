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
import multiprocessing
import time
import urllib
import socketio
import mslib.mswms.mswms
from werkzeug.serving import make_server

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


# TODO: Having this fixture be autouse is a crutch. It seems like if it is not autouse some tests can bring the pytest
# processes objects into a state in which the MSColab server will have trouble starting the Flask-SocketIO server once
# it is forked. With autouse the fork happens first, before any test runs. After that, the pytest process can no longer
# affect the now-running server, thus mitigating the issue. This is my understanding at time of writing.
#
# This issue would also be avoided if the background server process wasn't started with multiprocessing and a fork, but
# with a real subprocess, which would solve some other issues (e.g. testing on Windows) as well.
@pytest.fixture(scope="session", autouse=True)
def mscolab_session_server(mscolab_session_app, mscolab_session_managers):
    """Session-scoped fixture that provides a running MSColab server.

    This fixture should not be used in tests. Instead use :func:`mscolab_server`, which
    handles per-test cleanup as well.
    """
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
    with mscolab_session_app.app_context():
        handle_db_reset(verbose=False)


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
    # Update mscolab URL to avoid "Update Server List" message boxes
    modify_config_file({"default_MSCOLAB": [mscolab_session_server]})
    return mscolab_session_server


@pytest.fixture(scope="session")
def mswms_app():
    """Fixture that provides the MSWMS WSGI app instance."""
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
    srv = make_server(host, 0, app, threaded=True)
    port = srv.server_address[1]
    port_queue.put(port)
    srv.serve_forever()


@contextmanager
def _running_server(app):
    """Context manager that starts the app in a werkzeug server and returns its URL."""
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
