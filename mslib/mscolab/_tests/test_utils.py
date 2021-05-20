# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_utils
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for mscolab/utils

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2021 by the mss team, see AUTHORS.

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
import os
import sys
import pytest
from PyQt5 import QtWidgets, QtTest

from mslib.mscolab.models import User, MessageType
from mslib.mscolab.utils import get_recent_pid, get_session_id, get_message_dict, create_files
from mslib.mscolab.conf import mscolab_settings
from mslib.msui.mscolab import MSSMscolabWindow
from mslib._tests.utils import (mscolab_start_server, mscolab_create_project, mscolab_register_and_login,
                                mscolab_delete_user, mscolab_delete_all_projects)
from mslib.mscolab.server import register_user

PORTS = list(range(9561, 9580))


class Message():
    id = 1
    u_id = 2

    class user():
        username = "name"
    text = "Moin"
    message_type = MessageType.TEXT
    reply_id = 0
    replies = []

    class created_at():
        def strftime(value):
            pass


@pytest.mark.skipif(os.name == "nt",
                    reason="multiprocessing needs currently start_method fork")
class Test_Utils_with_Projects(object):
    def setup(self):
        self.process, self.url, self.app, self.sio, self.cm, self.fm = mscolab_start_server(PORTS)
        QtTest.QTest.qWait(500)
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = MSSMscolabWindow(data_dir=mscolab_settings.MSCOLAB_DATA_DIR,
                                       mscolab_server_url=self.url)

        with self.app.app_context():
            response = mscolab_register_and_login(self.app, self.url, 'a1a@a1a', 'a1a', 'a1a')
            _ = mscolab_create_project(self.app, self.url, response, path='f3', description='f3 test example')
            self.user = User.query.filter_by(emailid="a1a@a1a").first()
            self.test_p_id = get_recent_pid(self.fm, self.user)
            self.test_sid = 25
            socket_storage = {
                's_id': self.test_sid,
                'u_id': self.user.id
            }
            self.sockets = [socket_storage]

    def teardown(self):
        with self.app.app_context():
            mscolab_delete_all_projects(self.app, self.url, 'a1a@a1a', 'a1a', 'a1a')
            mscolab_delete_user(self.app, self.url, 'a1a@a1a', 'a1a')
        if self.window.version_window:
            self.window.version_window.close()
        if self.window.conn:
            self.window.conn.disconnect()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        self.process.terminate()

    def test_get_recent_pid(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.fm, self.user)
            assert p_id == self.test_p_id

    def test_get_session_id(self):
        with self.app.app_context():
            s_id = get_session_id(self.sockets, self.user.id)
            assert s_id == self.test_sid

    def test_get_message_dict(self):
        result = get_message_dict(Message())
        assert result["message_type"] == MessageType.TEXT

    def test_create_file(self):
        create_files()
        # ToDo refactor to fs
        assert os.path.exists(mscolab_settings.MSCOLAB_DATA_DIR)
        assert os.path.exists(mscolab_settings.UPLOAD_FOLDER)


class Test_Utils_No_Project(object):
    def setup(self):
        self.process, self.url, self.app, _, self.cm, self.fm = mscolab_start_server(PORTS)
        QtTest.QTest.qWait(100)
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = MSSMscolabWindow(data_dir=mscolab_settings.MSCOLAB_DATA_DIR,
                                       mscolab_server_url=self.url)
        with self.app.app_context():
            register_user('sdf@s.com', 'sdf', 'sdf')
            self.user = User.query.filter_by(emailid="sdf@s.com").first()

    def teardown(self):
        with self.app.app_context():
            mscolab_delete_user(self.app, self.url, 'sdf@s.com', 'sdf')
        if self.window.version_window:
            self.window.version_window.close()
        if self.window.conn:
            self.window.conn.disconnect()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        self.process.terminate()

    def test_get_recent_pid(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.fm, self.user)
            assert p_id is None
