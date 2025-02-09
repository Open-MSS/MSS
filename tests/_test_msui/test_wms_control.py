# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_wms_control
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.wms_control

    This file is part of MSS.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017-2024 by the MSS team, see AUTHORS.
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
import shutil
import tempfile
import pytest
import hashlib
import urllib
from PyQt5 import QtCore, QtTest
from mslib.msui import flighttrack as ft
import mslib.msui.wms_control as wc


class HSecViewMockup(mock.Mock):
    get_crs = mock.Mock(return_value="EPSG:4326")
    getBBOX = mock.Mock(return_value=(0, 0, 10, 10))
    get_plot_size_in_px = mock.Mock(return_value=(200, 100))


class VSecViewMockup(mock.Mock):
    get_crs = mock.Mock(return_value="VERT:LOGP")
    getBBOX = mock.Mock(return_value=(3, 500, 3, 10))
    get_plot_size_in_px = mock.Mock(return_value=(200, 100))


class WMSControlWidgetSetup:
    @pytest.fixture(autouse=True)
    def _with_mswms_server(self, mswms_server):
        self.url = mswms_server
        parsed_url = urllib.parse.urlparse(self.url)
        self.scheme, self.host, self.port = parsed_url.scheme, parsed_url.hostname, parsed_url.port

    def _setup(self, widget_type):
        wc.WMS_SERVICE_CACHE = {}
        if widget_type == "hsec":
            self.view = HSecViewMockup()
        else:
            self.view = VSecViewMockup()
        self.tempdir = tempfile.mkdtemp()
        if not os.path.exists(self.tempdir):
            os.mkdir(self.tempdir)
        if widget_type == "hsec":
            self.window = wc.HSecWMSControlWidget(view=self.view, wms_cache=self.tempdir)
        else:
            initial_waypoints = [ft.Waypoint(40., 25., 0), ft.Waypoint(60., -10., 0), ft.Waypoint(40., 10, 0)]
            waypoints_model = ft.WaypointsTableModel("")
            waypoints_model.insertRows(0, rows=len(initial_waypoints), waypoints=initial_waypoints)
            self.window = wc.VSecWMSControlWidget(
                view=self.view, wms_cache=self.tempdir, waypoints_model=waypoints_model)
        self.window.show()

        # Remove all previous cached URLs
        for url in self.window.multilayers.layers.copy():
            server = self.window.multilayers.listLayers.findItems(url, QtCore.Qt.MatchFixedString)[0]
            self.window.multilayers.delete_server(server)

        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtTest.QTest.mouseClick(self.window.cbCacheEnabled, QtCore.Qt.LeftButton)

    def _teardown(self):
        self.window.hide()
        shutil.rmtree(self.tempdir)

    def query_server(self, qtbot, url):
        while len(self.window.multilayers.cbWMS_URL.currentText()) > 0:
            QtTest.QTest.keyClick(self.window.multilayers.cbWMS_URL, QtCore.Qt.Key_Backspace)
        QtTest.QTest.keyClicks(self.window.multilayers.cbWMS_URL, url)
        with qtbot.wait_signal(self.window.cpdlg.canceled):
            QtTest.QTest.mouseClick(self.window.multilayers.btGetCapabilities, QtCore.Qt.LeftButton)


