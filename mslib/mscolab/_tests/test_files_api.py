# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_files_api
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    api integration tests for file based handlers

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2020 by the mss team, see AUTHORS.
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
import os
import pytest
import requests
import json
import sys
import time

from PyQt5 import QtWidgets
from werkzeug.urls import url_join
from mslib.mscolab.models import User, Change, Project
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.server import db
from mslib.mscolab.utils import get_recent_pid
from mslib._tests.utils import mscolab_register_and_login, mscolab_create_project, mscolab_start_server
from mslib.msui.mscolab import MSSMscolabWindow


PORTS = list(range(9381, 9400))


@pytest.mark.skipif(os.name == "nt",
                    reason="multiprocessing needs currently start_method fork")
class Test_Files(object):
    def setup(self):
        self.process, self.url, self.app, _, self.cm, self.fm = mscolab_start_server(PORTS)
        time.sleep(0.1)
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = MSSMscolabWindow(data_dir=mscolab_settings.MSCOLAB_DATA_DIR,
                                       mscolab_server_url=self.url)
        self.sockets = []
        self.file_message_counter = [0] * 2
        self.undefined_p_id = 123
        self.no_perm_p_id = 2
        data = {
            'email': 'a',
            'password': 'a'
        }
        r = requests.post(self.url + '/token', data=data)
        self.token = json.loads(r.text)['token']
        with self.app.app_context():
            self.user = User.query.filter_by(id=8).first()

    def teardown(self):
        for socket in self.sockets:
            socket.disconnect()
        if self.window.version_window:
            self.window.version_window.close()
        if self.window.conn:
            self.window.conn.disconnect()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        self.process.terminate()

    def test_create_project(self):
        data = {
            "token": self.token,
            "path": "dummy",
            "description": "test description"
        }
        url = url_join(self.url, 'create_project')
        r = requests.post(url, data=data)
        assert r.text == "True"
        r = requests.post(url, data=data)
        assert r.text == "False"

    def test_projects(self):
        data = {
            "token": self.token
        }
        url = url_join(self.url, 'projects')
        r = requests.get(url, data=data)
        json_res = json.loads(r.text)
        assert len(json_res["projects"]) == 3
        data["token"] = "garbage text"
        r = requests.get(url, data=data)
        assert r.text == "False"

    def test_get_project(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.fm, self.user)
            data = {
                "token": self.token,
                "p_id": p_id
            }
            url = url_join(self.url, 'get_project')
            r = requests.get(url, data=data)
            assert json.loads(r.text)["content"] == self.fm.get_file(int(p_id), self.user)

    def test_authorized_users(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.fm, self.user)
        data = {
            "token": self.token,
            "p_id": p_id
        }
        url = url_join(self.url, 'authorized_users')
        r = requests.get(url, data=data)
        users = json.loads(r.text)["users"]
        assert len(users) == 2
        # for any other random process which doesn't exist it will return empty array
        data["p_id"] = 43
        r = requests.get(url, data=data)
        users = json.loads(r.text)["users"]
        assert len(users) == 0

    def test_get_users_without_permission(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.fm, self.user)
        data = {
            "token": self.token,
            "p_id": p_id
        }
        url = url_join(self.url, "users_without_permission")
        res = requests.get(url, data=data).json()
        assert res["success"] is True
        data["p_id"] = self.undefined_p_id
        res = requests.get(url, data=data).json()
        assert res["success"] is False
        data["p_id"] = self.no_perm_p_id
        res = requests.get(url, data=data).json()
        assert res["success"] is False

    def test_get_users_with_permission(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.fm, self.user)
        data = {
            "token": self.token,
            "p_id": p_id
        }
        url = url_join(self.url, "users_with_permission")
        res = requests.get(url, data=data).json()
        assert res["success"] is True
        data["p_id"] = self.undefined_p_id
        res = requests.get(url, data=data).json()
        assert res["success"] is False
        data["p_id"] = self.no_perm_p_id
        res = requests.get(url, data=data).json()
        assert res["success"] is False

    def test_add_bulk_permissions(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.fm, self.user)
        data = {
            "token": self.token,
            "p_id": p_id,
            "selected_userids": json.dumps([12, 13]),
            "selected_access_level": "collaborator"
        }
        url = url_join(self.url, 'add_bulk_permissions')
        res = requests.post(url, data=data).json()
        assert res["success"] is True
        data["p_id"] = self.undefined_p_id
        res = requests.post(url, data=data).json()
        assert res["success"] is False
        data["p_id"] = self.no_perm_p_id
        res = requests.post(url, data=data).json()
        assert res["success"] is False

    def test_modify_bulk_permissions(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.fm, self.user)
            assert p_id == 4
        data = {
            "token": self.token,
            "p_id": p_id,
            "selected_userids": json.dumps([12, 13]),
            "selected_access_level": "viewer"
        }
        url = url_join(self.url, 'modify_bulk_permissions')
        r = requests.post(url, data=data).json()
        assert r["success"] is True
        data["p_id"] = self.undefined_p_id
        r = requests.post(url, data=data).json()
        assert r["success"] is False
        data["p_id"] = self.no_perm_p_id
        r = requests.post(url, data=data).json()
        assert r["success"] is False

    def test_delete_bulk_permissions(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.fm, self.user)
        data = {
            "token": self.token,
            "p_id": p_id,
            "selected_userids": json.dumps([12, 13]),
        }
        url = url_join(self.url, 'delete_bulk_permissions')
        r = requests.post(url, data=data).json()
        assert r["success"] is True
        data["p_id"] = self.undefined_p_id
        r = requests.post(url, data=data).json()
        assert r["success"] is False
        data["p_id"] = self.no_perm_p_id
        r = requests.post(url, data=data).json()
        assert r["success"] is False

    def test_import_permissions(self):
        current_p_id = 4
        import_p_id = 1
        data = {
            "token": self.token,
            "current_p_id": current_p_id,
            "import_p_id": import_p_id
        }
        url = url_join(self.url, 'import_permissions')
        res = requests.post(url, data=data).json()
        assert res["success"] is True
        data["import_p_id"] = self.no_perm_p_id
        res = requests.post(url, data=data).json()
        assert res["success"] is False
        data["current_p_id"] = self.no_perm_p_id
        res = requests.post(url, data=data).json()
        assert res["success"] is False

    def test_update_project(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.fm, self.user)
        # ToDo handle paths with blank characters here
        data = {
            "token": self.token,
            "p_id": p_id,
            "attribute": "path",
            "value": "a_diff_path"
        }
        get_proj_url = url_join(self.url, 'get_project')
        update_proj_url = url_join(self.url, 'update_project')
        r = requests.post(update_proj_url, data=data)
        assert r.text == "True"
        # to make sure that path has changed, which is indirectly known by this request
        # getting results properly
        r = requests.get(get_proj_url, data=data)
        assert r.text != "False"
        data = {
            "token": self.token,
            "p_id": p_id,
            "attribute": "description",
            "value": "a_diff description"
        }
        r = requests.post(update_proj_url, data=data)
        assert r.text == "True"
        with self.app.app_context():
            project = Project.query.filter_by(id=p_id).first()
            assert project.path == "a_diff_path"
            assert project.description == "a_diff description"

    def test_delete_project(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, self.url, 'a', 'a', 'a')
            assert response.status == '200 OK'
            data, response = mscolab_create_project(self.app, self.url, response,
                                                    path='f3', description='f3 test example')
            assert response.status == '200 OK'
            p_id = get_recent_pid(self.fm, self.user)

        # first free number after sseding
        assert p_id == 7
        data = {
            "token": self.token,
            "p_id": p_id
        }
        url = url_join(self.url, 'delete_project')
        res = requests.post(url, data=data).json()
        assert res["success"] is True

    def test_change(self):
        """
        since file needs to be saved to inflict changes, changes during integration
        tests have to be manually inserted
        """
        with self.app.app_context():
            p_id = get_recent_pid(self.fm, self.user)
            ch = Change(int(p_id), 8, "", "Version1", "some comment")

            db.session.add(ch)
            db.session.commit()
        data = {
            "token": self.token,
            "p_id": p_id
        }
        # test 'get all changes' request
        url = url_join(self.url, 'get_all_changes')
        r = requests.get(url, data=data)
        changes = json.loads(r.text)["changes"]
        assert len(changes) == 1
        assert changes[0]["comment"] == "some comment"

    def test_change_content(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.fm, self.user)
            ch = Change(int(p_id), 8, "", "Version changed", "some comment")
            db.session.add(ch)
            db.session.commit()
            data = {
                "token": self.token,
                "p_id": p_id
            }
            get_proj_url = url_join(self.url, 'get_project')
            res = requests.get(get_proj_url, data=data)
            content = json.loads(res.text)["content"]
            change = Change.query.order_by(Change.created_at.desc()).first()
            data = {
                "token": self.token,
                "ch_id": change.id
            }
            get_change_content_url = url_join(self.url, 'get_change_content')
            res = requests.get(get_change_content_url, data=data).json()
            change_content = res["content"]
            assert content.strip() == change_content.strip()

    def test_set_version_name(self):
        with self.app.app_context():
            p_id = int(get_recent_pid(self.fm, self.user))
            ch = Change(int(p_id), 8, "", "Version changed", "some comment")
            db.session.add(ch)
            db.session.commit()
            change = Change.query.filter_by(p_id=p_id).order_by(Change.created_at.desc()).first()
        data = {
            "token": self.token,
            "ch_id": change.id,
            "p_id": p_id,
            "version_name": "Test Version Name"
        }
        url = url_join(self.url, 'set_version_name')
        res = requests.post(url, data=data).json()
        assert res["success"] is True
        with self.app.app_context():
            change = Change.query.filter_by(id=change.id).first()
            assert change.version_name == "Test Version Name"
