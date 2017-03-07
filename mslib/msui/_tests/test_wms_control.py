# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_wms_control
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.wms_control

    This file is part of mss.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017 by the mss team, see AUTHORS.
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
import paste
import paste.httpserver
import shutil
import tempfile
import multiprocessing

from mslib.msui import flighttrack as ft
from mslib._tests.utils import BASE_DIR, close_modal_messagebox

# important so wms finds the mss_wms_settings file in BASE_DIR
sys.path.append(BASE_DIR)

import mslib.mswms.wms
from mslib.msui.mss_qt import QtWidgets, QtCore, QtTest
import mslib.msui.wms_control as wc


class HSecViewMockup(mock.Mock):
    getCRS = mock.Mock(return_value="EPSG:4326")
    getBBOX = mock.Mock(return_value=(0, 0, 10, 10))
    getPlotSizePx = mock.Mock(return_value=(200, 100))


class VSecViewMockup(mock.Mock):
    getCRS = mock.Mock(return_value="VERT:LOGP")
    getBBOX = mock.Mock(return_value=(3, 500, 3, 10))
    getPlotSizePx = mock.Mock(return_value=(200, 100))


class Test_HSecWMSControlWidget(object):
    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)
        self.view = HSecViewMockup()
        self.tempdir = tempfile.mkdtemp()
        if not os.path.exists(self.tempdir):
            os.mkdir(self.tempdir)
        self.thread = multiprocessing.Process(
            target=paste.httpserver.serve,
            args=(mslib.mswms.wms.application,),
            kwargs={"host": "127.0.0.1", "port": "8082", "use_threadpool": False})
        self.thread.start()
        self.window = wc.HSecWMSControlWidget(view=self.view, wms_cache=self.tempdir)
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(2000)
        QtTest.QTest.qWaitForWindowShown(self.window)
        QtTest.QTest.mouseClick(self.window.cbCacheEnabled, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        shutil.rmtree(self.tempdir)
        self.thread.terminate()
        # the next del statement should not be necessary, but the windows stay around without it.
        # It sometimes also cause the QThread terminated early statement, wich should be prevented
        # by the stuff in del __del__ function...
        del self.window
        #  sys.exit(self.application.exec_())

    def query_server(self, url):
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.keyClicks(self.window.cbWMS_URL, url)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.window.btGetCapabilities, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(2000)

    def test_no_server(self):
        """
        assert that a message box informs about server troubles
        """
        self.query_server("http://127.0.0.1:8083")
        assert close_modal_messagebox(self.window)

    def test_server_abort_getmap(self):
        """
        assert that an aborted getmap call does not change the displayed image
        """
        self.query_server("http://127.0.0.1:8082")

        QtTest.QTest.mouseClick(self.window.btGetMap, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(20)
        QtTest.QTest.keyClick(self.window.pdlg, QtCore.Qt.Key_Enter)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(2000)

        assert self.view.drawImage.call_count == 0
        assert self.view.drawLegend.call_count == 0
        assert self.view.drawMetadata.call_count == 0
        self.view.reset_mock()

    def test_server_getmap(self):
        """
        assert that a getmap call to a WMS server displays an image
        """
        self.query_server("http://127.0.0.1:8082")

        QtTest.QTest.mouseClick(self.window.btGetMap, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(2000)
        assert not close_modal_messagebox(self.window)

        assert self.view.drawImage.call_count == 1
        assert self.view.drawLegend.call_count == 1
        assert self.view.drawMetadata.call_count == 1
        self.view.reset_mock()

    def test_server_service_cache(self):
        """
        assert that changing between servers still allows image retrieval
        """
        self.query_server("http://127.0.0.1:8082")
        assert not close_modal_messagebox(self.window)

        QtTest.QTest.keyClick(self.window.cbWMS_URL, QtCore.Qt.Key_Backspace)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.window.btGetCapabilities, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        assert close_modal_messagebox(self.window)
        assert self.view.drawImage.call_count == 0
        assert self.view.drawLegend.call_count == 0
        assert self.view.drawMetadata.call_count == 0

        QtTest.QTest.keyClick(self.window.cbWMS_URL, QtCore.Qt.Key_2)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.window.btGetMap, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(2000)

        assert self.view.drawImage.call_count == 1
        assert self.view.drawLegend.call_count == 1
        assert self.view.drawMetadata.call_count == 1
        self.view.reset_mock()

    # def test_get_all_maps(self):
    #     self.query_server("http://127.0.0.1:8082")
    #
    #     for layer_idx in range(self.window.cbLayer.count()):
    #         self.window.cbLayer.setCurrentIndex(layer_idx)
    #         self.window.cb_init_time_back_click()
    #         self.window.cb_valid_time_back_click()
    #         for style_idx in range(self.window.cbStyle.count()):
    #             self.window.cbStyle.setCurrentIndex(style_idx)
    #             QtTest.QTest.mouseClick(self.window.btGetMap, QtCore.Qt.LeftButton)
    #             QtWidgets.QApplication.processEvents()
    #             QtTest.QTest.qWait(2000)
    #             assert not close_modal_messagebox(self.window)
    #
    #             assert self.view.drawImage.call_count == 1
    #             assert self.view.drawLegend.call_count == 1
    #             assert self.view.drawMetadata.call_count == 1
    #             self.view.reset_mock()
    #             if layer_idx > 2:
    #                 break


class Test_VSecWMSControlWidget(object):
    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)
        self.view = VSecViewMockup()
        self.tempdir = tempfile.mkdtemp()
        if not os.path.exists(self.tempdir):
            os.mkdir(self.tempdir)
        self.thread = multiprocessing.Process(
            target=paste.httpserver.serve,
            args=(mslib.mswms.wms.application,),
            kwargs={"host": "127.0.0.1", "port": "8082", "use_threadpool": False})
        self.thread.start()

        initial_waypoints = [ft.Waypoint(40., 25., 0), ft.Waypoint(60., -10., 0), ft.Waypoint(40., 10, 0)]
        waypoints_model = ft.WaypointsTableModel("")
        waypoints_model.insertRows(
            0, rows=len(initial_waypoints), waypoints=initial_waypoints)
        self.window = wc.VSecWMSControlWidget(
            view=self.view, wms_cache=self.tempdir, waypoints_model=waypoints_model)
        self.window.show()

        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(2000)
        QtTest.QTest.qWaitForWindowShown(self.window)
        QtTest.QTest.mouseClick(self.window.cbCacheEnabled, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        shutil.rmtree(self.tempdir)
        self.thread.terminate()
        del self.window

    def query_server(self, url):
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.keyClicks(self.window.cbWMS_URL, url)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.window.btGetCapabilities, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(2000)

    def test_server_getmap(self):
        """
        assert that a getmap call to a WMS server displays an image
        """
        self.query_server("http://127.0.0.1:8082")
        QtTest.QTest.mouseClick(self.window.btGetMap, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(2000)

        assert not close_modal_messagebox(self.window)
        assert self.view.drawImage.call_count == 1
        assert self.view.drawLegend.call_count == 1
        assert self.view.drawMetadata.call_count == 1
        self.view.reset_mock()
