# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_mscolab_project
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module is used to test mscolab-project related gui.

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

import sys
from mslib.msui.mss_qt import QtWidgets, QtTest, QtCore
import logging
import multiprocessing
import time

from mslib.mscolab.server import db, sockio, app
from mslib.mscolab.models import Message, Change
import mslib.msui.mscolab as mc


class Test_Mscolab(object):
    def setup(self):

        # start mscolab server
        self._app = app
        db.init_app(self._app)
        self.p = multiprocessing.Process(
            target=sockio.run,
            args=(app,),
            kwargs={'port': 8083})
        self.p.start()
        time.sleep(1)

        logging.debug("starting")
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = mc.MSSMscolabWindow()
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
        self.window.logout()
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
        # close mscolab server
        self.p.terminate()

    def test_changes(self):
        len_prev = self.proj_window.changes.count()
        # make a change
        self.window.waypoints_model.invert_direction()
        # save it with a comment
        self.window.save_wp_mscolab(comment="dummy save")
        QtWidgets.QApplication.processEvents()
        # test doesn't work without the sleep, because of delay in adding change and commit
        time.sleep(3)
        # change again for db consistency
        self.window.waypoints_model.invert_direction()
        self.window.save_wp_mscolab(comment="dummy save")
        QtWidgets.QApplication.processEvents()
        # fetch wp/chats/project
        self.window.reload_window(self.window.active_pid)
        QtWidgets.QApplication.processEvents()
        len_after = self.proj_window.changes.count()
        # test change render
        assert len_prev == (len_after - 2)
        # delete the change
        with self._app.app_context():
            Change.query.filter_by(comment="dummy save").delete()
            db.session.commit()

    def test_chat(self):
        self.proj_window.messageText.setPlainText('some - message')
        QtTest.QTest.mouseClick(self.proj_window.sendMessage, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        # delete message from db here
        # wait till server processes the change
        time.sleep(3)
        with self._app.app_context():
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

    def _login(self):
        # login
        self.window.emailid.setText('a')
        self.window.password.setText('a')
        QtTest.QTest.mouseClick(self.window.loginButton, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()

    def _activate_project_at_index(self, index):
        item = self.window.listProjects.item(index)
        point = self.window.listProjects.visualItemRect(item).center()
        QtTest.QTest.mouseClick(self.window.listProjects.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.keyClick(self.window.listProjects.viewport(), QtCore.Qt.Key_Return)
        QtWidgets.QApplication.processEvents()
