# -*- coding: utf-8 -*-
"""

    _tests._test_msui.test_multiple_flightpath_dockwidget
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tesst for the MultipleFlightpathControlWidget

    This file is part of MSS.

    :copyright: Copyright 2023 Reimar Bauer
    :copyright: Copyright 2023-2024 by the MSS team, see AUTHORS.
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
import pytest
# from PyQt5 import QtTest
from mslib.msui import msui
# from mslib.msui.multiple_flightpath_dockwidget import MultipleFlightpathControlWidget
# from mslib.msui import flighttrack as ft
import mslib.msui.topview as tv


class Test_MultipleFlightpathControlWidget:
    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        # Start a MSUI window
        self.main_window = msui.MSUIMainWindow()
        self.main_window.show()
        qtbot.wait_exposed(self.main_window)

        # Create two flight tracks
        self.main_window.actionNewFlightTrack.trigger()
        self.main_window.actionNewFlightTrack.trigger()

        # Open a Top View window
        self.main_window.actionTopView.trigger()
        self.topview_window = self.main_window.listViews.currentItem().window

        # Switch to the Multiple Flightpath Widget
        self.topview_window.cbTools.setCurrentIndex(6)

        # Get a reference to the created MultipleFlightpathControlWidget
        self.multiple_flightpath_widget = self.topview_window.docks[tv.MULTIPLEFLIGHTPATH].widget()

        yield
        self.main_window.hide()

    def test_initialization(self):
        # Ensure the MultipleFlightpathControlWidget is correctly initialized
        assert self.multiple_flightpath_widget is not None
        assert self.multiple_flightpath_widget.color == (0, 0, 1, 1)
