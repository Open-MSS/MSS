# -*- coding: utf-8 -*-
"""

    tests._test_utils.test_mssautoplot
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to test mslib.utils.mssautoplot

    This file is part of MSS.

    :copyright: Copyright 2022 Sreelakshmi Jayarajan
    :copyright: Copyright 2022 by the MSS team, see AUTHORS.
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
import fnmatch
import logging
from click.testing import CliRunner
from mslib.utils import mssautoplot
from datetime import datetime, timedelta
from tests.utils import wait_until_signal
import mslib.msui.wms_control as wc
from tests.constants import ROOT_DIR


PORTS = list(range(18600, 19000)) # ToDo


class HSecViewMockup(mock.Mock):
    get_crs = mock.Mock(return_value="EPSG:4326")
    getBBOX = mock.Mock(return_value=(0, 0, 10, 10))
    get_plot_size_in_px = mock.Mock(return_value=(200, 100))


class Test_mssautoplot(object):
    def setup(self):
        wc.WMS_SERVICE_CACHE = {}
        self.port = PORTS.pop()
        self.view = HSecViewMockup()
        # path
        parent_dir = ROOT_DIR
        # Create the directory
        directory = "Plots"
        # Path
        self.path = os.path.join(parent_dir, directory)
        try:
            os.mkdir(self.path)
        except OSError as error:
            logging.error(error)
        self.window = wc.HSecWMSControlWidget(view=self.view, wms_cache=self.path)

    def test_download_one_plot(self):
        dir_path = self.path
        count1 = len(fnmatch.filter(os.listdir(dir_path), '*.*'))
        runner = CliRunner()
        kwargs = {"--itime": "", "--vtime": "2019-09-02T00:00:00"}
        runner = CliRunner()
        result = runner.invoke(mssautoplot, args=kwargs)
        wait_until_signal(self.window.image_displayed)

        assert self.view.draw_image.call_count == 1
        assert self.view.draw_legend.call_count == 1
        assert self.view.draw_metadata.call_count == 1

        count2 = len(fnmatch.filter(os.listdir(dir_path), '*.*'))
        assert result.exit_code == 0
        assert result.output == 'Plot downloaded!\n'
        assert count2 == count1 + 1
        self.view.reset_mock()

    def test_download_multiple_plots(self):
        dir_path = self.path
        count1 = len(fnmatch.filter(os.listdir(dir_path), '*.*'))
        runner = CliRunner()
        kwargs = {"--stime": "2019-09-01T00:00:00", "--etime": "2019-09-02T00:00:00", "--intv": "6"}
        runner = CliRunner()
        result = runner.invoke(mssautoplot, args=kwargs)
        wait_until_signal(self.window.image_displayed)

        start = kwargs["--stime"]
        end = kwargs["--etime"]
        intv = kwargs["--intv"]
        starttime = datetime.strptime(start, "%Y-%m-%dT" "%H:%M:%S")
        endtime = datetime.strptime(end, "%Y-%m-%dT" "%H:%M:%S")
        count = 0
        while starttime <= endtime:
            count = count + 1
            starttime = starttime + timedelta(hours=intv)
        assert self.view.draw_image.call_count == count
        assert self.view.draw_legend.call_count == count
        assert self.view.draw_metadata.call_count == count
        count2 = len(fnmatch.filter(os.listdir(dir_path), '*.*'))
        assert result.exit_code == 0
        assert result.output == 'Plots downloaded!\n'
        assert count2 == count1 + count
        self.view.reset_mock()

    def teardown(self):
        os.rmdir("plots")
