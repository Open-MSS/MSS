# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_mscolab_version_history
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module is used to test mscolab-project related gui.

    This file is part of mss.

    :copyright: Copyright 2020 Tanish Grover
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
import time

from mslib.msui.mscolab import MSSMscolabWindow
from mslib._tests.constants import MSCOLAB_URL_TEST
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import Change
from mslib.mscolab.server import APP, db, initialize_managers
from mslib.msui.mss_qt import QtCore, QtTest, QtWidgets


class Test_MscolabVersionHistory(object):
    def setup(self):
        # start mscolab server
        self.app = APP
        self.app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
        self.app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
        self.app, _, cm, fm = initialize_managers(self.app)
        self.fm = fm
        self.cm = cm
        db.init_app(self.app)
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = MSSMscolabWindow(data_dir=mscolab_settings.MSCOLAB_DATA_DIR,
                                       mscolab_server_url=MSCOLAB_URL_TEST)
        self._login()
        self._activate_project_at_index(0)
        # activate project window here by clicking button
        QtTest.QTest.mouseClick(self.window.versionHistoryBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        self.version_window = self.window.version_window
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        # to disconnect connections, and clear token
        # Not logging out since it pops up a dialog
        # self.window.logout()
        if self.window.version_window:
            self.window.version_window.close()
        if self.window.conn:
            self.window.conn.disconnect()
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    def test_changes(self):
        len_prev = self.version_window.changes.count()
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
        self.version_window.load_all_changes()
        QtWidgets.QApplication.processEvents()
        len_after = self.version_window.changes.count()
        # test change render
        assert len_prev == (len_after - 2)

    def test_undo(self):
        old_count = self.version_window.changes.count()
        self._activate_change_at_index(0)
        QtWidgets.QApplication.processEvents()
        self.version_window.request_undo_mscolab(self.version_window.changes.currentIndex())
        # wait till server emits event to reload
        time.sleep(2)
        self.version_window.load_all_changes()
        QtWidgets.QApplication.processEvents()
        assert self.version_window.changes.count() == old_count + 1
        # delete the changes
        with self.app.app_context():
            Change.query.filter_by(comment="dummy save").delete()
            db.session.commit()

    def _connect_to_mscolab(self):
        self.window.url.setEditText("http://localhost:8084")
        QtTest.QTest.mouseClick(self.window.connectMscolab, QtCore.Qt.LeftButton)
        time.sleep(0.5)

    def _login(self):
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
        item = self.version_window.changes.item(index)
        point = self.version_window.changes.visualItemRect(item).center()
        QtTest.QTest.mouseClick(self.version_window.changes.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.keyClick(self.version_window.changes.viewport(), QtCore.Qt.Key_Return)
        QtWidgets.QApplication.processEvents()
