# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_kmloverlay_dockwidget
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.kmloverlay_dockwidget

    This file is part of mss.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017-2020 by the mss team, see AUTHORS.
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
import sys
import mock
from mslib.msui.mss_qt import QtWidgets, QtCore, QtTest
import mslib.msui.kmloverlay_dockwidget as kd


class Test_KmlOverlayDockWidget(object):
    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)
        self.view = mock.Mock()
        self.view.map = mock.Mock(side_effect=lambda x, y: (x, y))
        self.view.map.plot = mock.Mock(return_value=[mock.Mock()])
        self.window = kd.KMLOverlayControlWidget(view=self.view)
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        # start load test
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        del self.window

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_load_error(self, mockbox):
        """
        Test that program mitigates loading a non-existing file
        """
        # load a non existing path
        path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs",
                            "samples", "satellite_tracks", "satellite_predictor.txt")
        self.window.leFile.setText(path)
        QtTest.QTest.mouseClick(self.window.btLoadFile, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 1

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_load(self, mockbox):
        """
        Test for flawless loading of parsing of KML files
        """
        for sample in ["folder.kml", "line.kml", "color.kml", "style.kml", "features.kml"]:
            path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "samples", "kml", sample)
            self.window.leFile.setText(path)
            QtTest.QTest.mouseClick(self.window.btLoadFile, QtCore.Qt.LeftButton)
            QtWidgets.QApplication.processEvents()
            assert mockbox.critical.call_count == 0

    def test_styles(self):
        """
        Test for changing styles and toggling visibility
        """
        self.test_load()
        # disable/enable overlay
        QtTest.QTest.mouseClick(self.window.cbOverlay, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.window.cbOverlay, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        # disable/enable styles
        QtTest.QTest.mouseClick(self.window.cbManualStyle, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.window.cbManualStyle, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
