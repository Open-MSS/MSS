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
import pytest
import mock

from mslib._tests.utils import mscolab_start_server
from mslib.msui.mscolab import MSSMscolabWindow
from mslib.mscolab.conf import mscolab_settings
from PyQt5 import QtCore, QtTest, QtWidgets


PORTS = list(range(9591, 9620))


class Test_MscolabVersionHistory(object):
    def setup(self):
        self.process, self.url, self.app, _, self.cm, self.fm = mscolab_start_server(PORTS)
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = MSSMscolabWindow(data_dir=mscolab_settings.MSCOLAB_DATA_DIR,
                                       mscolab_server_url=self.url)
        self.window.show()
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
        self.process.terminate()

    def test_changes(self):
        self._change_version_filter(1)
        len_prev = self.version_window.changes.count()
        # make a changes
        self.window.waypoints_model.invert_direction()
        QtWidgets.QApplication.processEvents()
        time.sleep(4)
        self.window.waypoints_model.invert_direction()
        QtWidgets.QApplication.processEvents()
        time.sleep(4)
        self.version_window.load_all_changes()
        QtWidgets.QApplication.processEvents()
        len_after = self.version_window.changes.count()
        assert len_prev == (len_after - 2)

    @mock.patch("PyQt5.QtWidgets.QInputDialog.getText", return_value=["MyVersionName", True])
    def test_set_version_name(self, mockbox):
        pytest.skip('check xdist dependencies')
        self._change_version_filter(1)
        self._activate_change_at_index(0)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.version_window.nameVersionBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        time.sleep(4)
        assert self.version_window.changes.currentItem().version_name == "MyVersionName"

    def test_version_name_filter(self):
        pytest.skip('check xdist dependencies')
        assert self.version_window.changes.count() == 1

    def test_version_name_delete(self):
        self._activate_change_at_index(0)
        QtTest.QTest.mouseClick(self.version_window.deleteVersionNameBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        time.sleep(4)
        assert self.version_window.changes.count() == 0

    @mock.patch("PyQt5.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.Yes)
    def test_undo(self, mockbox):
        pytest.skip('check xdist dependencies')
        self._change_version_filter(1)
        changes_count = self.version_window.changes.count()
        self._activate_change_at_index(1)
        QtTest.QTest.mouseClick(self.version_window.checkoutBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        time.sleep(4)
        new_changes_count = self.version_window.changes.count()
        assert changes_count + 1 == new_changes_count

    def test_refresh(self):
        self._change_version_filter(1)
        changes_count = self.version_window.changes.count()
        self.window.waypoints_model.invert_direction()
        QtWidgets.QApplication.processEvents()
        time.sleep(4)
        self.window.waypoints_model.invert_direction()
        QtWidgets.QApplication.processEvents()
        time.sleep(4)
        QtTest.QTest.mouseClick(self.version_window.refreshBtn, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        time.sleep(4)
        new_changes_count = self.version_window.changes.count()
        assert new_changes_count == changes_count + 2

    def _connect_to_mscolab(self):
        self.window.url.setEditText(self.url)
        QtTest.QTest.mouseClick(self.window.connectMscolab, QtCore.Qt.LeftButton)
        time.sleep(1)

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
        time.sleep(2)

    def _change_version_filter(self, index):
        self.version_window.versionFilterCB.setCurrentIndex(index)
        self.version_window.versionFilterCB.currentIndexChanged.emit(index)
        QtWidgets.QApplication.processEvents()
        time.sleep(4)