class Test_HSecWMSControlWidget(WMSControlWidgetSetup):
    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        self._setup("hsec")
        yield
        self._teardown()

    def test_no_server(self, qtbot):
        """
        assert that a message box informs about server troubles
        """
        with mock.patch("PyQt5.QtWidgets.QMessageBox.critical") as mock_critical:
            self.query_server(qtbot, f"{self.scheme}://{self.host}:{self.port - 1}")
            mock_critical.assert_called_once()

    def test_no_schema(self, qtbot):
        """
        assert that a message box informs about server troubles
        """
        with mock.patch("PyQt5.QtWidgets.QMessageBox.critical") as mock_critical:
            self.query_server(qtbot, f"{self.host}:{self.port}")
            mock_critical.assert_called_once()

    def test_invalid_schema(self, qtbot):
        """
        assert that a message box informs about server troubles
        """
        with mock.patch("PyQt5.QtWidgets.QMessageBox.critical") as mock_critical:
            self.query_server(qtbot, f"hppd://{self.host}:{self.port}")
            mock_critical.assert_called_once()

    def test_invalid_url(self, qtbot):
        """
        assert that a message box informs about server troubles
        """
        with mock.patch("PyQt5.QtWidgets.QMessageBox.critical") as mock_critical:
            self.query_server(qtbot, f"{self.scheme}://???{self.host}:{self.port}")
            mock_critical.assert_called_once()

    def test_connection_error(self, qtbot):
        """
        assert that a message box informs about server troubles
        """
        with mock.patch("PyQt5.QtWidgets.QMessageBox.critical") as mock_critical:
            self.query_server(qtbot, f"{self.scheme}://.....{self.host}:{self.port}")
            mock_critical.assert_called_once()

    @pytest.mark.skip("Breaks other tests in this class because of a lingering message box, for some reason")
    def test_forward_backward_clicks(self, qtbot):
        self.query_server(qtbot, self.url)
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

    @pytest.mark.skip("Has a race condition where the abort might not happen fast enough")
    def test_server_abort_getmap(self, qtbot):
        """
        assert that an aborted getmap call does not change the displayed image
        """
        self.query_server(qtbot, self.url)
        with qtbot.wait_signal(self.window.image_displayed):
            QtTest.QTest.mouseClick(self.window.btGetMap, QtCore.Qt.LeftButton)
            QtTest.QTest.keyClick(self.window.pdlg, QtCore.Qt.Key_Enter)
        assert self.view.draw_image.call_count == 0
        assert self.view.draw_legend.call_count == 0
        assert self.view.draw_metadata.call_count == 0
        self.view.reset_mock()

    def test_server_getmap(self, qtbot):
        """
        assert that a getmap call to a WMS server displays an image
        """
        self.query_server(qtbot, self.url)

        with qtbot.wait_signal(self.window.image_displayed):
            QtTest.QTest.mouseClick(self.window.btGetMap, QtCore.Qt.LeftButton)

        assert self.view.draw_image.call_count == 1
        assert self.view.draw_legend.call_count == 1
        assert self.view.draw_metadata.call_count == 1

    def test_server_getmap_cached(self, qtbot):
        """
        assert that a getmap call to a WMS server displays an image
        """
        self.query_server(qtbot, self.url)

        with qtbot.wait_signal(self.window.image_displayed):
            QtTest.QTest.mouseClick(self.window.btGetMap, QtCore.Qt.LeftButton)

        assert self.view.draw_image.call_count == 1
        assert self.view.draw_legend.call_count == 1
        assert self.view.draw_metadata.call_count == 1
        self.view.reset_mock()

        QtTest.QTest.mouseClick(self.window.cbCacheEnabled, QtCore.Qt.LeftButton)
        with qtbot.wait_signal(self.window.image_displayed):
            QtTest.QTest.mouseClick(self.window.btGetMap, QtCore.Qt.LeftButton)

        assert self.view.draw_image.call_count == 1
        assert self.view.draw_legend.call_count == 1
        assert self.view.draw_metadata.call_count == 1

    def test_server_service_cache(self, qtbot):
        """
        assert that changing between servers still allows image retrieval
        """
        self.query_server(qtbot, self.url)

        with mock.patch("PyQt5.QtWidgets.QMessageBox.critical") as qm_critical:
            with qtbot.wait_signal(self.window.cpdlg.canceled):
                QtTest.QTest.keyClick(self.window.multilayers.cbWMS_URL, QtCore.Qt.Key_Backspace)
                QtTest.QTest.keyClick(self.window.multilayers.cbWMS_URL, QtCore.Qt.Key_Backspace)
                QtTest.QTest.mouseClick(self.window.multilayers.btGetCapabilities, QtCore.Qt.LeftButton)
            qm_critical.assert_called_once()
        assert self.view.draw_image.call_count == 0
        assert self.view.draw_legend.call_count == 0
        assert self.view.draw_metadata.call_count == 0

        with qtbot.wait_signal(self.window.cpdlg.canceled):
            QtTest.QTest.keyClick(self.window.multilayers.cbWMS_URL, ord(str(self.port)[-1]))
            QtTest.QTest.keyClick(self.window.multilayers.cbWMS_URL, QtCore.Qt.Key_Slash)
            QtTest.QTest.mouseClick(self.window.multilayers.btGetCapabilities, QtCore.Qt.LeftButton)

        with qtbot.wait_signal(self.window.image_displayed):
            QtTest.QTest.mouseClick(self.window.btGetMap, QtCore.Qt.LeftButton)

        assert self.view.draw_image.call_count == 1
        assert self.view.draw_legend.call_count == 1
        assert self.view.draw_metadata.call_count == 1

    def test_multilayer_handling(self, qtbot):
        """
        assert that multilayers get created, handled and drawn properly
        """
        self.query_server(qtbot, self.url)
        server = self.window.multilayers.listLayers.findItems(f"{self.url}/",
                                                              QtCore.Qt.MatchFixedString)[0]
        self.window.cbAutoUpdate.setCheckState(False)
        assert server is not None
        assert "header" in self.window.multilayers.layers[f"{self.url}/"]
        assert "wms" in self.window.multilayers.layers[f"{self.url}/"]
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
        with qtbot.wait_signal(self.window.image_displayed):
            QtTest.QTest.mouseClick(self.window.btGetMap, QtCore.Qt.LeftButton)

        assert self.view.draw_image.call_count == 1
        assert self.view.draw_legend.call_count == 1
        assert self.view.draw_metadata.call_count == 1

    def test_filter_handling(self, qtbot):
        self.query_server(qtbot, self.url)
        server = self.window.multilayers.listLayers.findItems(f"{self.url}/",
                                                              QtCore.Qt.MatchFixedString)[0]
        self.window.cbAutoUpdate.setCheckState(False)
        assert server is not None
        assert "header" in self.window.multilayers.layers[f"{self.url}/"]
        assert "wms" in self.window.multilayers.layers[f"{self.url}/"]

        starts_at = int(40 * self.window.multilayers.scale)
        icon_start_fav = starts_at + 3
        if self.window.multilayers.cbMultilayering.isChecked():
            checkbox_width = round(self.window.multilayers.height * 0.75)
            icon_start_fav += checkbox_width + 6

        starts_at = int(20 * self.window.multilayers.scale)
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
        QtTest.QTest.mouseMove(self.window.multilayers.listLayers, QtCore.QPoint(icon_start_fav + 3, 0), -1)
        self.window.multilayers.check_icon_clicked(server.child(0))
        self.window.multilayers.filter_favourite_toggled()
        # ToDo The next assert fails in reverse test order
        assert not server.isHidden()
        server.child(0).favourite_triggered()
        self.window.multilayers.remove_filter_triggered()

        # Check deleting server is working
        QtTest.QTest.mouseMove(self.window.multilayers.listLayers, QtCore.QPoint(icon_start_del + 3, 0), -1)
        self.window.multilayers.check_icon_clicked(server)
        assert len(self.window.multilayers.listLayers.findItems(f"{self.url}/",
                                                                QtCore.Qt.MatchFixedString)) == 0

    def test_singlelayer_handling(self, qtbot):
        """
        assert that singlelayer mode behaves as expected
        """
        self.query_server(qtbot, self.url)
        server = self.window.multilayers.listLayers.findItems(f"{self.url}/",
                                                              QtCore.Qt.MatchFixedString)[0]
        self.window.cbAutoUpdate.setCheckState(False)
        assert server is not None
        assert "header" in self.window.multilayers.layers[f"{self.url}/"]
        assert "wms" in self.window.multilayers.layers[f"{self.url}/"]

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
        with qtbot.wait_signal(self.window.image_displayed):
            QtTest.QTest.mouseClick(self.window.btGetMap, QtCore.Qt.LeftButton)

        assert self.view.draw_image.call_count == 1
        assert self.view.draw_legend.call_count == 1
        assert self.view.draw_metadata.call_count == 1

    def test_multilayer_syncing(self, qtbot):
        """
        assert that synced layers share their options
        """
        self.query_server(qtbot, self.url)
        server = self.window.multilayers.listLayers.findItems(f"{self.url}/",
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

    @mock.patch("mslib.msui.wms_control.WMSMapFetcher.moveToThread")
    def test_server_no_thread(self, mockthread, qtbot):
        self.query_server(qtbot, self.url)
        server = self.window.multilayers.listLayers.findItems(f"{self.url}/",
                                                              QtCore.Qt.MatchFixedString)[0]
        self.window.cbAutoUpdate.setCheckState(False)
        server.setExpanded(True)
        self.window.multilayers.cbMultilayering.setChecked(True)
        server.child(0).setCheckState(0, 2)
        server.child(1).setCheckState(0, 2)

        with qtbot.wait_signal(self.window.image_displayed):
            QtTest.QTest.mouseClick(self.window.btGetMap, QtCore.Qt.LeftButton)

        urlstr = f"{self.url}/mss/logo.png"
        md5_filname = os.path.join(self.window.wms_cache, hashlib.md5(urlstr.encode('utf-8')).hexdigest() + ".png")
        self.window.fetcher.fetch_legend(urlstr, use_cache=False, md5_filename=md5_filname)
        self.window.fetcher.fetch_legend(urlstr, use_cache=True, md5_filename=md5_filname)

        assert self.view.draw_image.call_count == 1
        assert self.view.draw_legend.call_count == 1
        assert self.view.draw_metadata.call_count == 1


class Test_VSecWMSControlWidget(WMSControlWidgetSetup):
    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        self._setup("vsec")
        yield
        self._teardown()

    def test_server_getmap(self, qtbot):
        """
        assert that a getmap call to a WMS server displays an image
        """
        self.query_server(qtbot, self.url)
        with qtbot.wait_signal(self.window.image_displayed):
            QtTest.QTest.mouseClick(self.window.btGetMap, QtCore.Qt.LeftButton)

        assert self.view.draw_image.call_count == 1
        assert self.view.draw_legend.call_count == 1
        assert self.view.draw_metadata.call_count == 1

    def test_multilayer_drawing(self, qtbot):
        """
        assert that drawing a layer through code doesn't fail for vsec
        """
        self.query_server(qtbot, self.url)
        server = self.window.multilayers.listLayers.findItems(f"{self.url}/",
                                                              QtCore.Qt.MatchFixedString)[0]
        with qtbot.wait_signal(self.window.image_displayed):
            server.child(0).draw()


class TestWMSControlWidgetSetupSimple:
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

    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        self.view = HSecViewMockup()
        self.window = wc.HSecWMSControlWidget(view=self.view)
        self.window.show()

        # Remove all previous cached URLs
        for url in self.window.multilayers.layers.copy():
            server = self.window.multilayers.listLayers.findItems(url, QtCore.Qt.MatchFixedString)[0]
            self.window.multilayers.delete_server(server)

        yield
        self.window.hide()

    def test_xml(self):
        testxml = self.xml.format("", self.srs_base, self.dimext_time + self.dimext_inittime + self.dimext_elevation)
        self.window.activate_wms(wc.MSUIWebMapService(None, version='1.1.1', xml=testxml))
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
        self.window.activate_wms(wc.MSUIWebMapService(None, version='1.1.1', xml=testxml))
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
        self.window.activate_wms(wc.MSUIWebMapService(None, version='1.1.1', xml=testxml))
        assert [self.window.cbValidTime.itemText(i) for i in range(self.window.cbValidTime.count())] == []
        assert [self.window.cbInitTime.itemText(i) for i in range(self.window.cbInitTime.count())] == []
        assert [self.window.cbLevel.itemText(i) for i in range(self.window.cbLevel.count())] == []
        assert not self.window.cbLevel.isEnabled()
        assert not self.window.cbValidTime.isEnabled()
        assert not self.window.cbInitTime.isEnabled()

    def test_xml_onlytimedim(self):
        dimext_time_noext = '<Dimension name="TIME" units="ISO8610"> </Dimension>'

        testxml = self.xml.format("", self.srs_base, dimext_time_noext + self.dimext_inittime + self.dimext_elevation)
        self.window.activate_wms(wc.MSUIWebMapService(None, version='1.1.1', xml=testxml))
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
        self.window.activate_wms(wc.MSUIWebMapService(None, version='1.1.1', xml=testxml))
        assert [self.window.cbValidTime.itemText(i) for i in range(self.window.cbValidTime.count())] == \
            ['2012-10-17T12:00:00Z', '2012-10-17T18:00:00Z', '2012-10-18T00:00:00Z']
        assert [self.window.cbInitTime.itemText(i) for i in range(self.window.cbInitTime.count())] == \
            ['2012-10-16T12:00:00Z', '2012-10-17T12:00:00Z']
        assert [self.window.cbLevel.itemText(i) for i in range(self.window.cbLevel.count())] == \
            ['500.0 (hPa)', '600.0 (hPa)', '700.0 (hPa)', '900.0 (hPa)']

    def test_xml_separate_leafs(self):
        testxml = self.xml.format(
            self.dimext_inittime, self.srs_base, self.dimext_time + self.dimext_elevation)
        self.window.activate_wms(wc.MSUIWebMapService(None, version='1.1.1', xml=testxml))
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
        self.window.activate_wms(wc.MSUIWebMapService(None, version='1.1.1', xml=testxml))
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
        self.window.activate_wms(wc.MSUIWebMapService(None, version='1.1.1', xml=testxml))
        assert [self.window.cbValidTime.itemText(i) for i in range(self.window.cbValidTime.count())] == \
            ['2012-10-17T12:00:00Z', '2012-10-17T18:00:00Z', '2012-10-18T00:00:00Z']
        assert [self.window.cbInitTime.itemText(i) for i in range(self.window.cbInitTime.count())] == \
            ['2013-10-16T12:00:00Z', '2013-10-17T12:00:00Z']
        assert [self.window.cbLevel.itemText(i) for i in range(self.window.cbLevel.count())] == \
            ['500.0 (hPa)', '600.0 (hPa)', '700.0 (hPa)', '900.0 (hPa)']

    def test_xml_no_elevation(self):
        testxml = self.xml.format("", self.srs_base, self.dimext_time + self.dimext_inittime)
        self.window.activate_wms(wc.MSUIWebMapService(None, version='1.1.1', xml=testxml))
        assert [self.window.cbValidTime.itemText(i) for i in range(self.window.cbValidTime.count())] == \
            ['2012-10-17T12:00:00Z', '2012-10-17T18:00:00Z', '2012-10-18T00:00:00Z']
        assert [self.window.cbInitTime.itemText(i) for i in range(self.window.cbInitTime.count())] == \
            ['2012-10-16T12:00:00Z', '2012-10-17T12:00:00Z']
        assert [self.window.cbLevel.itemText(i) for i in range(self.window.cbLevel.count())] == []
        assert not self.window.cbLevel.isEnabled()

    def test_xml_no_validtime(self):
        testxml = self.xml.format("", self.srs_base, self.dimext_inittime + self.dimext_elevation)
        self.window.activate_wms(wc.MSUIWebMapService(None, version='1.1.1', xml=testxml))
        assert [self.window.cbValidTime.itemText(i) for i in range(self.window.cbValidTime.count())] == []
        assert not self.window.cbValidTime.isEnabled()
        assert [self.window.cbInitTime.itemText(i) for i in range(self.window.cbInitTime.count())] == \
            ['2012-10-16T12:00:00Z', '2012-10-17T12:00:00Z']
        assert [self.window.cbLevel.itemText(i) for i in range(self.window.cbLevel.count())] == \
            ['500.0 (hPa)', '600.0 (hPa)', '700.0 (hPa)', '900.0 (hPa)']

    def test_xml_no_inittime(self):
        testxml = self.xml.format(
            "", self.srs_base, self.dimext_time + self.dimext_elevation)
        self.window.activate_wms(wc.MSUIWebMapService(None, version='1.1.1', xml=testxml))
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
        self.window.activate_wms(wc.MSUIWebMapService(None, version='1.1.1', xml=testxml))
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
        self.window.activate_wms(wc.MSUIWebMapService(None, version='1.1.1', xml=testxml))
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
        self.window.activate_wms(wc.MSUIWebMapService(None, version='1.1.1', xml=testxml))
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
        self.window.activate_wms(wc.MSUIWebMapService(None, version='1.1.1', xml=testxml))
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
        self.window.activate_wms(wc.MSUIWebMapService(None, version='1.1.1', xml=testxml))
        self.window.cbAutoUpdate.setCheckState(False)
        self.window.cbInitTime.setCurrentIndex(0)
        assert [self.window.cbValidTime.itemText(i) for i in range(self.window.cbValidTime.count())] == \
            ['2012-10-17T00:00:00Z', '2012-10-18T00:00:00Z', '2012-10-19T00:00:00Z']
        assert [self.window.cbInitTime.itemText(i) for i in range(self.window.cbInitTime.count())] == \
            ['2012-10-16T12:00:00Z', '2012-10-17T12:00:00Z']

    def test_xml_time_error(self):
        dimext_time_error = """
            <Dimension name="TIME" units="ISO8610"> </Dimension>
            <Extent name="TIME"> a2012-10-17T12:00:00Z/2012-10-18T00:00:00Z/PT6H </Extent>"""
        testxml = self.xml.format(
            "", self.srs_base, dimext_time_error + self.dimext_inittime + self.dimext_elevation)
        self.window.activate_wms(wc.MSUIWebMapService(None, version='1.1.1', xml=testxml))
        assert [self.window.cbValidTime.itemText(i) for i in range(self.window.cbValidTime.count())] == []
        assert [self.window.cbInitTime.itemText(i) for i in range(self.window.cbInitTime.count())] == []
