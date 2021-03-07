# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_files
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for file based handlers

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
import socketio
import requests
import json
import os
from functools import partial
import time
import sys

from PyQt5 import QtWidgets

from werkzeug.urls import url_join

from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import db, User, Project, Change, Permission, Message
from mslib.mscolab.utils import get_recent_pid
from mslib._tests.utils import mscolab_register_and_login, mscolab_create_project, mscolab_start_server
from mslib.msui.mscolab import MSSMscolabWindow


PORTS = list(range(9361, 9380))


class Test_Files(object):
    def setup(self):
        self.process, self.url, self.app, _, self.cm, self.fm = mscolab_start_server(PORTS)
        time.sleep(0.5)
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = MSSMscolabWindow(data_dir=mscolab_settings.MSCOLAB_DATA_DIR,
                                       mscolab_server_url=self.url)
        self.window.show()

        self.sockets = []
        self.file_message_counter = [0] * 2
        with self.app.app_context():
            self.user = User.query.filter_by(id=8).first()

    def teardown(self):
        for socket in self.sockets:
            socket.disconnect()
        if self.window.version_window:
            self.window.version_window.close()
        if self.window.conn:
            self.window.conn.disconnect()
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        self.process.terminate()

    def test_create_project(self):
        with self.app.app_context():
            # test for blank character in path
            assert self.fm.create_project('test path', 'test desc.', self.user) is False
            # test for normal path
            assert self.fm.create_project('test_path', 'test desc.', self.user) is True
            # test for '/' in path
            assert self.fm.create_project('test/path', 'sth', self.user) is False
            # check file existence
            assert os.path.exists(os.path.join(mscolab_settings.MSCOLAB_DATA_DIR, 'test_path')) is True
            # check creation in db
            p = Project.query.filter_by(path="test_path").first()
            assert p is not None
            # check permission for author
            perms = Permission.query.filter_by(p_id=p.id, access_level="creator").all()
            assert len(perms) == 1
            assert perms[0].u_id == self.user.id

    def test_projects(self):
        with self.app.app_context():
            projects = self.fm.list_projects(self.user)
            assert len(projects) == 3

    def test_is_admin(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.fm, self.user)
            u_id = self.user.id
            assert self.fm.is_admin(u_id, p_id) is True
            undefined_p_id = 123
            assert self.fm.is_admin(u_id, undefined_p_id) is False
            no_perm_p_id = 2
            assert self.fm.is_admin(u_id, no_perm_p_id) is False

    def test_file_save(self):
        url = url_join(self.url, 'token')
        r = requests.post(url, data={
            'email': 'a',
            'password': 'a'
        })
        response1 = json.loads(r.text)
        r = requests.post(url, data={
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
        sio1.connect(self.url)
        sio2.connect(self.url)
        with self.app.app_context():
            p_id = get_recent_pid(self.fm, self.user)
            user2 = User.query.filter_by(id=9).first()
            perm = Permission(u_id=9, p_id=p_id, access_level="admin")
            db.session.add(perm)
            db.session.commit()
            sio1.emit('start', response1)
            sio2.emit('start', response2)
            time.sleep(0.5)
            sio1.emit('file-save', {
                      "p_id": p_id,
                      "token": response1['token'],
                      "content": "file save content 1"
                      })
            time.sleep(0.5)
            # second file change
            sio1.emit('file-save', {
                      "p_id": p_id,
                      "token": response1['token'],
                      "content": "file save content 2"
                      })
            time.sleep(0.5)
            # check if there were events triggered related to file-save
            assert self.file_message_counter[0] == 2
            assert self.file_message_counter[1] == 2
            # check if content is saved in file
            assert self.fm.get_file(p_id, user2) == "file save content 2"
            # check if change is saved properly
            changes = self.fm.get_all_changes(p_id, self.user)
            assert len(changes) == 2
            change = Change.query.order_by(Change.created_at.desc()).first()
            change_content = self.fm.get_change_content(change.id)
            assert change_content == "file save content 2"
            perm = Permission.query.filter_by(u_id=9, p_id=p_id).first()
            db.session.delete(perm)
            db.session.commit()
            # to disconnect sockets later
            self.sockets.append(sio1)
            self.sockets.append(sio2)

    def test_undo(self):
        url = url_join(self.url, 'token')
        r = requests.post(url, data={
            'email': 'a',
            'password': 'a'
        })
        response1 = json.loads(r.text)
        r = requests.post(url, data={
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
        sio1.connect(self.url)
        sio2.connect(self.url)
        with self.app.app_context():
            p_id = get_recent_pid(self.fm, self.user)
            User.query.filter_by(id=9).first()
            perm = Permission(u_id=9, p_id=p_id, access_level="admin")
            db.session.add(perm)
            db.session.commit()
            sio1.emit('start', response1)
            sio2.emit('start', response2)
            time.sleep(0.5)
            sio1.emit('file-save', {
                "p_id": p_id,
                "token": response1['token'],
                "content": "file save content 1"
            })
            time.sleep(0.5)
            # second file change
            sio1.emit('file-save', {
                "p_id": p_id,
                "token": response1['token'],
                "content": "file save content 2"
            })
            time.sleep(0.5)
        with self.app.app_context():
            p_id = get_recent_pid(self.fm, self.user)
            changes = Change.query.filter_by(p_id=p_id).all()
            assert self.fm.undo(changes[0].id, self.user) is True
            assert len(self.fm.get_all_changes(p_id, self.user)) == 3
            assert self.fm.get_file(p_id, self.user) == "file save content 1"

    def test_get_project(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.fm, self.user)
            assert self.fm.get_file(p_id, self.user) is not False
            user2 = User.query.filter_by(id=9).first()
            assert self.fm.get_file(p_id, user2) is False

    def test_authorized_users(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.fm, self.user)
            assert p_id == 4
            assert len(self.fm.get_authorized_users(p_id)) == 2

    def test_modify_project(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.fm, self.user)
            # testing for wrong characters in path like ' ', '/'
            assert self.fm.update_project(p_id, 'path', 'dummy wrong', self.user) is False
            assert self.fm.update_project(p_id, 'path', 'dummy/wrong', self.user) is False
            assert self.fm.update_project(p_id, 'path', 'dummy', self.user) is True
            assert os.path.exists(os.path.join(mscolab_settings.MSCOLAB_DATA_DIR, 'dummy'))
            assert self.fm.update_project(p_id, 'description', 'dummy', self.user) is True

    def test_delete_project(self):
        with self.app.app_context():
            response = mscolab_register_and_login(self.app, self.url, 'a', 'a', 'a')
            data, response = mscolab_create_project(self.app, self.url, response,
                                                    path='f3', description='f3 test example')
            p_id = get_recent_pid(self.fm, self.user)
            assert p_id == 7
            assert response.status == '200 OK'
            user2 = User.query.filter_by(id=9).first()
            assert self.fm.delete_file(p_id, user2) is False
            assert self.fm.delete_file(p_id, self.user) is True
            assert self.fm.delete_file(p_id, self.user) is False
            permissions = Permission.query.filter_by(p_id=p_id).all()
            assert len(permissions) == 0
            projects_db = Project.query.filter_by(id=p_id).all()
            assert len(projects_db) == 0
            changes = Change.query.filter_by(p_id=p_id).all()
            assert len(changes) == 0
            messages = Message.query.filter_by(p_id=p_id).all()
            assert len(messages) == 0
