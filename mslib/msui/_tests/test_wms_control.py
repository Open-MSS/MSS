# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_wms_control
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.wms_control

    This file is part of mss.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017-2021 by the mss team, see AUTHORS.
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
import shutil
import tempfile
import pytest
import hashlib
import multiprocessing
from mslib.mswms.mswms import application
from PyQt5 import QtWidgets, QtCore, QtTest
from mslib.msui import flighttrack as ft
import mslib.msui.wms_control as wc
from mslib.msui.mss_pyui import MSSMainWindow
from mslib._tests.utils import wait_until_signal


PORTS = list(range(8107, 8125))


class HSecViewMockup(mock.Mock):
    get_crs = mock.Mock(return_value="EPSG:4326")
    getBBOX = mock.Mock(return_value=(0, 0, 10, 10))
    get_plot_size_in_px = mock.Mock(return_value=(200, 100))


class VSecViewMockup(mock.Mock):
    get_crs = mock.Mock(return_value="VERT:LOGP")
    getBBOX = mock.Mock(return_value=(3, 500, 3, 10))
    get_plot_size_in_px = mock.Mock(return_value=(200, 100))


class WMSControlWidgetSetup(object):
    def _setup(self, widget_type):
        self.port = PORTS.pop()
        self.application = QtWidgets.QApplication(sys.argv)
        if widget_type == "hsec":
            self.view = HSecViewMockup()
        else:
            self.view = VSecViewMockup()
        self.tempdir = tempfile.mkdtemp()
        if not os.path.exists(self.tempdir):
            os.mkdir(self.tempdir)
        QtTest.QTest.qWait(3000)
        self.thread = multiprocessing.Process(
            target=application.run,
            args=("127.0.0.1", self.port))
        self.thread.start()
        if widget_type == "hsec":
            self.window = wc.HSecWMSControlWidget(view=self.view, wms_cache=self.tempdir)
        else:
            initial_waypoints = [ft.Waypoint(40., 25., 0), ft.Waypoint(60., -10., 0), ft.Waypoint(40., 10, 0)]
            waypoints_model = ft.WaypointsTableModel("")
            waypoints_model.insertRows(0, rows=len(initial_waypoints), waypoints=initial_waypoints)
            self.window = wc.VSecWMSControlWidget(
                view=self.view, wms_cache=self.tempdir, waypoints_model=waypoints_model)
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(2000)
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtTest.QTest.mouseClick(self.window.cbCacheEnabled, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        shutil.rmtree(self.tempdir)
        self.thread.terminate()

    def query_server(self, url):
        while len(self.window.multilayers.cbWMS_URL.currentText()) > 0:
            QtTest.QTest.keyClick(self.window.multilayers.cbWMS_URL, QtCore.Qt.Key_Backspace)
            QtWidgets.QApplication.processEvents()
        QtTest.QTest.keyClicks(self.window.multilayers.cbWMS_URL, url)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(2000)  # time for the server to start up
        QtTest.QTest.mouseClick(self.window.multilayers.btGetCapabilities, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        wait_until_signal(self.window.cpdlg.canceled)


@pytest.mark.skipif(os.name == "nt",
                    reason="multiprocessing needs currently start_method fork")
class Test_HSecWMSControlWidget(WMSControlWidgetSetup):
    def setup(self):
        self._setup("hsec")

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_no_server(self, mockbox):
        """
        assert that a message box informs about server troubles
        """
        self.query_server("http://127.0.0.1:8882")
        assert mockbox.critical.call_count == 1

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_no_schema(self, mockbox):
        """
        assert that a message box informs about server troubles
        """
        self.query_server(f"127.0.0.1:{self.port}")
        assert mockbox.critical.call_count == 1

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_invalid_schema(self, mockbox):
        """
        assert that a message box informs about server troubles
        """
        self.query_server(f"hppd://127.0.0.1:{self.port}")
        assert mockbox.critical.call_count == 1

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_invalid_url(self, mockbox):
        """
        assert that a message box informs about server troubles
        """
        self.query_server(f"http://???127.0.0.1:{self.port}")
        assert mockbox.critical.call_count == 1

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_connection_error(self, mockbox):
        if sys.version_info.major == 3:
            pytest.skip("problem in urllib3")
        """
        assert that a message box informs about server troubles
        """
        self.query_server(f"http://.....127.0.0.1:{self.port}")
        assert mockbox.critical.call_count == 1

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_forward_backward_clicks(self, mockbox):
        self.query_server(f"http://127.0.0.1:{self.port}")
        self.window.init_time_back_click()
        self.window.init_time_fwd_click()
        self.window.valid_time_fwd_click()
        self.window.valid_time_back_click()
        self.window.level_fwd_click()
        self.window.level_back_click()
        self.window.cb_init_time_back_click()
        self.window.cb_valid_time_back_click()
        self.window.cb_init_time_fwd_click()
        self.window.cb_valid_time_fwd_click()
        try:
            self.window.secs_from_timestep("Wrong")
        except ValueError:
            pass
        assert mockbox.critical.call_count == 0

    def test_server_abort_getmap(self):
        """
        assert that an aborted getmap call does not change the displayed image
        """
        self.query_server(f"http://127.0.0.1:{self.port}")
        QtTest.QTest.mouseClick(self.window.btGetMap, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWait(20)
        QtTest.QTest.keyClick(self.window.pdlg, QtCore.Qt.Key_Enter)
        QtWidgets.QApplication.processEvents()
        wait_until_signal(self.window.image_displayed)

        assert self.view.draw_image.call_count == 0
        assert self.view.draw_legend.call_count == 0
        assert self.view.draw_metadata.call_count == 0
        self.view.reset_mock()

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_server_getmap(self, mockbox):
        """
        assert that a getmap call to a WMS server displays an image
        """
        self.query_server(f"http://127.0.0.1:{self.port}")

        QtTest.QTest.mouseClick(self.window.btGetMap, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        wait_until_signal(self.window.image_displayed)

        assert mockbox.critical.call_count == 0
        assert self.view.draw_image.call_count == 1
        assert self.view.draw_legend.call_count == 1
        assert self.view.draw_metadata.call_count == 1
        self.view.reset_mock()

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_server_getmap_cached(self, mockbox):
        """
        assert that a getmap call to a WMS server displays an image
        """
        self.query_server(f"http://127.0.0.1:{self.port}")

        QtTest.QTest.mouseClick(self.window.btGetMap, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        wait_until_signal(self.window.image_displayed)

        # assert mockbox.critical.call_count == 0

        assert self.view.draw_image.call_count == 1
        assert self.view.draw_legend.call_count == 1
        assert self.view.draw_metadata.call_count == 1
        self.view.reset_mock()

        QtTest.QTest.mouseClick(self.window.cbCacheEnabled, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.window.btGetMap, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        wait_until_signal(self.window.image_displayed)

        assert mockbox.critical.call_count == 0

        assert self.view.draw_image.call_count == 1
        assert self.view.draw_legend.call_count == 1
        assert self.view.draw_metadata.call_count == 1

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_server_service_cache(self, mockbox):
        """
        assert that changing between servers still allows image retrieval
        """
        self.query_server(f"http://127.0.0.1:{self.port}")
        assert mockbox.critical.call_count == 0

        QtTest.QTest.keyClick(self.window.multilayers.cbWMS_URL, QtCore.Qt.Key_Backspace)
        QtTest.QTest.keyClick(self.window.multilayers.cbWMS_URL, QtCore.Qt.Key_Backspace)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.window.multilayers.btGetCapabilities, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        wait_until_signal(self.window.cpdlg.canceled)
        assert mockbox.critical.call_count == 1
        assert self.view.draw_image.call_count == 0
        assert self.view.draw_legend.call_count == 0
        assert self.view.draw_metadata.call_count == 0
        mockbox.reset_mock()
        QtTest.QTest.keyClick(self.window.multilayers.cbWMS_URL, ord(str(self.port)[3]))
        QtTest.QTest.keyClick(self.window.multilayers.cbWMS_URL, QtCore.Qt.Key_Slash)
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.mouseClick(self.window.multilayers.btGetCapabilities, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        wait_until_signal(self.window.cpdlg.canceled)
        assert mockbox.critical.call_count == 0

        QtTest.QTest.mouseClick(self.window.btGetMap, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        wait_until_signal(self.window.image_displayed)

        assert mockbox.critical.call_count == 0
        assert self.view.draw_image.call_count == 1
        assert self.view.draw_legend.call_count == 1
        assert self.view.draw_metadata.call_count == 1

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_multilayer_handling(self, mockbox):
        """
        assert that multilayers get created, handled and drawn properly
        """
        self.query_server(f"http://127.0.0.1:{self.port}")
        server = self.window.multilayers.listLayers.findItems(f"http://127.0.0.1:{self.port}/",
                                                              QtCore.Qt.MatchFixedString)[0]
        self.window.cbAutoUpdate.setCheckState(False)
        assert server is not None
        assert "header" in self.window.multilayers.layers[f"http://127.0.0.1:{self.port}/"]
        assert "wms" in self.window.multilayers.layers[f"http://127.0.0.1:{self.port}/"]
        self.window.multilayers.cbMultilayering.setChecked(True)

        for i in range(0, server.childCount()):
            layer_widget = server.child(i)
            assert layer_widget.checkState(0) == 0

        # Check activating and deactivating layers, and changing priorities works
        server.setExpanded(True)
        server.child(0).setCheckState(0, QtCore.Qt.Checked)
        server.child(2).setCheckState(0, QtCore.Qt.Checked)
        self.window.multilayers.listLayers.itemWidget(server.child(0), 2).setCurrentIndex(1)
        self.window.multilayers.multilayer_clicked(server.child(1))
        assert self.window.lLayerName.text() != server.child(1).text(0)
        assert self.window.multilayers.get_current_layer().text(0) in self.window.lLayerName.text()
        assert self.window.multilayers.listLayers.itemWidget(server.child(0), 2) is not None
        assert self.window.multilayers.listLayers.itemWidget(server.child(2), 2) is not None
        assert self.window.multilayers.listLayers.itemWidget(server.child(0), 2).currentText() == "2"
        assert self.window.multilayers.listLayers.itemWidget(server.child(1), 2) is None
        server.child(2).setCheckState(0, QtCore.Qt.Unchecked)
        assert self.window.multilayers.listLayers.itemWidget(server.child(2), 2) is None
        assert self.window.multilayers.listLayers.itemWidget(server.child(0), 2).currentText() == "1"

        # Check drawing not causing errors
        QtTest.QTest.mouseClick(self.window.btGetMap, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        wait_until_signal(self.window.image_displayed)

        assert mockbox.critical.call_count == 0
        assert self.view.draw_image.call_count == 1
        assert self.view.draw_legend.call_count == 1
        assert self.view.draw_metadata.call_count == 1

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_filter_handling(self, mockbox):
        pytest.skip('Test fails in reverse order, see ToDo')
        self.query_server(f"http://127.0.0.1:{self.port}")
        server = self.window.multilayers.listLayers.findItems(f"http://127.0.0.1:{self.port}/",
                                                              QtCore.Qt.MatchFixedString)[0]
        self.window.cbAutoUpdate.setCheckState(False)
        assert server is not None
        assert "header" in self.window.multilayers.layers[f"http://127.0.0.1:{self.port}/"]
        assert "wms" in self.window.multilayers.layers[f"http://127.0.0.1:{self.port}/"]

        starts_at = 40 * self.window.multilayers.scale
        icon_start_fav = starts_at + 3
        if self.window.multilayers.cbMultilayering.isChecked():
            checkbox_width = round(self.window.multilayers.height * 0.75)
            icon_start_fav += checkbox_width + 6

        starts_at = 20 * self.window.multilayers.scale
        icon_start_del = starts_at + 3

        # Check layer filter is working
        server.child(0).is_favourite = False
        self.window.multilayers.leMultiFilter.setText("No matches")
        assert server.isHidden()
        self.window.multilayers.remove_filter_triggered()
        assert not server.isHidden()
        self.window.multilayers.filter_favourite_toggled()
        assert server.isHidden()
        self.window.multilayers.filter_favourite_toggled()
        QtTest.QTest.qWait(100)
        QtTest.QTest.mouseMove(self.window.multilayers.listLayers, QtCore.QPoint(icon_start_fav + 3, 0), -1)
        QtWidgets.QApplication.processEvents()
        self.window.multilayers.check_icon_clicked(server.child(0))
        self.window.multilayers.filter_favourite_toggled()
        # ToDo The next assert fails in reverse test order
        assert not server.isHidden()
        server.child(0).favourite_triggered()
        self.window.multilayers.remove_filter_triggered()

        # Check deleting server is working
        QtTest.QTest.mouseMove(self.window.multilayers.listLayers, QtCore.QPoint(icon_start_del + 3, 0), -1)
        QtWidgets.QApplication.processEvents()
        self.window.multilayers.check_icon_clicked(server)
        assert len(self.window.multilayers.listLayers.findItems(f"http://127.0.0.1:{self.port}/",
                                                                QtCore.Qt.MatchFixedString)) == 0
        assert mockbox.critical.call_count == 0

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_singlelayer_handling(self, mockbox):
        """
        assert that singlelayer mode behaves as expected
        """
        self.query_server(f"http://127.0.0.1:{self.port}")
        server = self.window.multilayers.listLayers.findItems(f"http://127.0.0.1:{self.port}/",
                                                              QtCore.Qt.MatchFixedString)[0]
        self.window.cbAutoUpdate.setCheckState(False)
        assert server is not None
        assert "header" in self.window.multilayers.layers[f"http://127.0.0.1:{self.port}/"]
        assert "wms" in self.window.multilayers.layers[f"http://127.0.0.1:{self.port}/"]

        self.window.multilayers.cbMultilayering.setChecked(True)
        self.window.multilayers.cbMultilayering.setChecked(False)
        # Check using singlelayer mode contains no checkboxes
        for i in range(0, server.childCount()):
            layer = server.child(i)
            assert layer.data(0, QtCore.Qt.CheckStateRole) is None or not layer.data(0,
                                                                                     QtCore.Qt.CheckStateRole).isValid()

        # Check clicking on layers updates the UI
        self.window.multilayers.multilayer_clicked(server.child(0))
        assert self.window.lLayerName.text().endswith(server.child(0).text(0))
        self.window.multilayers.multilayer_clicked(server.child(1))
        assert self.window.lLayerName.text().endswith(server.child(1).text(0))

        # Check drawing not causing errors
        QtTest.QTest.mouseClick(self.window.btGetMap, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        wait_until_signal(self.window.image_displayed)

        assert mockbox.critical.call_count == 0
        assert self.view.draw_image.call_count == 1
        assert self.view.draw_legend.call_count == 1
        assert self.view.draw_metadata.call_count == 1

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_multilayer_syncing(self, mockbox):
        """
        assert that synced layers share their options
        """
        self.query_server(f"http://127.0.0.1:{self.port}")
        server = self.window.multilayers.listLayers.findItems(f"http://127.0.0.1:{self.port}/",
                                                              QtCore.Qt.MatchFixedString)[0]
        self.window.cbAutoUpdate.setCheckState(False)
        server.setExpanded(True)
        self.window.multilayers.cbMultilayering.setChecked(True)
        layer_a = server.child(0)
        layer_b = server.child(1)

        # Check synced layers have the same options
        layer_a.setCheckState(0, 2)
        layer_b.setCheckState(0, 2)
        self.window.multilayers.multilayer_clicked(layer_a)
        assert layer_a.get_levels() == layer_b.get_levels()
        assert layer_a.get_itimes() == layer_b.get_itimes()
        assert layer_a.get_vtimes() == layer_b.get_vtimes()

        # Check synced layers are both set to the same option upon change
        self.window.cbLevel.setCurrentIndex(1)
        assert layer_a.get_level() == self.window.cbLevel.currentText()
        self.window.cbValidTime.setCurrentIndex(1)
        assert layer_a.get_vtime() == self.window.cbValidTime.currentText()
        assert layer_a.get_level() == layer_b.get_level()
        assert layer_a.get_vtime() == layer_b.get_vtime()
        assert layer_a.get_itime() == layer_a.get_itimes()[-1]
        assert mockbox.critical.call_count == 0

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    @mock.patch("mslib.msui.wms_control.WMSMapFetcher.moveToThread")
    def test_server_no_thread(self, mockbox, mockthread):
        self.query_server(f"http://127.0.0.1:{self.port}")
        server = self.window.multilayers.listLayers.findItems(f"http://127.0.0.1:{self.port}/",
                                                              QtCore.Qt.MatchFixedString)[0]
        self.window.cbAutoUpdate.setCheckState(False)
        server.setExpanded(True)
        self.window.multilayers.cbMultilayering.setChecked(True)
        server.child(0).setCheckState(0, 2)
        server.child(1).setCheckState(0, 2)

        QtTest.QTest.mouseClick(self.window.btGetMap, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        wait_until_signal(self.window.image_displayed)

        urlstr = f"http://127.0.0.1:{self.port}/mss/logo.png"
        md5_filname = os.path.join(self.window.wms_cache, hashlib.md5(urlstr.encode('utf-8')).hexdigest() + ".png")
        self.window.fetcher.fetch_legend(urlstr, use_cache=False, md5_filename=md5_filname)
        self.window.fetcher.fetch_legend(urlstr, use_cache=True, md5_filename=md5_filname)

        assert mockbox.critical.call_count == 0
        assert self.view.draw_image.call_count == 1
        assert self.view.draw_legend.call_count == 1
        assert self.view.draw_metadata.call_count == 1

    def test_preload(self):
        assert f"http://127.0.0.1:{self.port}/" not in wc.WMS_SERVICE_CACHE
        MSSMainWindow.preload_wms([f"http://127.0.0.1:{self.port}/"])
        assert f"http://127.0.0.1:{self.port}/" in wc.WMS_SERVICE_CACHE


@pytest.mark.skipif(os.name == "nt",
                    reason="multiprocessing needs currently start_method fork")
class Test_VSecWMSControlWidget(WMSControlWidgetSetup):
    def setup(self):
        self._setup("vsec")

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_server_getmap(self, mockbox):
        pytest.skip("unknown problem")
        """
        assert that a getmap call to a WMS server displays an image
        """
        self.query_server(f"http://127.0.0.1:{self.port}")
        QtTest.QTest.mouseClick(self.window.btGetMap, QtCore.Qt.LeftButton)
        QtWidgets.QApplication.processEvents()
        wait_until_signal(self.window.image_displayed)

        assert mockbox.critical.call_count == 0
        assert self.view.draw_image.call_count == 1
        assert self.view.draw_legend.call_count == 1
        assert self.view.draw_metadata.call_count == 1
        self.view.reset_mock()

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_multilayer_drawing(self, mockbox):
        """
        assert that drawing a layer through code doesn't fail for vsec
        """
        self.query_server(f"http://127.0.0.1:{self.port}")
        server = self.window.multilayers.listLayers.findItems(f"http://127.0.0.1:{self.port}/",
                                                              QtCore.Qt.MatchFixedString)[0]
        server.child(0).draw()
        wait_until_signal(self.window.image_displayed)

        assert mockbox.critical.call_count == 0


class TestWMSControlWidgetSetupSimple(object):
    xml = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <!DOCTYPE WMT_MS_Capabilities SYSTEM "http://schemas.opengis.net/wms/1.1.1/capabilities_1_1_1.dtd">
        <WMT_MS_Capabilities version="1.1.1" updateSequence="0">
            <Service>
            <Name>OGC:WMS</Name>
            <Title>Mission Support System Web Map Service</Title>
            <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="http://localhost:8081/"/>
            </Service>
            <Capability>
                <Request>
                    <GetCapabilities>
                    <Format>application/vnd.ogc.wms_xml</Format>
                    <DCPType> <HTTP> <Get>
                        <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="http://localhost/?"/>
                    </Get> </HTTP> </DCPType>
                    </GetCapabilities>
                    <GetMap>
                    <Format>image/png</Format>
                    <DCPType> <HTTP> <Get>
                        <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="http://localhost/?"/>
                    </Get> </HTTP> </DCPType>
                    </GetMap>
                </Request>
                <Exception>
                    <Format>application/vnd.ogc.se_xml</Format>
                </Exception>
                <Layer>
                    <Title>Mission Support WMS Server</Title>
                    <Abstract>Mission Support WMS Server</Abstract>
                    {}
                    <Layer>
                        <Name>ecmwf_EUR_LL015.PLTemp01</Name>
                        <Title> Temperature (degC) and Geopotential Height (m) </Title>
                        {}
                        <LatLonBoundingBox minx="-180" maxx="180" miny="-90" maxy="90"></LatLonBoundingBox>
                        {}
                    </Layer>
                </Layer>
            </Capability>
        </WMT_MS_Capabilities>
    """

    srs_base = "<SRS> CRS:84 </SRS> <SRS> EPSG:3031 </SRS> <SRS> MSS:stere </SRS>"

    dimext_time = """
        <Dimension name="TIME" units="ISO8610"> </Dimension>
        <Extent name="TIME"> 2012-10-17T12:00:00Z,2012-10-17T18:00:00Z,2012-10-18T00:00:00Z </Extent>"""

    dimext_inittime = """
        <Dimension name="INIT_TIME" units="ISO8610"> </Dimension>
        <Extent name="INIT_TIME"> 2012-10-16T12:00:00Z,2012-10-17T12:00:00Z </Extent>"""

    dimext_elevation = """
        <Dimension name="ELEVATION" units="hPa"> </Dimension>
        <Extent name="ELEVATION" default="900.0"> 500.0,600.0,700.0,900.0 </Extent>"""

    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)
        self.view = HSecViewMockup()
        self.window = wc.HSecWMSControlWidget(view=self.view)
        self.window.show()
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    def test_xml(self):
        testxml = self.xml.format("", self.srs_base, self.dimext_time + self.dimext_inittime + self.dimext_elevation)
        self.window.activate_wms(wc.MSSWebMapService(None, version='1.1.1', xml=testxml))
        QtWidgets.QApplication.processEvents()
        assert [self.window.cbValidTime.itemText(i) for i in range(self.window.cbValidTime.count())] == \
            ['2012-10-17T12:00:00Z', '2012-10-17T18:00:00Z', '2012-10-18T00:00:00Z']
        assert [self.window.cbInitTime.itemText(i) for i in range(self.window.cbInitTime.count())] == \
            ['2012-10-16T12:00:00Z', '2012-10-17T12:00:00Z']
        assert [self.window.cbLevel.itemText(i) for i in range(self.window.cbLevel.count())] == \
            ['500.0 (hPa)', '600.0 (hPa)', '700.0 (hPa)', '900.0 (hPa)']
        assert self.window.cbLevel.isEnabled()
        assert self.window.cbValidTime.isEnabled()
        assert self.window.cbInitTime.isEnabled()

    def test_xml_currenttag(self):
        dimext_time = """
            <Dimension name="TIME" units="ISO8610"> </Dimension>
            <Extent name="TIME"> 2014-10-17T12:00:00Z/current/P1Y </Extent>"""
        testxml = self.xml.format("", self.srs_base, dimext_time + self.dimext_inittime + self.dimext_elevation)
        self.window.activate_wms(wc.MSSWebMapService(None, version='1.1.1', xml=testxml))
        QtWidgets.QApplication.processEvents()
        print([self.window.cbValidTime.itemText(i) for i in range(self.window.cbValidTime.count())])
        assert [self.window.cbValidTime.itemText(i) for i in range(self.window.cbValidTime.count())][:4] == \
            ['2014-10-17T12:00:00Z', '2015-10-17T12:00:00Z', '2016-10-17T12:00:00Z', '2017-10-17T12:00:00Z']
        assert [self.window.cbInitTime.itemText(i) for i in range(self.window.cbInitTime.count())] == \
            ['2012-10-16T12:00:00Z', '2012-10-17T12:00:00Z']
        assert [self.window.cbLevel.itemText(i) for i in range(self.window.cbLevel.count())] == \
            ['500.0 (hPa)', '600.0 (hPa)', '700.0 (hPa)', '900.0 (hPa)']
        assert self.window.cbLevel.isEnabled()
        assert self.window.cbValidTime.isEnabled()
        assert self.window.cbInitTime.isEnabled()

    def test_xml_emptyextent(self):
        dimext_time_empty = """<Dimension name="TIME" units="ISO8610"> </Dimension> <Extent name="TIME"> </Extent>"""
        testxml = self.xml.format(
            "", self.srs_base, dimext_time_empty + self.dimext_inittime + self.dimext_elevation)
        self.window.activate_wms(wc.MSSWebMapService(None, version='1.1.1', xml=testxml))
        QtWidgets.QApplication.processEvents()
        assert [self.window.cbValidTime.itemText(i) for i in range(self.window.cbValidTime.count())] == []
        assert [self.window.cbInitTime.itemText(i) for i in range(self.window.cbInitTime.count())] == []
        assert [self.window.cbLevel.itemText(i) for i in range(self.window.cbLevel.count())] == []
        assert not self.window.cbLevel.isEnabled()
        assert not self.window.cbValidTime.isEnabled()
        assert not self.window.cbInitTime.isEnabled()

    def test_xml_onlytimedim(self):
        dimext_time_noext = '<Dimension name="TIME" units="ISO8610"> </Dimension>'

        testxml = self.xml.format("", self.srs_base, dimext_time_noext + self.dimext_inittime + self.dimext_elevation)
        self.window.activate_wms(wc.MSSWebMapService(None, version='1.1.1', xml=testxml))
        QtWidgets.QApplication.processEvents()
        assert [self.window.cbValidTime.itemText(i) for i in range(self.window.cbValidTime.count())] == []
        assert not self.window.cbValidTime.isEnabled()
        assert [self.window.cbInitTime.itemText(i) for i in range(self.window.cbInitTime.count())] == \
            ['2012-10-16T12:00:00Z', '2012-10-17T12:00:00Z']
        assert [self.window.cbLevel.itemText(i) for i in range(self.window.cbLevel.count())] == \
            ['500.0 (hPa)', '600.0 (hPa)', '700.0 (hPa)', '900.0 (hPa)']

    def test_xml_separatedim(self):
        dimext_time_dim = '<Dimension name="TIME" units="ISO8610"> </Dimension>'
        dimext_time_ext = \
            '<Extent name="TIME"> 2012-10-17T12:00:00Z,2012-10-17T18:00:00Z,2012-10-18T00:00:00Z </Extent>'
        testxml = self.xml.format(
            dimext_time_dim, self.srs_base, dimext_time_ext + self.dimext_inittime + self.dimext_elevation)
        self.window.activate_wms(wc.MSSWebMapService(None, version='1.1.1', xml=testxml))
        QtWidgets.QApplication.processEvents()
        assert [self.window.cbValidTime.itemText(i) for i in range(self.window.cbValidTime.count())] == \
            ['2012-10-17T12:00:00Z', '2012-10-17T18:00:00Z', '2012-10-18T00:00:00Z']
        assert [self.window.cbInitTime.itemText(i) for i in range(self.window.cbInitTime.count())] == \
            ['2012-10-16T12:00:00Z', '2012-10-17T12:00:00Z']
        assert [self.window.cbLevel.itemText(i) for i in range(self.window.cbLevel.count())] == \
            ['500.0 (hPa)', '600.0 (hPa)', '700.0 (hPa)', '900.0 (hPa)']

    def test_xml_separate_leafs(self):
        testxml = self.xml.format(
            self.dimext_inittime, self.srs_base, self.dimext_time + self.dimext_elevation)
        self.window.activate_wms(wc.MSSWebMapService(None, version='1.1.1', xml=testxml))
        QtWidgets.QApplication.processEvents()
        assert [self.window.cbValidTime.itemText(i) for i in range(self.window.cbValidTime.count())] == \
            ['2012-10-17T12:00:00Z', '2012-10-17T18:00:00Z', '2012-10-18T00:00:00Z']
        assert [self.window.cbInitTime.itemText(i) for i in range(self.window.cbInitTime.count())] == \
            ['2012-10-16T12:00:00Z', '2012-10-17T12:00:00Z']

    def test_xml_time_forecast(self):
        dimext_time_forecast = """
            <Dimension name="FORECAST" units="ISO8610"> </Dimension>
            <Extent name="FORECAST"> 2013-10-17T12:00:00Z,2013-10-17T18:00:00Z,2013-10-18T00:00:00Z </Extent>"""
        testxml = self.xml.format(
            "", self.srs_base, dimext_time_forecast + self.dimext_inittime + self.dimext_elevation)
        self.window.activate_wms(wc.MSSWebMapService(None, version='1.1.1', xml=testxml))
        QtWidgets.QApplication.processEvents()
        assert [self.window.cbValidTime.itemText(i) for i in range(self.window.cbValidTime.count())] == \
            ['2013-10-17T12:00:00Z', '2013-10-17T18:00:00Z', '2013-10-18T00:00:00Z']
        assert [self.window.cbInitTime.itemText(i) for i in range(self.window.cbInitTime.count())] == \
            ['2012-10-16T12:00:00Z', '2012-10-17T12:00:00Z']
        assert [self.window.cbLevel.itemText(i) for i in range(self.window.cbLevel.count())] == \
            ['500.0 (hPa)', '600.0 (hPa)', '700.0 (hPa)', '900.0 (hPa)']

    def test_xml_inittime_reference(self):
        dimext_inittime_reference = """
            <Dimension name="REFERENCE_TIME" units="ISO8610"> </Dimension>
            <Extent name="REFERENCE_TIME"> 2013-10-16T12:00:00Z,2013-10-17T12:00:00Z </Extent>"""
        testxml = self.xml.format(
            "", self.srs_base, self.dimext_time + dimext_inittime_reference + self.dimext_elevation)
        self.window.activate_wms(wc.MSSWebMapService(None, version='1.1.1', xml=testxml))
        QtWidgets.QApplication.processEvents()
        assert [self.window.cbValidTime.itemText(i) for i in range(self.window.cbValidTime.count())] == \
            ['2012-10-17T12:00:00Z', '2012-10-17T18:00:00Z', '2012-10-18T00:00:00Z']
        assert [self.window.cbInitTime.itemText(i) for i in range(self.window.cbInitTime.count())] == \
            ['2013-10-16T12:00:00Z', '2013-10-17T12:00:00Z']
        assert [self.window.cbLevel.itemText(i) for i in range(self.window.cbLevel.count())] == \
            ['500.0 (hPa)', '600.0 (hPa)', '700.0 (hPa)', '900.0 (hPa)']

    def test_xml_no_elevation(self):
        testxml = self.xml.format("", self.srs_base, self.dimext_time + self.dimext_inittime)
        self.window.activate_wms(wc.MSSWebMapService(None, version='1.1.1', xml=testxml))
        QtWidgets.QApplication.processEvents()
        assert [self.window.cbValidTime.itemText(i) for i in range(self.window.cbValidTime.count())] == \
            ['2012-10-17T12:00:00Z', '2012-10-17T18:00:00Z', '2012-10-18T00:00:00Z']
        assert [self.window.cbInitTime.itemText(i) for i in range(self.window.cbInitTime.count())] == \
            ['2012-10-16T12:00:00Z', '2012-10-17T12:00:00Z']
        assert [self.window.cbLevel.itemText(i) for i in range(self.window.cbLevel.count())] == []
        assert not self.window.cbLevel.isEnabled()

    def test_xml_no_validtime(self):
        testxml = self.xml.format("", self.srs_base, self.dimext_inittime + self.dimext_elevation)
        self.window.activate_wms(wc.MSSWebMapService(None, version='1.1.1', xml=testxml))
        QtWidgets.QApplication.processEvents()
        assert [self.window.cbValidTime.itemText(i) for i in range(self.window.cbValidTime.count())] == []
        assert not self.window.cbValidTime.isEnabled()
        assert [self.window.cbInitTime.itemText(i) for i in range(self.window.cbInitTime.count())] == \
            ['2012-10-16T12:00:00Z', '2012-10-17T12:00:00Z']
        assert [self.window.cbLevel.itemText(i) for i in range(self.window.cbLevel.count())] == \
            ['500.0 (hPa)', '600.0 (hPa)', '700.0 (hPa)', '900.0 (hPa)']

    def test_xml_no_inittime(self):
        testxml = self.xml.format(
            "", self.srs_base, self.dimext_time + self.dimext_elevation)
        self.window.activate_wms(wc.MSSWebMapService(None, version='1.1.1', xml=testxml))
        QtWidgets.QApplication.processEvents()
        assert [self.window.cbValidTime.itemText(i) for i in range(self.window.cbValidTime.count())] == \
            ['2012-10-17T12:00:00Z', '2012-10-17T18:00:00Z', '2012-10-18T00:00:00Z']
        assert [self.window.cbInitTime.itemText(i) for i in range(self.window.cbInitTime.count())] == []
        assert not self.window.cbInitTime.isEnabled()
        assert [self.window.cbLevel.itemText(i) for i in range(self.window.cbLevel.count())] == \
            ['500.0 (hPa)', '600.0 (hPa)', '700.0 (hPa)', '900.0 (hPa)']

    def test_xml_time_period(self):
        dimext_time_period = """
            <Dimension name="TIME" units="ISO8610"> </Dimension>
            <Extent name="TIME"> 2012-10-17T12:00:00Z/2012-10-18T00:00:00Z/PT6H </Extent>"""
        testxml = self.xml.format(
            "", self.srs_base, dimext_time_period + self.dimext_inittime + self.dimext_elevation)
        self.window.activate_wms(wc.MSSWebMapService(None, version='1.1.1', xml=testxml))
        QtWidgets.QApplication.processEvents()
        assert [self.window.cbValidTime.itemText(i) for i in range(self.window.cbValidTime.count())] == \
            ['2012-10-17T12:00:00Z', '2012-10-17T18:00:00Z', '2012-10-18T00:00:00Z']
        assert [self.window.cbInitTime.itemText(i) for i in range(self.window.cbInitTime.count())] == \
            ['2012-10-16T12:00:00Z', '2012-10-17T12:00:00Z']

    def test_xml_time_multiperiod(self):
        dimext_time_period = '<Dimension name="TIME" units="ISO8610"> </Dimension> ' \
            '<Extent name="TIME"> 2010-10-17T12:00:00Z/2010-11-18T00:00:00Z/P1M, ' \
            '2012-10-01T12:00:00Z,2012-10-17T12:00:00Z/2012-10-18T00:00:00Z/PT12H </Extent>'
        dimext_inittime = """
                <Dimension name="INIT_TIME" units="ISO8610"> </Dimension>
                <Extent name="INIT_TIME"> 2010-10-17T12:00:00Z,2012-10-16T12:00:00Z,2012-10-17T12:00:00Z </Extent>"""

        testxml = self.xml.format(
            "", self.srs_base, dimext_time_period + dimext_inittime + self.dimext_elevation)
        self.window.activate_wms(wc.MSSWebMapService(None, version='1.1.1', xml=testxml))
        QtWidgets.QApplication.processEvents()
        self.window.cbAutoUpdate.setCheckState(False)
        self.window.cbInitTime.setCurrentIndex(0)
        assert [self.window.cbValidTime.itemText(i) for i in range(self.window.cbValidTime.count())] == \
            ['2010-10-17T12:00:00Z', '2010-11-17T12:00:00Z',
             '2012-10-01T12:00:00Z',
             '2012-10-17T12:00:00Z', '2012-10-18T00:00:00Z']
        assert [self.window.cbInitTime.itemText(i) for i in range(self.window.cbInitTime.count())] == \
            ['2010-10-17T12:00:00Z', '2012-10-16T12:00:00Z', '2012-10-17T12:00:00Z']

    def test_valid_before_init(self):
        dimext_time_period = '<Dimension name="TIME" units="ISO8610"> </Dimension> ' \
            '<Extent name="TIME"> 2010-10-17T12:00:00Z,2012-10-17T12:00:00Z </Extent>' \

        testxml = self.xml.format(
            "", self.srs_base, dimext_time_period + self.dimext_inittime + self.dimext_elevation)
        self.window.activate_wms(wc.MSSWebMapService(None, version='1.1.1', xml=testxml))
        QtWidgets.QApplication.processEvents()
        assert [self.window.cbValidTime.itemText(i) for i in range(self.window.cbValidTime.count())] == \
            ['2012-10-17T12:00:00Z']
        assert [self.window.cbInitTime.itemText(i) for i in range(self.window.cbInitTime.count())] == \
            ['2012-10-16T12:00:00Z', '2012-10-17T12:00:00Z']

    def test_xml_time_init_period(self):
        dimext_inittime_period = """
            <Dimension name="INIT_TIME" units="ISO8610"> </Dimension>
            <Extent name="INIT_TIME"> 2012-10-17T12:00:00Z/2012-10-24T12:00:00Z/P1W </Extent>"""
        testxml = self.xml.format(
            "", self.srs_base, self.dimext_time + dimext_inittime_period + self.dimext_elevation)
        self.window.activate_wms(wc.MSSWebMapService(None, version='1.1.1', xml=testxml))
        QtWidgets.QApplication.processEvents()
        assert [self.window.cbValidTime.itemText(i) for i in range(self.window.cbValidTime.count())] == \
            ['2012-10-17T12:00:00Z', '2012-10-17T18:00:00Z', '2012-10-18T00:00:00Z']
        assert [self.window.cbInitTime.itemText(i) for i in range(self.window.cbInitTime.count())] == \
            ['2012-10-17T12:00:00Z', '2012-10-24T12:00:00Z']
        assert [self.window.cbLevel.itemText(i) for i in range(self.window.cbLevel.count())] == \
            ['500.0 (hPa)', '600.0 (hPa)', '700.0 (hPa)', '900.0 (hPa)']

    def test_xml_othertimeformat(self):
        dimext_time_format = """
            <Dimension name="TIME" units="ISO8610"> </Dimension>
            <Extent name="TIME"> 2012-10-17,2012-10-18,2012-10-19 </Extent>"""
        testxml = self.xml.format(
            "", self.srs_base, dimext_time_format + self.dimext_inittime + self.dimext_elevation)
        self.window.activate_wms(wc.MSSWebMapService(None, version='1.1.1', xml=testxml))
        QtWidgets.QApplication.processEvents()
        self.window.cbAutoUpdate.setCheckState(False)
        self.window.cbInitTime.setCurrentIndex(0)
        assert [self.window.cbValidTime.itemText(i) for i in range(self.window.cbValidTime.count())] == \
            ['2012-10-17T00:00:00Z', '2012-10-18T00:00:00Z', '2012-10-19T00:00:00Z']
        assert [self.window.cbInitTime.itemText(i) for i in range(self.window.cbInitTime.count())] == \
            ['2012-10-16T12:00:00Z', '2012-10-17T12:00:00Z']

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_xml_time_error(self, mockbox):
        dimext_time_error = """
            <Dimension name="TIME" units="ISO8610"> </Dimension>
            <Extent name="TIME"> a2012-10-17T12:00:00Z/2012-10-18T00:00:00Z/PT6H </Extent>"""
        testxml = self.xml.format(
            "", self.srs_base, dimext_time_error + self.dimext_inittime + self.dimext_elevation)
        self.window.activate_wms(wc.MSSWebMapService(None, version='1.1.1', xml=testxml))
        QtWidgets.QApplication.processEvents()
        assert [self.window.cbValidTime.itemText(i) for i in range(self.window.cbValidTime.count())] == []
        assert [self.window.cbInitTime.itemText(i) for i in range(self.window.cbInitTime.count())] == []
