# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_mscolab_project
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module is used to test mscolab-project related gui.

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

import sys
from mslib.msui.mss_qt import QtWidgets, QtTest, QtCore
import logging
import time

from mslib.mscolab.server import db, app, initialize_managers
from mslib._tests.constants import MSCOLAB_URL_TEST
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import Message, Change
import mslib.msui.mscolab as mc


class Test_MscolabProject(object):
    def setup(self):

        # start mscolab server
        self.app = app
        self.app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
        self.app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
        self.app, _, cm, fm = initialize_managers(self.app)
        self.fm = fm
        self.cm = cm
        db.init_app(self.app)

        logging.debug("starting")
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = mc.MSSMscolabWindow(data_dir=mscolab_settings.MSCOLAB_DATA_DIR,
                                          mscolab_server_url=MSCOLAB_URL_TEST)
        self._login()
        self._activate_project_at_index(0)
        # activate project window here by clicking button
        QtTest.QTest.mouseClick(self.window.projWindow, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        self.proj_window = self.window.project_window
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        # to disconnect connections, and clear token
        # Not logging out since it pops up a dialog
        # self.window.logout()
        for window in self.window.active_windows:
            window.hide()
        if self.window.project_window:
            self.window.project_window.hide()
        self.window.hide()
        if self.window.conn:
            self.window.conn.disconnect()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    def test_changes(self):
        len_prev = self.proj_window.changes.count()
        # make a change
        self.window.waypoints_model.invert_direction()
        # save it with a comment
        self.window.save_wp_mscolab(comment="dummy save")
        QtWidgets.QApplication.processEvents()
        # test doesn't work without the sleep, because of delay in adding change and commit
        time.sleep(2)
        # change again for db consistency
        self.window.waypoints_model.invert_direction()
        self.window.save_wp_mscolab(comment="dummy save")
        QtWidgets.QApplication.processEvents()
        time.sleep(2)
        # fetch wp/chats/project
        self.window.reload_window(self.window.active_pid)
        QtWidgets.QApplication.processEvents()
        self.proj_window.load_all_changes()
        QtWidgets.QApplication.processEvents()
        len_after = self.proj_window.changes.count()
        # test change render
        assert len_prev == (len_after - 2)

    def test_undo(self):
        old_count = self.proj_window.changes.count()
        self._activate_change_at_index(0)
        QtWidgets.QApplication.processEvents()
        self.proj_window.request_undo_mscolab(self.proj_window.changes.currentIndex())
        # wait till server emits event to reload
        time.sleep(3)
        self.proj_window.load_all_changes()
        QtWidgets.QApplication.processEvents()
        assert self.proj_window.changes.count() == old_count + 1
        # delete the changes
        with self.app.app_context():
            Change.query.filter_by(comment="dummy save").delete()
            db.session.commit()

    def test_chat(self):
        self.proj_window.messageText.setPlainText('some - message')
        QtTest.QTest.mouseClick(self.proj_window.sendMessage, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        # delete message from db here
        # wait till server processes the change
        time.sleep(3)
        with self.app.app_context():
            assert Message.query.filter_by(text='some - message').count() == 1
            Message.query.filter_by(text='some - message').delete()
            db.session.commit()

    def test_users(self):
        assert self.proj_window.collaboratorsList.count() == 3
        # test remove/add/update collaborator
        self.proj_window.username.setText('c')
        QtTest.QTest.mouseClick(self.proj_window.delete_1, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        self.proj_window.accessLevel.setCurrentIndex(0)
        QtTest.QTest.mouseClick(self.proj_window.add, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        self.proj_window.accessLevel.setCurrentIndex(2)
        QtTest.QTest.mouseClick(self.proj_window.modify, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()

    def _connect_to_mscolab(self):
        self.window.url.setEditText("http://localhost:8084")
        QtTest.QTest.mouseClick(self.window.connectMscolab, QtCore.Qt.LeftButton)
        time.sleep(0.5)

    def _login(self):
        # login
        self._connect_to_mscolab()
        self.window.emailid.setText('a')
        self.window.password.setText('a')
        QtTest.QTest.mouseClick(self.window.loginButton, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()

    def _activate_project_at_index(self, index):
        item = self.window.listProjects.item(index)
        point = self.window.listProjects.visualItemRect(item).center()
        QtTest.QTest.mouseClick(self.window.listProjects.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseDClick(self.window.listProjects.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()

    def _activate_change_at_index(self, index):
        item = self.proj_window.changes.item(index)
        point = self.proj_window.changes.visualItemRect(item).center()
        QtTest.QTest.mouseClick(self.proj_window.changes.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.keyClick(self.proj_window.changes.viewport(), QtCore.Qt.Key_Return)
        QtWidgets.QApplication.processEvents()
