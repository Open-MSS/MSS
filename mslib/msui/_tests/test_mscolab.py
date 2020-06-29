# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_mscolab
    ~~~~~~~~~~~~~~~~~~~

    This module is used to test mscolab related gui.

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
import logging
import sys
import time
import mock

from mslib.msui.mscolab import MSSMscolabWindow
from mslib._tests.constants import MSCOLAB_URL_TEST
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import Project
from mslib.mscolab.server import APP, db, initialize_managers
from mslib.msui.mss_qt import QtCore, QtTest, QtWidgets


class Test_Mscolab(object):
    def setup(self):
        logging.debug("starting")
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = MSSMscolabWindow(data_dir=mscolab_settings.MSCOLAB_DATA_DIR,
                                       mscolab_server_url=MSCOLAB_URL_TEST)
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()

        self.app = APP
        self.app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
        self.app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
        self.app, _, cm, fm = initialize_managers(self.app)
        self.fm = fm
        self.cm = cm
        db.init_app(self.app)

    def teardown(self):
        # to disconnect connections, and clear token
        self.window.logout()
        for window in self.window.active_windows:
            window.hide()
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    def test_url_combo(self):
        assert self.window.url.count() >= 1

    def test_login(self):
        self._login()
        # screen shows logout button
        assert self.window.loggedInWidget.isVisible() is True
        assert self.window.loginWidget.isVisible() is False
        # test project listing visibility
        assert self.window.listProjects.model().rowCount() == 3
        # test logout
        QtTest.QTest.mouseClick(self.window.logoutButton, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert self.window.loggedInWidget.isVisible() is False
        assert self.window.loginWidget.isVisible() is True

    def test_disconnect(self):
        self._connect_to_mscolab()
        QtTest.QTest.mouseClick(self.window.disconnectMscolab, QtCore.Qt.LeftButton)
        assert self.window.mscolab_server_url is None

    def _connect_to_mscolab(self):
        self.window.url.setEditText("http://localhost:8084")
        QtTest.QTest.mouseClick(self.window.connectMscolab, QtCore.Qt.LeftButton)
        time.sleep(0.5)

    def _login(self, emailid="a", password="a"):
        # login
        self._connect_to_mscolab()
        self.window.emailid.setText(emailid)
        self.window.password.setText(password)
        QtTest.QTest.mouseClick(self.window.loginButton, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()

    def test_activate_project(self):
        self._login()
        # activate a project
        self._activate_project_at_index(0)
        assert self.window.active_pid is not None

    def _activate_project_at_index(self, index):
        item = self.window.listProjects.item(index)
        point = self.window.listProjects.visualItemRect(item).center()
        QtTest.QTest.mouseClick(self.window.listProjects.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseDClick(self.window.listProjects.viewport(), QtCore.Qt.LeftButton, pos=point)
        QtWidgets.QApplication.processEvents()

    def test_view_open(self):
        self._login()
        # test without activating project
        QtTest.QTest.mouseClick(self.window.topview, QtCore.Qt.LeftButton)
        QtTest.QTest.mouseClick(self.window.sideview, QtCore.Qt.LeftButton)
        QtTest.QTest.mouseClick(self.window.tableview, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len(self.window.active_windows) == 0
        # test after activating project
        self._activate_project_at_index(0)
        QtTest.QTest.mouseClick(self.window.tableview, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len(self.window.active_windows) == 1
        QtTest.QTest.mouseClick(self.window.topview, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len(self.window.active_windows) == 2
        QtTest.QTest.mouseClick(self.window.sideview, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len(self.window.active_windows) == 3

    def test_save_fetch(self):

        self._login()
        self._activate_project_at_index(0)
        # change waypoint
        self.window.waypoints_model.invert_direction()
        wpdata1 = self.window.waypoints_model.waypoint_data(0)
        # don't save, fetch
        QtTest.QTest.mouseClick(self.window.fetch_ft, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        wpdata2 = self.window.waypoints_model.waypoint_data(0)
        assert wpdata2.lat != wpdata1.lat
        # save, fetch
        self.window.waypoints_model.invert_direction()
        wpdata1 = self.window.waypoints_model.waypoint_data(0)
        QtTest.QTest.mouseClick(self.window.save_ft, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        time.sleep(2)  # for change to take place
        QtTest.QTest.mouseClick(self.window.fetch_ft, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        wpdata2 = self.window.waypoints_model.waypoint_data(0)
        assert wpdata2.lat == wpdata1.lat
        # to undo changes
        self.window.waypoints_model.invert_direction()
        QtTest.QTest.mouseClick(self.window.save_ft, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        # to let server process
        time.sleep(2)

    def test_autosave(self):
        self._login()
        self._activate_project_at_index(0)
        QtTest.QTest.mouseClick(self.window.autoSave, QtCore.Qt.LeftButton,
                                pos=QtCore.QPoint(2, self.window.autoSave.height() / 2))
        QtWidgets.QApplication.processEvents()
        # sleeping to let server do the change
        time.sleep(3)
        with self.app.app_context():
            project = Project.query.filter_by(id=self.window.active_pid).first()
        assert project.autosave is self.window.autoSave.isChecked()
        QtTest.QTest.mouseClick(self.window.autoSave, QtCore.Qt.LeftButton,
                                pos=QtCore.QPoint(2, self.window.autoSave.height() / 2))
        QtWidgets.QApplication.processEvents()
        # top let server process
        time.sleep(2)

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.Yes)
    def test_user_delete(self, mockbox):
        self._login(emailid="d", password="d")
        QtTest.QTest.mouseClick(self.window.deleteAccountButton, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert len(self.window.listProjects) == 0
        assert self.window.loggedInWidget.isVisible() is False
        assert self.window.loginWidget.isVisible() is True
