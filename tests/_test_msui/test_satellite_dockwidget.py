# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_satellite_dockwidget
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.satellite_dockwidget

    This file is part of MSS.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017-2023 by the MSS team, see AUTHORS.
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
import mock
from PyQt5 import QtWidgets, QtCore, QtTest
import mslib.msui.satellite_dockwidget as sd


class Test_SatelliteDockWidget(object):
    def setup_method(self):
        self.application = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        self.view = mock.Mock()
        self.window = sd.SatelliteControlWidget(view=self.view)
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown_method(self):
        self.window.close()
        self.window.deleteLater()
        QtWidgets.QApplication.processEvents()

    def test_load(self):
        path = os.path.join(os.path.dirname(__file__), "../", "data", "satellite_predictor.txt")
        self.window.leFile.setText(path)
        assert self.window.cbSatelliteOverpasses.count() == 0
        QtTest.QTest.mouseClick(self.window.btLoadFile, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert self.window.cbSatelliteOverpasses.count() == 11
        assert self.view.plot_satellite_overpass.call_count == 1
        self.window.cbSatelliteOverpasses.currentIndexChanged.emit(2)
        QtWidgets.QApplication.processEvents()
        assert self.view.plot_satellite_overpass.call_count == 2
        self.view.reset_mock()

    @mock.patch("PyQt5.QtWidgets.QMessageBox.critical")
    def test_load_no_file(self, mockbox):
        QtTest.QTest.mouseClick(self.window.btLoadFile, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert self.window.cbSatelliteOverpasses.count() == 0
        mockbox.assert_called_once_with(
            self.window,
            "Satellite Overpass Tool",
            "ERROR:\n<class 'fs.errors.FileExpected'>\npath '' should be a file",
        )
