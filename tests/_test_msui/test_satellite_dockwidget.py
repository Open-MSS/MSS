# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_satellite_dockwidget
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.satellite_dockwidget

    This file is part of MSS.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017-2026 by the MSS team, see AUTHORS.
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
from datetime import datetime

import mock
import numpy as np
import pytest
from PyQt5 import QtCore, QtTest
import mslib.msui.satellite_dockwidget as sd

SAMPLE = os.path.join(os.path.dirname(__file__), "../", "data", "satellite_predictor.txt")


def test_read_nasa_satellite_prediction_keeps_every_point():
    segments = sd.read_nasa_satellite_prediction(SAMPLE)
    assert len(segments) == 10
    # every data line of the file is in an overpass, also the first one after a gap and those of the last overpass
    with open(SAMPLE) as sample:
        assert sum(len(segment["utc"]) for segment in segments) == len(sample.read().splitlines()) - 2
    assert segments[0]["utc"][0] == datetime(2017, 1, 27, 0, 0, 0)
    assert segments[-1]["utc"][-1] == datetime(2017, 1, 27, 23, 1, 20)
    for segment in segments:
        for key in ("satpos", "heading", "swath_left", "swath_right"):
            assert len(segment[key]) == len(segment["utc"])


def test_read_nasa_satellite_prediction_segments(tmp_path):
    prediction = tmp_path / "prediction.txt"
    prediction.write_text("""2017/01/27 Orbital Tracks
   GMT      SUBLAT    SUBLON  HEADING
00:00:00   33.3741  -31.5336  -999.00
00:00:20   32.1739  -31.2049   192.88
01:00:00   10.0000   20.0000   190.00
01:00:20   11.0000   21.0000   191.00

""")
    first, second = sd.read_nasa_satellite_prediction(prediction)
    assert list(first["utc"]) == [datetime(2017, 1, 27, 0, 0, 0), datetime(2017, 1, 27, 0, 0, 20)]
    assert list(second["utc"]) == [datetime(2017, 1, 27, 1, 0, 0), datetime(2017, 1, 27, 1, 0, 20)]
    # LON of the file is negated, see read_nasa_satellite_prediction
    assert np.allclose(second["satpos"], [[-20., 10.], [-21., 11.]])
    # -999 marks missing values
    assert first["heading"].mask.tolist() == [True, False]


class Test_SatelliteDockWidget:
    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        self.view = mock.Mock()
        self.window = sd.SatelliteControlWidget(view=self.view)
        self.window.show()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        yield
        self.window.hide()

    def test_load(self):
        self.window.leFile.setText(SAMPLE)
        assert self.window.cbSatelliteOverpasses.count() == 0
        QtTest.QTest.mouseClick(self.window.btLoadFile, QtCore.Qt.LeftButton)
        # "None", "All tracks" and the 10 overpasses of the file
        assert self.window.cbSatelliteOverpasses.count() == 12
        assert self.view.plot_satellite_overpass.call_count == 1
        self.window.cbSatelliteOverpasses.currentIndexChanged.emit(2)
        assert self.view.plot_satellite_overpass.call_count == 2
        self.view.reset_mock()

    @mock.patch("PyQt5.QtWidgets.QMessageBox.critical")
    def test_load_no_file(self, mockbox):
        QtTest.QTest.mouseClick(self.window.btLoadFile, QtCore.Qt.LeftButton)
        assert self.window.cbSatelliteOverpasses.count() == 0
        mockbox.assert_called_once_with(
            self.window,
            'Satellite Overpass Tool',
            "ERROR:\n<class 'IsADirectoryError'>\n[Errno 21] Is a directory: '.'"
        )
