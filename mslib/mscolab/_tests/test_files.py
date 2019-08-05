# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_files
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for file based handlers

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
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
import requests
import multiprocessing
import json
import os
from flask import Flask
from functools import partial
import time

from mslib.mscolab.conf import SQLALCHEMY_DB_URI, MSCOLAB_DATA_DIR
from mslib.mscolab.models import db, User, Project, Change, Permission, Message
from mslib.mscolab.sockets_manager import fm
from mslib._tests.constants import MSCOLAB_URL_TEST
from mslib.mscolab.server import app, sockio
from mslib.mscolab.utils import get_recent_pid


class Test_Files(object):
    def setup(self):
        self.sockets = []
        self.file_message_counter = [0] * 2
        self.p = multiprocessing.Process(
            target=sockio.run,
            args=(app,),
            kwargs={'port': 8083})
        self.p.start()
        time.sleep(1)
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DB_URI
        db.init_app(self.app)
        with self.app.app_context():
            self.user = User.query.filter_by(id=8).first()

    def test_create_project(self):
        with self.app.app_context():
            # test for blank character in path
            assert fm.create_project('test path', 'test desc.', self.user) is False
            # test for normal path
            assert fm.create_project('test_path', 'test desc.', self.user) is True
            # test for '/' in path
            assert fm.create_project('test/path', 'sth', self.user) is False
            # check file existence
            assert os.path.exists(os.path.join(MSCOLAB_DATA_DIR, 'test_path')) is True
            # check creation in db
            p = Project.query.filter_by(path="test_path").first()
            assert p is not None
            # check permission for author
            perms = Permission.query.filter_by(p_id=p.id, access_level="creator").all()
            assert len(perms) == 1
            assert perms[0].u_id == self.user.id

    def test_projects(self):
        with self.app.app_context():
            projects = fm.list_projects(self.user)
            assert len(projects) == 3

    def test_add_permission(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.user)
            assert fm.add_permission(p_id, 9, None, 'collaborator', self.user) is True
            user2 = User.query.filter_by(id=9).first()
            projects = fm.list_projects(user2)
            assert len(projects) == 3

    def test_modify_permission(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.user)
            # modifying permission to 'viewer'
            assert fm.update_access_level(p_id, 9, None, 'viewer', self.user) is True
            user2 = User.query.filter_by(id=9).first()
            projects = fm.list_projects(user2)
            assert projects[-1]["access_level"] == "viewer"

    def test_file_save(self):
        r = requests.post(MSCOLAB_URL_TEST + "/token", data={
                          'email': 'a',
                          'password': 'a'
                          })
        response1 = json.loads(r.text)
        r = requests.post(MSCOLAB_URL_TEST + "/token", data={
                          'email': 'b',
                          'password': 'b'
                          })
        response2 = json.loads(r.text)

        def handle_chat_message(sno, message):
            self.file_message_counter[sno - 1] += 1

        sio1 = socketio.Client()
        sio2 = socketio.Client()

        sio1.on('file-changed', handler=partial(handle_chat_message, 1))
        sio2.on('file-changed', handler=partial(handle_chat_message, 2))
        sio1.connect(MSCOLAB_URL_TEST)
        sio2.connect(MSCOLAB_URL_TEST)
        with self.app.app_context():
            p_id = get_recent_pid(self.user)
            user2 = User.query.filter_by(id=9).first()
            sio1.emit('start', response1)
            sio2.emit('start', response2)
            time.sleep(4)
            sio1.emit('file-save', {
                      "p_id": p_id,
                      "token": response1['token'],
                      "content": "test"
                      })
            time.sleep(4)
            # second file change
            sio1.emit('file-save', {
                      "p_id": p_id,
                      "token": response1['token'],
                      "content": "no ive changed the file now"
                      })
            time.sleep(4)
            # check if there were events triggered related to file-save
            assert self.file_message_counter[0] == 2
            assert self.file_message_counter[1] == 2
            # check if content is saved in file
            assert fm.get_file(p_id, user2) == "no ive changed the file now"
            # check if change is saved properly
            changes = fm.get_changes(p_id, self.user)
            assert len(changes) == 2
            change = Change.query.first()
            change_function_result = fm.get_change_by_id(change.id, self.user)
            assert change.content == change_function_result['content']
            # to disconnect sockets later
            self.sockets.append(sio1)
            self.sockets.append(sio2)

    def test_undo(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.user)
            changes = Change.query.filter_by(p_id=p_id).all()
            assert fm.undo(changes[0].id, self.user) is True
            assert len(fm.get_changes(p_id, self.user)) == 3
            assert fm.get_file(p_id, self.user) == "test"

    def test_revoke_permission(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.user)
            assert fm.update_access_level(p_id, 9, None, 'admin', self.user) is True
            user2 = User.query.filter_by(id=9).first()
            # returns false because non-creator can't revoke permission of creator
            assert fm.revoke_permission(p_id, 8, None, user2) is False
            assert fm.revoke_permission(p_id, 9, None, self.user) is True
            projects = fm.list_projects(user2)
            assert len(projects) == 2

    def test_get_project(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.user)
            assert fm.get_file(p_id, self.user) is not False
            user2 = User.query.filter_by(id=9).first()
            assert fm.get_file(p_id, user2) is False

    def test_authorized_users(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.user)
            assert len(fm.get_authorized_users(p_id)) == 1

    def test_modify_project(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.user)
            # testing for wrong characters in path like ' ', '/'
            assert fm.update_project(p_id, 'path', 'dummy wrong', self.user) is False
            assert fm.update_project(p_id, 'path', 'dummy/wrong', self.user) is False
            assert fm.update_project(p_id, 'path', 'dummy', self.user) is True
            assert os.path.exists(os.path.join(MSCOLAB_DATA_DIR, 'dummy'))
            assert fm.update_project(p_id, 'description', 'dummy', self.user) is True

    def test_delete_project(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.user)
            user2 = User.query.filter_by(id=9).first()
            assert fm.delete_file(p_id, user2) is False
            assert fm.delete_file(p_id, self.user) is True
            assert fm.delete_file(p_id, self.user) is False
            permissions = Permission.query.filter_by(p_id=p_id).all()
            assert len(permissions) == 0
            projects_db = Project.query.filter_by(id=p_id).all()
            assert len(projects_db) == 0
            changes = Change.query.filter_by(p_id=p_id).all()
            assert len(changes) == 0
            messages = Message.query.filter_by(p_id=p_id).all()
            assert len(messages) == 0

    def teardown(self):
        for socket in self.sockets:
            socket.disconnect()
        self.p.terminate()
