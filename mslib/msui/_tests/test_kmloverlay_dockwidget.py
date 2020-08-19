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
import fs
import sys
import mock
from mslib.msui.mss_qt import QtWidgets, QtCore, QtTest, QtGui
import mslib.msui.kmloverlay_dockwidget as kd
import mslib.msui.topview as tv
from mslib.msui.viewwindows import MSSMplViewWindow


class Test_KmlOverlayDockWidget(object):
    sample_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "samples")

    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)
        self.view = mock.Mock()
        self.view.map = mock.Mock(side_effect=lambda x, y: (x, y))
        self.view.map.plot = mock.Mock(return_value=[mock.Mock()])
        self.window = kd.KMLOverlayControlWidget(view=self.view)
        # self.abc = kd.KMLPatch(self.window)
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        # start load test
        self.window.remove_all_files()
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        del self.window

    def select_file(self, file):  # Utility function for single file
        path = fs.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "samples", "kml", file)
        filename = (path,)  # converted to tuple
        self.window.select_file(filename)
        QtWidgets.QApplication.processEvents()

    def select_files(self):  # Utility function
        for sample in ["folder.kml", "line.kml", "color.kml", "style.kml", "features.kml"]:
            path = fs.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "samples", "kml", sample)
            filename = (path,)  # converted to tuple
            self.window.select_file(filename)
            QtWidgets.QApplication.processEvents()

    @mock.patch("mslib.msui.kmloverlay_dockwidget.get_open_filenames",
                return_value=[os.path.join(sample_path, "kml", "line.kml")])
    def test_get_file(self, mockopen):  # Tests opening of QFileDialog
        QtTest.QTest.mouseClick(self.window.btSelectFile, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert mockopen.call_count == 1

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_select_file(self, mockbox):
        index = 0
        assert self.window.listWidget.count() == 0
        for sample in ["folder.kml", "line.kml", "color.kml", "style.kml", "features.kml",
                       "geometry_collection.kml", "Multilinestrings.kml", "polygon_inner.kml",
                       "World_Map.kml"]:
            path = fs.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "samples", "kml", sample)
            filename = (path,)  # converted to tuple
            self.window.select_file(filename)
            QtWidgets.QApplication.processEvents()
            QtTest.QTest.qWait(250)
            assert self.window.listWidget.item(index).checkState() == QtCore.Qt.Checked
            index = index + 1
        assert self.window.directory_location == path
        assert mockbox.critical.call_count == 0
        assert self.window.listWidget.count() == index
        assert len(self.window.dict_files) == index
        assert self.window.patch is not None
        self.window.remove_all_files()

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_select_file_error(self, mockbox):
        """
        Test that program mitigates loading a non-existing file
        """
        # load a non existing path
        self.window.remove_all_files()
        path = fs.path.join(os.path.dirname(__file__), "..", "..", "..", "docs",
                            "samples", "satellite_tracks", "satellite_predictor.txt")
        filename = (path,)  # converted to tuple
        self.window.select_file(filename)
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 1
        self.window.listWidget.clear()
        self.window.dict_files = {}

    def test_remove_file(self):
        self.select_files()
        QtWidgets.QApplication.processEvents()
        self.window.listWidget.item(0).setCheckState(QtCore.Qt.Unchecked)
        QtTest.QTest.mouseClick(self.window.pushButton_remove, QtCore.Qt.LeftButton)
        assert self.window.listWidget.count() == 1
        assert len(self.window.dict_files) == 1
        self.window.remove_all_files()

    def test_remove_all_files(self):
        self.select_files()
        QtWidgets.QApplication.processEvents()
        assert self.window.listWidget.count() == 5
        QtTest.QTest.mouseClick(self.window.pushButton_remove_all, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert self.window.listWidget.count() == 0  # No items in list
        assert self.window.dict_files == {}  # Dictionary should be empty
        assert self.window.patch is None   # Patch should be None

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_merge_file(self, mockbox):
        self.select_files()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.window.pushButton_merge, QtCore.Qt.LeftButton)
        path = fs.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "samples", "kml", "output.kml")
        filename = (path,)
        self.window.select_file(filename)
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0
        self.window.remove_all_files()

    # def test_check_uncheck(self):
    #     self.select_file("line.kml")
    #     assert self.window.listWidget.item(0).checkState() == QtCore.Qt.Checked
    #     self.window.listWidget.item(0).setCheckState(QtCore.Qt.Unchecked)
    #     assert self.window.listWidget.item(0).checkState() == QtCore.Qt.Unchecked
        

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QColorDialog.getColor", return_value=QtGui.QColor().setRgbF(1,1,1,1))
    def test_customize(self, mock_colour_dialog):
        self.select_file("line.kml")
        assert self.window.listWidget.count() == 1
        item = self.window.listWidget.item(0)
        rect = self.window.listWidget.visualItemRect(item)
        QtTest.QTest.mouseClick(self.window.listWidget.viewport(),
                                QtCore.Qt.LeftButton,
                                pos=rect.center())  # in testing, need to add mouseclick before double click
        QtWidgets.QApplication.processEvents()
        # Double click feature
        QtTest.QTest.mouseDClick(self.window.listWidget.viewport(),
                                QtCore.Qt.LeftButton,
                                pos=rect.center())
        QtWidgets.QApplication.processEvents()
        # Clicking on Push Button Colour
        QtTest.QTest.mouseClick(self.window.dialog.pushButton_colour, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseDClick(self.window.dialog.pushButton_colour, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert mock_colour_dialog.call_count == 1

        # Testing the Double Spin Box
        self.window.dialog.dsb_linewidth.setValue(3)
        assert self.window.dialog.dsb_linewidth.value() == 3
        QtTest.QTest.qWait(3000)

        # clicking on OK Button
        okWidget = self.window.dialog.buttonBox.button(self.window.dialog.buttonBox.Ok)
        QtTest.QTest.mouseClick(okWidget, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(3000)
        self.window.remove_file()
        assert self.window.listWidget.count() == 0




