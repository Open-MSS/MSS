# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_loopview
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.loopview

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


from builtins import range
from builtins import object
import sys
import mock

from mslib.msui.mss_qt import QtWidgets, QtTest
import mslib.msui.loopview as lv


loop_configuration = {
    "ECMWF forecasts": {
        # URL to the Mission Support website at which the batch image
        # products are located.
        "url": "http://www.your-server.de/forecasts",
        # Initialisation times every init_timestep hours.
        "init_timestep": 12,
        # Products available on the webpage. Add new products here!
        # Each product listed here will be loaded as one group, so
        # that the defined times can be navigated with <wheel> and
        # the defined levels can be navigated with <shift+wheel>.
        # Times not found in the listed range of forecast_steps
        # are ignored, its hence save to define the entire forecast
        # range with the smalled available time step.
        "products": {
            "Geopotential and Wind": {
                "abbrev": "geop",
                "regions": {"Europe": "eur", "Germany": "de"},
                "levels": [200, 250, 300, 500, 700, 850, 925],
                "forecast_steps": list(range(0, 240, 3))},
        }
    }
}


class Test_MSSLoopViewWindow(object):

    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)

        self.window = lv.MSSLoopWindow(loop_configuration)
        self.window.show()
        QtWidgets.QApplication.processEvents()
        try:
            QtTest.QTest.qWaitForWindowExposed(self.window)
        except AttributeError:
            QtTest.QTest.qWaitForWindowShown(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    @mock.patch("mslib.msui.mss_qt.QtWidgets.QMessageBox")
    def test_window_start(self, mockbox):
        assert mockbox.critical.call_count == 0
