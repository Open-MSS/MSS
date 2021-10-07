# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_server
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for server functionalities

    This file is part of mss.

    :copyright: Copyright 2020 Reimar Bauer
    :copyright: Copyright 2020-2021 by the mss team, see AUTHORS.
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

from flask_testing import TestCase
import os
import pytest
import json
import io

from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import db, User, Operation
from mslib.mscolab.mscolab import handle_db_reset
from mslib.mscolab.server import initialize_managers, check_login, register_user, APP
from mslib.mscolab.file_manager import FileManager
from mslib.mscolab.seed import add_user, get_user


@pytest.mark.skipif(os.name == "nt",
                    reason="multiprocessing needs currently start_method fork")
class Test_Server(TestCase):
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
        handle_db_reset()
        db.init_app(self.app)
        self.userdata = 'UV10@uv10', 'UV10', 'uv10'

    def tearDown(self):
        pass

    def test_initialize_managers(self):
        app, sockio, cm, fm = initialize_managers(self.app)
        assert app.config['MSCOLAB_DATA_DIR'] == mscolab_settings.MSCOLAB_DATA_DIR
        assert 'Create a Flask-SocketIO server.' in sockio.__doc__
        assert 'Class with handler functions for chat related functionalities' in cm.__doc__
        assert 'Class with handler functions for file related functionalities' in fm.__doc__

    def test_home(self):
        # we switched templates off
        with self.app.test_client() as test_client:
            response = test_client.get('/')
            assert response.status_code == 200
            assert b"" in response.data

    def test_hello(self):
        with self.app.test_client() as test_client:
            response = test_client.get('/status')
            assert response.status_code == 200
            assert b"Mscolab server" in response.data

    def test_register_user(self):
        with self.app.test_client():
            result = register_user(self.userdata[0], self.userdata[1], self.userdata[2])
            assert result["success"] is True
            result = register_user(self.userdata[0], self.userdata[1], self.userdata[2])
            assert result["success"] is False
            assert result["message"] == "Oh no, this email ID is already taken!"
            result = register_user("UV", self.userdata[1], self.userdata[2])
            assert result["success"] is False
            assert result["message"] == "Oh no, your email ID is not valid!"
            result = register_user(self.userdata[0], self.userdata[1], self.userdata[0])
            assert result["success"] is False
            assert result["message"] == "Oh no, your username cannot contain @ symbol!"

    def test_check_login(self):
        with self.app.test_client():
            result = register_user(self.userdata[0], self.userdata[1], self.userdata[2])
            assert result["success"] is True
            result = check_login(self.userdata[0], self.userdata[1])
            user = User.query.filter_by(emailid=str(self.userdata[0])).first()
            assert user is not None
            assert result == user
            result = check_login('UV20@uv20', self.userdata[1])
            assert result is False

    def test_get_auth_token(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        with self.app.test_client() as test_client:
            token = self._get_token(test_client, self.userdata)
            assert User.verify_auth_token(token)
            response = test_client.post('/token', data={"email": self.userdata[0], "password": "fail"})
            assert response.status_code == 200
            assert response.data.decode('utf-8') == "False"

    def test_authorized(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        with self.app.test_client() as test_client:
            token = self._get_token(test_client, self.userdata)
            response = test_client.get('/test_authorized', data={"token": token})
            assert response.status_code == 200
            assert response.data.decode('utf-8') == "True"
            response = test_client.get('/test_authorized', data={"token": "effsdfs"})
            assert response.data.decode('utf-8') == "False"

    def test_user_register_handler(self):
        with self.app.test_client() as test_client:
            response = test_client.post('/register', data={"email": self.userdata[0],
                                                           "password": self.userdata[2],
                                                           "username": self.userdata[1]})
            assert response.status_code == 201
            response = test_client.post('/register', data={"email": self.userdata[0],
                                                           "pass": "dsss",
                                                           "username": self.userdata[1]})
            assert response.status_code == 400

    def test_get_user(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        with self.app.test_client() as test_client:
            token = self._get_token(test_client, self.userdata)
            response = test_client.get('/user', data={"token": token})
            data = json.loads(response.data.decode('utf-8'))
            assert data["user"]["username"] == self.userdata[1]

    def test_delete_user(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        with self.app.test_client() as test_client:
            token = self._get_token(test_client, self.userdata)
            response = test_client.post('/delete_user', data={"token": token})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            assert data["success"] is True
            response = test_client.post('/delete_user', data={"token": "dsdsds"})
            assert response.status_code == 200
            assert response.data.decode('utf-8') == "False"

    def test_messages(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            response = test_client.get('/messages', data={"token": token,
                                                          "op_id": operation.id})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            assert data["messages"] == []

    def test_message_attachment(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            attachment = io.BytesIO(b"this is a test")
            response = test_client.post('/message_attachment', data={"token": token,
                                                                     "op_id": operation.id,
                                                                     "file": (attachment, 'test.txt'),
                                                                     "message_type": "3"})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            pfn = data["path"]
            assert "txt" in pfn
            assert "uploads" in pfn

    def test_uploads(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            text = b"this is a test"
            attachment = io.BytesIO(text)
            response = test_client.post('/message_attachment', data={"token": token,
                                                                     "op_id": operation.id,
                                                                     "file": (attachment, 'test.txt'),
                                                                     "message_type": "3"})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            pfn = data["path"]
            response = test_client.get(f'{pfn}')
            assert response.status_code == 200
            assert response.data == text

    def test_create_operation(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            assert operation is not None
            assert token is not None

    def test_get_operation_by_id(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            response = test_client.get('/get_operation_by_id', data={"token": token,
                                                                     "op_id": operation.id})
            assert response.status_code == 200
            assert "<ListOfWaypoints>" in response.data.decode('utf-8')

    def test_get_operations(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        with self.app.test_client() as test_client:
            self._create_operation(test_client, self.userdata, path="firstflightpath1")
            operation, token = self._create_operation(test_client, self.userdata, path="firstflightpath2")
            response = test_client.get('/operations', data={"token": token})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            assert len(data["operations"]) == 2
            assert data["operations"][0]["path"] == "firstflightpath1"
            assert data["operations"][1]["path"] == "firstflightpath2"

    def test_get_all_changes(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            fm, user = self._save_content(operation, self.userdata)
            fm.save_file(operation.id, "content2", user)
            response = test_client.get('/get_all_changes', data={"token": token,
                                                                 "op_id": operation.id})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            assert len(data["changes"]) == 2

    def test_get_change_content(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            fm, user = self._save_content(operation, self.userdata)
            fm.save_file(operation.id, "content2", user)
            all_changes = fm.get_all_changes(operation.id, user)
            response = test_client.get('/get_change_content', data={"token": token,
                                                                    "ch_id": all_changes[1]["id"]})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            assert data == {'content': 'content1'}

    def test_set_version_name(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            fm, user = self._save_content(operation, self.userdata)
            fm.save_file(operation.id, "content2", user)
            all_changes = fm.get_all_changes(operation.id, user)
            ch_id = all_changes[1]["id"]
            version_name = "THIS"
            response = test_client.post('/set_version_name', data={"token": token,
                                                                   "ch_id": ch_id,
                                                                   "op_id": operation.id,
                                                                   "version_name": version_name})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            assert data["success"] is True

    def test_authorized_users(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            response = test_client.get('/authorized_users', data={"token": token,
                                                                  "op_id": operation.id})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            assert data["users"] == [{'access_level': 'creator', 'username': self.userdata[1]}]

    def test_delete_operation(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            response = test_client.post('/delete_operation', data={"token": token,
                                                                   "op_id": operation.id})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            assert data["success"] is True

    def test_update_operation(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            response = test_client.post('/update_operation', data={"token": token,
                                                                   "op_id": operation.id,
                                                                   "attribute": "path",
                                                                   "value": "newflight"})
            assert response.status_code == 200
            data = response.data.decode('utf-8')
            assert data == "True"
            response = test_client.post('/update_operation', data={"token": token,
                                                                   "op_id": operation.id,
                                                                   "attribute": "description",
                                                                   "value": "sunday start"})
            assert response.status_code == 200
            data = response.data.decode('utf-8')
            assert data == "True"

    def test_get_operation_details(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        with self.app.test_client() as test_client:
            path = "flp1"
            operation, token = self._create_operation(test_client, self.userdata, path=path)
            response = test_client.get('/operation_details', data={"token": token,
                                                                   "op_id": operation.id})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            assert data["path"] == path

    def test_get_users_without_permission(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        unprevileged_user = 'UV20@uv20', 'UV20', 'uv20'
        assert add_user(unprevileged_user[0], unprevileged_user[1], unprevileged_user[2])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            response = test_client.get('/users_without_permission', data={"token": token,
                                                                          "op_id": operation.id})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            # ToDo after cleanup pf database use absolute values
            assert data["users"][-1][0] == unprevileged_user[1]

    def test_get_users_with_permission(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        another_user = 'UV20@uv20', 'UV20', 'uv20'
        assert add_user(another_user[0], another_user[1], another_user[2])
        with self.app.test_client() as test_client:
            operation, token = self._create_operation(test_client, self.userdata)
            response = test_client.get('/users_with_permission', data={"token": token,
                                                                       "op_id": operation.id})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            # creator is not listed
            assert data["users"] == []

    def test_import_permissions(self):
        assert add_user(self.userdata[0], self.userdata[1], self.userdata[2])
        another_user = 'UV20@uv20', 'UV20', 'uv20'
        assert add_user(another_user[0], another_user[1], another_user[2])
        with self.app.test_client() as test_client:
            import_operation, token = self._create_operation(test_client, self.userdata, path="import")
            user = get_user(self.userdata[0])
            another = get_user(another_user[0])
            fm = FileManager(self.app.config["MSCOLAB_DATA_DIR"])
            fm.add_bulk_permission(import_operation.id, user, [another.id], "viewer")
            current_operation, token = self._create_operation(test_client, self.userdata, path="current")
            response = test_client.post('/import_permissions', data={"token": token,
                                                                     "import_op_id": import_operation.id,
                                                                     "current_op_id": current_operation.id})
            assert response.status_code == 200
            data = json.loads(response.data.decode('utf-8'))
            # creator is not listed
            assert data["success"] is True

    def _create_operation(self, test_client, userdata=None, path="firstflight", description="simple test"):
        if userdata is None:
            userdata = self.userdata
        response = test_client.post('/token', data={"email": userdata[0], "password": userdata[2]})
        data = json.loads(response.data.decode('utf-8'))
        token = data["token"]
        response = test_client.post('/create_operation', data={"token": token,
                                                               "path": path,
                                                               "description": description})
        assert response.status_code == 200
        assert response.data.decode('utf-8') == "True"
        operation = Operation.query.filter_by(path=path).first()
        return operation, token

    def _get_token(self, test_client, userdata=None):
        if userdata is None:
            userdata = self.userdata
        response = test_client.post('/token', data={"email": userdata[0], "password": userdata[2]})
        assert response.status_code == 200
        data = json.loads(response.data.decode('utf-8'))
        assert data["user"]["username"] == userdata[1]
        token = data["token"]
        return token

    def _save_content(self, operation, userdata=None):
        if userdata is None:
            userdata = self.userdata
        user = get_user(userdata[0])
        fm = FileManager(self.app.config["MSCOLAB_DATA_DIR"])
        fm.save_file(operation.id, "content1", user)
        return fm, user
