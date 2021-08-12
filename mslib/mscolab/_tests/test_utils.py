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
from flask_testing import TestCase
import os
import pytest
import json

from fs.tempfs import TempFS
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import db, Project, MessageType
from mslib.mscolab.mscolab import handle_db_seed
from mslib.mscolab.server import APP
from mslib.mscolab.seed import add_user, get_user
from mslib.mscolab.utils import get_recent_pid, get_session_id, get_message_dict, create_files, os_fs_create_dir
from mslib.mscolab.sockets_manager import setup_managers


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
class Test_Utils(TestCase):
    render_templates = False

    def create_app(self):
        app = APP
        app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
        app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
        app.config['UPLOAD_FOLDER'] = mscolab_settings.UPLOAD_FOLDER
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config["TESTING"] = True
        app.config['LIVESERVER_TIMEOUT'] = 10
        app.config['LIVESERVER_PORT'] = 0
        return app

    def setUp(self):
        handle_db_seed()
        self.userdata = 'UV10@uv10', 'UV10', 'uv10'
        self.anotheruserdata = 'UV20@uv20', 'UV20', 'uv20'
        socketio, cm, self.fm = setup_managers(self.app)

    def tearDown(self):
        pass
        # review later when handle_db does not seed for tests
        # db.session.remove()
        # db.drop_all()

    def test_get_recent_pid(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        assert add_user(self.anotheruserdata[0], self.anotheruserdata[1], self.anotheruserdata[2])
        with self.app.test_client() as test_client:
            db.init_app(self.app)
            user = get_user(self.userdata[0])
            anotheruser = get_user(self.anotheruserdata[0])
            project, token = self._create_project(test_client, self.userdata)
            p_id = get_recent_pid(self.fm, user)
            assert p_id == project.id
            p_id = get_recent_pid(self.fm, anotheruser)
            assert p_id is None

    def test_get_session_id(self):
        sockets = [{"u_id": 5, "s_id": 100}]
        assert get_session_id(sockets, 5) == 100

    def test_get_message_dict(self):
        result = get_message_dict(Message())
        assert result["message_type"] == MessageType.TEXT

    def test_os_fs_create_dir(self):
        _fs = TempFS(identifier="mss")
        _dir = _fs.getsyspath("")
        os_fs_create_dir(_dir)
        assert os.path.exists(_dir)

    def test_create_file(self):
        create_files()
        # ToDo refactor to fs
        assert os.path.exists(mscolab_settings.MSCOLAB_DATA_DIR)
        assert os.path.exists(mscolab_settings.UPLOAD_FOLDER)

    def _create_project(self, test_client, userdata=None, path="firstflight", description="simple test"):
        if userdata is None:
            userdata = self.userdata
        response = test_client.post('/token', data={"email": userdata[0], "password": userdata[2]})
        data = json.loads(response.data.decode('utf-8'))
        token = data["token"]
        response = test_client.post('/create_project', data={"token": token,
                                                             "path": path,
                                                             "description": description})
        assert response.status_code == 200
        assert response.data.decode('utf-8') == "True"
        project = Project.query.filter_by(path=path).first()
        return project, token
