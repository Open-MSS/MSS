# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_utils
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for mscolab/utils

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2021 by the mss team, see AUTHORS.

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
import time
import pytest

from PyQt5 import QtWidgets

from mslib.mscolab.models import User
from mslib.mscolab.utils import get_recent_pid
from mslib.mscolab.conf import mscolab_settings
from mslib.msui.mscolab import MSSMscolabWindow
from mslib._tests.utils import mscolab_start_server


PORTS = list(range(9561, 9580))


@pytest.mark.skipif(os.name == "nt",
                    reason="multiprocessing needs currently start_method fork")
class Test_Utils(object):
    def setup(self):
        self.process, self.url, self.app, _, self.cm, self.fm = mscolab_start_server(PORTS)
        time.sleep(0.1)
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = MSSMscolabWindow(data_dir=mscolab_settings.MSCOLAB_DATA_DIR,
                                       mscolab_server_url=self.url)
        with self.app.app_context():
            self.user = User.query.filter_by(id=8).first()

    def teardown(self):
        if self.window.version_window:
            self.window.version_window.close()
        if self.window.conn:
            self.window.conn.disconnect()
        self.application.quit()
        QtWidgets.QApplication.processEvents()
        self.process.terminate()

    def test_get_recent_pid(self):
        with self.app.app_context():
            p_id = get_recent_pid(self.fm, self.user)
        assert p_id == 4
