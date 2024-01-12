# -*- coding: utf-8 -*-
"""

    tests.utils
    ~~~~~~~~~~~

    This module provides utils for pytest to test mslib modules

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2016-2023 by the MSS team, see AUTHORS.
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
import requests
import time
import fs
import socket
import multiprocessing

from flask_testing import LiveServerTestCase

from PyQt5 import QtTest
from urllib.parse import urljoin
from mslib.mscolab.server import register_user
from flask import json
from tests.constants import MSUI_CONFIG_PATH
from mslib.mscolab.server import initialize_managers, start_server


def callback_ok_image(status, response_headers):
    assert status == "200 OK"
    assert response_headers[0] == ('Content-type', 'image/png')


def callback_ok_xml(status, response_headers):
    assert status == "200 OK"
    assert response_headers[0] == ('Content-type', 'text/xml')


def callback_ok_html(status, response_headers):
    assert status == "200 OK"
    assert response_headers[0] == ('Content-Type', 'text/html; charset=utf-8')


def callback_404_plain(status, response_headers):
    assert status == "404 NOT FOUND"
    assert response_headers[0] == ('Content-type', 'text/plain')


def callback_307_html(status, response_headers):
    assert status == "307 TEMPORARY REDIRECT"
    assert response_headers[0] == ('Content-Type', 'text/html; charset=utf-8')


def mscolab_register_user(app, msc_url, email, password, username):
    # Duplicate of imported register_user
    data = {
        'email': email,
        'password': password,
        'username': username
    }
    url = urljoin(msc_url, 'register')
    response = app.test_client().post(url, data=data)
    return response


def mscolab_register_and_login(app, msc_url, email, password, username):
    register_user(email, password, username)
    data = {
        'email': email,
        'password': password
    }
    url = urljoin(msc_url, 'token')
    response = app.test_client().post(url, data=data)
    return response


def mscolab_login(app, msc_url, email='a', password='a'):
    data = {
        'email': email,
        'password': password
    }
    url = urljoin(msc_url, 'token')
    response = app.test_client().post(url, data=data)
    return response


def mscolab_delete_user(app, msc_url, email, password):
    with app.app_context():
        response = mscolab_login(app, msc_url, email, password)
        if response.status == '200 OK':
            data = json.loads(response.get_data(as_text=True))
            url = urljoin(msc_url, 'delete_own_account')
            response = app.test_client().post(url, data=data)
            if response.status == '200 OK':
                data = json.loads(response.get_data(as_text=True))
                return data["success"]
        return False


def mscolab_create_content(app, msc_url, data, path_name='example', content=None):
    if content is None:
        content = f"""\
        <?xml version="1.0" encoding="utf-8"?>
          <FlightTrack>
            <Name>{path_name}</Name>
            <ListOfWaypoints>
              <Waypoint flightlevel="0.0" lat="55.15" location="A1" lon="-23.74">
                <Comments>Takeoff</Comments>
              </Waypoint>
              <Waypoint flightlevel="350" lat="42.99" location="A2" lon="-12.1">
                <Comments></Comments>
              </Waypoint>
              </ListOfWaypoints>
          </FlightTrack>"""
    data["path"] = path_name
    data['description'] = path_name
    data['content'] = content
    url = urljoin(msc_url, 'create_operation')
    response = app.test_client().post(url, data=data)
    return response


def mscolab_delete_all_operations(app, msc_url, email, password, username):
    response = mscolab_register_and_login(app, msc_url, email, password, username)
    data = json.loads(response.get_data(as_text=True))
    url = urljoin(msc_url, 'operations')
    response = app.test_client().get(url, data=data)
    response = json.loads(response.get_data(as_text=True))
    for p in response['operations']:
        data['op_id'] = p['op_id']
        url = urljoin(msc_url, 'delete_operation')
        response = app.test_client().post(url, data=data)


def mscolab_create_operation(app, msc_url, response, path='f', description='description'):
    data = json.loads(response.get_data(as_text=True))
    data["path"] = path
    data['description'] = description
    url = urljoin(msc_url, 'create_operation')
    response = app.test_client().post(url, data=data)
    return data, response


def mscolab_get_operation_id(app, msc_url, email, password, username, path):
    response = mscolab_register_and_login(app, msc_url, email, password, username)
    data = json.loads(response.get_data(as_text=True))
    url = urljoin(msc_url, 'operations')
    response = app.test_client().get(url, data=data)
    response = json.loads(response.get_data(as_text=True))
    for p in response['operations']:
        if p['path'] == path:
            return p['op_id']


def mscolab_check_free_port(all_ports, port):
    _s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        _s.bind(("127.0.0.1", port))
    except (socket.error, IOError):
        port = all_ports.pop()
        port = mscolab_check_free_port(all_ports, port)
    else:
        _s.close()
    return port


def create_msui_settings_file(content):
    with fs.open_fs(MSUI_CONFIG_PATH) as file_dir:
        file_dir.writetext("msui_settings.json", content)


def is_url_response_ok(url):
    try:
        response = requests.get(url)
        return response.status_code == 200
    except:  # noqa: E722
        return False


def wait_until_signal(signal, timeout=5):
    """
    Blocks the calling thread until the signal emits or the timeout expires.
    """
    init_time = time.time()
    finished = False

    def done(*args):
        nonlocal finished
        finished = True

    signal.connect(done)
    while not finished and time.time() - init_time < timeout:
        QtTest.QTest.qWait(100)

    try:
        signal.disconnect(done)
    except TypeError:
        pass
    finally:
        return finished


class ExceptionMock:
    """
    Replace function calls with raised exceptions
    e.g.
    with mock.patch("requests.get", new=ExceptionMock(requests.exceptions.ConnectionError).raise_exc):
        self._login()
    """
    def __init__(self, exc):
        self.exc = exc

    def raise_exc(self, *args, **kwargs):
        raise self.exc


class LiveSocketTestCase(LiveServerTestCase):

    def _spawn_live_server(self):
        self._process = None
        port_value = self._port_value
        app, sockio, cm, fm = initialize_managers(self.app)
        self._process = multiprocessing.Process(
            target=start_server,
            args=(app, sockio, cm, fm,),
            kwargs={'port': port_value.value})

        self._process.start()

        # We must wait for the server to start listening, but give up
        # after a specified maximum timeout
        timeout = self.app.config.get('LIVESERVER_TIMEOUT', 5)
        start_time = time.time()

        while True:
            elapsed_time = (time.time() - start_time)
            if elapsed_time > timeout:
                raise RuntimeError(
                    "Failed to start the server after %d seconds. " % timeout
                )

            if self._can_ping_server():
                break
