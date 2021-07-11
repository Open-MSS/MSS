# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_seed
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for conf functionalities

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2021 by the mss team, see AUTHORS.
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

import sys
from PyQt5 import QtTest, QtWidgets
from mslib.mscolab.models import User
from mslib.mscolab.conf import mscolab_settings
from mslib._tests.utils import (mscolab_register_and_login,
                                mscolab_create_project, mscolab_delete_all_projects,
                                mscolab_delete_user, mscolab_start_server)
from mslib.mscolab.seed import add_all_users_default_project, add_user, delete_user
import mslib.msui.mss_pyui as mss_pyui


PORTS = list(range(19571, 19590))


class Test_Seed():
    def setup(self):
        mscolab_settings.enable_basic_http_authentication = False
        self.process, self.url, self.app, _, self.cm, self.fm = mscolab_start_server(PORTS, mscolab_settings)
        QtTest.QTest.qWait(100)
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = mss_pyui.MSSMainWindow(mscolab_data_dir=mscolab_settings.MSCOLAB_DATA_DIR)
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, self.url, 'UV0@uv0', 'UV0', 'uv0')
            assert response.status == '200 OK'
            data, response = mscolab_create_project(self.app, self.url, response,
                                                    path='XYZ', description='Template')
            assert response.status == '200 OK'
            data = response.get_data(as_text=True)
            assert data == 'True'
            mscolab_register_and_login(self.app, self.url, 'UV1@uv1', 'UV1', 'UV1')

    def teardown(self):
        with self.app.app_context():
            mscolab_delete_user(self.app, self.url, 'UV0@uv0', 'UV0')
            mscolab_delete_user(self.app, self.url, 'UV1@uv1', 'UV1')
            mscolab_delete_all_projects(self.app, self.url, 'UV0@uv0', 'uv0', 'UV0')
            mscolab_delete_all_projects(self.app, self.url, 'UV1@uv1', 'uv1', 'UV1')
            user = User.query.filter_by(emailid="UV2@v2").first()
            if user is not None:
                delete_user('UV2@uv2')
        if self.window.mscolab.version_window:
            self.window.mscolab.version_window.close()
        if self.window.mscolab.conn:
            self.window.mscolab.conn.disconnect()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        self.process.terminate()

    def test_add_all_users_default_project_viewer(self):
        with self.app.app_context():
            # viewer
            add_all_users_default_project(path='XYZ', description="Project to keep all users", access_level='viewer')
            expected_result = [{'access_level': 'viewer', 'description': 'Template', 'p_id': 7, 'path': 'XYZ'}]
            user = User.query.filter_by(emailid="UV1@uv1").first()
            assert user is not None
            result = self.fm.list_projects(user)
            # we don't care here for p_id
            expected_result[0]['p_id'] = result[0]['p_id']
            assert result == expected_result

    def test_add_all_users_default_project_collaborator(self):
        with self.app.app_context():
            # collaborator
            add_all_users_default_project(path='XYZ', description="Project to keep all users",
                                          access_level='collaborator')
            expected_result = [{'access_level': 'collaborator', 'description': 'Template', 'p_id': 7, 'path': 'XYZ'}]
            user = User.query.filter_by(emailid="UV1@uv1").first()
            assert user is not None
            result = self.fm.list_projects(user)
            # we don't care here for p_id
            expected_result[0]['p_id'] = result[0]['p_id']
            assert result == expected_result

    def test_add_all_users_default_project_creator(self):
        with self.app.app_context():
            # creator
            add_all_users_default_project(path='XYZ', description="Project to keep all users",
                                          access_level='creator')
            expected_result = [{'access_level': 'creator', 'description': 'Template', 'p_id': 7, 'path': 'XYZ'}]
            user = User.query.filter_by(emailid="UV1@uv1").first()
            result = self.fm.list_projects(user)
            # we don't care here for p_id
            expected_result[0]['p_id'] = result[0]['p_id']
            assert result == expected_result

    def test_add_all_users_default_project_creator_unknown_project(self):
        with self.app.app_context():
            # creator added to new project
            add_all_users_default_project(path='UVXYZ', description="Project to keep all users",
                                          access_level='creator')
            expected_result = [{'access_level': 'creator', 'description': 'Project to keep all users',
                                'p_id': 7, 'path': 'UVXYZ'}]
            user = User.query.filter_by(emailid="UV1@uv1").first()
            result = self.fm.list_projects(user)
            # we don't care here for p_id
            expected_result[0]['p_id'] = result[0]['p_id']
            assert result == expected_result

    def test_add_user(self, capsys):
        self.app.app_context().push()
        add_user("UV2@v2", "V2", "v2")
        captured = capsys.readouterr()
        assert "Userdata: UV2@v2 V2 v2" in captured.out
        add_user("UV2@v2", "V2", "v2")
        captured = capsys.readouterr()
        assert '<User V2> already in db\n' == captured.out

    def test_delete_user(self, capsys):
        self.app.app_context().push()
        add_user("UV2@v2", "V2", "v2")
        captured = capsys.readouterr()
        assert "Userdata: UV2@v2 V2 v2" in captured.out
        user = User.query.filter_by(emailid="UV2@v2").first()
        assert user is not None
        delete_user("UV2@v2")
        captured = capsys.readouterr()
        assert 'User: UV2@v2 deleted from db\n' == captured.out
        user = User.query.filter_by(emailid="UV2@v2").first()
        assert user is None
