"""

    mslib.tutorials.utils.restart_mscolab
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module has functions related to restarting the mscolab server.

    This file is part of MSS.

    :copyright: Copyright 2024 by Reimar Bauer
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
import socketio
import time
from pathlib import Path

try:
    import mscolab_settings
except ImportError:
    msc_settings = None


sio = socketio.Client()


@sio.event
def connect():
    print('connection established')
    return True


@sio.event
def disconnect():
    print('disconnected from server')
    return False


def restart_mscolab():
    if msc_settings is not None:
        msc_settings_file = mscolab_settings.__file__
        Path(msc_settings_file).touch()
    else:
        print("mscolab settings file not found, can't restart, have you set the PYTHONPATH environment variable?")


def verify_mscolab_server_alive(url="http://localhost", port="8083"):
    try:
        sio.connect(f'{url}:{port}')
        return True
    except socketio.exceptions.ConnectionError:
        return False


def wait_until_mscolab_server_alive(max_wait=10, interval=0.5):
    start_time = time.time()

    while True:
        # Check server status
        if verify_mscolab_server_alive():
            print("MSColab server is alive!")
            break

        # Check if the max wait time has passed
        if time.time() - start_time > max_wait:
            print(f"Waited for {max_wait} seconds, but MSColab server is still not alive.")
            break

        # Wait for short interval before checking server status again
        time.sleep(interval)
