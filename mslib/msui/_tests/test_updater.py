# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_updater
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.updater

    This file is part of mss.

    :copyright: Copyright 2021 May Bär
    :copyright: Copyright 2021 by the mss team, see AUTHORS.
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
import sys
import mock
from PyQt5 import QtWidgets

from mslib._tests.utils import wait_until_signal
from mslib.msui.updater import Updater
from mslib import __version__


class SubprocessVersionMock:
    def __init__(self):
        self.stdout = "*mss 999.999.999\n"
        self.returncode = 0


class SubprocessSameMock:
    def __init__(self):
        self.stdout = f"*mss {__version__}\n"
        self.returncode = 0


class SubprocessGitMock:
    def __init__(self):
        self.stdout = "true"


class Test_MSS_ShortcutDialog:
    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)
        self.updater = Updater()

    def teardown(self):
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    @mock.patch("subprocess.run", return_value=SubprocessVersionMock())
    def test_update_recognised(self, subprocess_mock):
        update_available = False
        status = ""
        progress = 0
        finished = False

        def status_changed(s):
            nonlocal status
            status = s

        def progress_changed(i):
            nonlocal progress
            progress = i

        def update_signal():
            nonlocal update_available
            update_available = True

        def finished_signal():
            nonlocal finished
            finished = True

        self.updater.on_status_update.connect(status_changed)
        self.updater.on_update_finished.connect(finished_signal)
        self.updater.on_progress_update.connect(progress_changed)
        self.updater.on_update_available.connect(update_signal)
        self.updater.run()

        wait_until_signal(self.updater.on_update_available, 1)
        assert self.updater.new_version == "999.999.999"
        assert update_available

        self.updater.update_mss()
        wait_until_signal(self.updater.on_update_finished, 1)
        assert self.updater.base_path == "999.999.999"
        assert self.updater.current_path == "999.999.999"
        assert progress == 100
        assert finished
        assert status == "Update finished. Please restart MSS."

    @mock.patch("subprocess.run", return_value=SubprocessSameMock())
    def test_no_update(self, subprocess_mock):
        update_available = False
        status = ""

        def update_signal():
            nonlocal update_available
            update_available = True

        def status_changed(s):
            nonlocal status
            status = s

        self.updater.on_update_available.connect(update_signal)
        self.updater.on_status_update.connect(status_changed)
        self.updater.run()

        wait_until_signal(self.updater.on_update_available, 1)
        assert self.updater.new_version == __version__
        assert not update_available
        assert status == "Your MSS is up to date."

    @mock.patch("subprocess.run", return_value=SubprocessGitMock())
    def test_no_update_on_git(self, subprocess_mock):
        update_available = False

        def update_signal():
            nonlocal update_available
            update_available = True

        self.updater.on_update_available.connect(update_signal)
        self.updater.run()

        wait_until_signal(self.updater.on_update_available, 1)
        assert self.updater.new_version is None
        assert not update_available

    @mock.patch("subprocess.run", return_value=SubprocessVersionMock())
    def test_update_failed(self, subprocess_mock):
        update_available = False
        status = ""
        progress = 0
        finished = False

        def status_changed(s):
            nonlocal status
            status = s

        def progress_changed(i):
            nonlocal progress
            progress = i

        def update_signal():
            nonlocal update_available
            update_available = True

        def finished_signal():
            nonlocal finished
            finished = True

        self.updater.on_status_update.connect(status_changed)
        self.updater.on_update_finished.connect(finished_signal)
        self.updater.on_progress_update.connect(progress_changed)
        self.updater.on_update_available.connect(update_signal)
        self.updater.run()

        wait_until_signal(self.updater.on_update_available, 1)
        assert self.updater.new_version == "999.999.999"
        assert update_available
        self.updater.new_version = "1000.1000.1000"

        self.updater.update_mss()
        wait_until_signal(self.updater.on_update_failed, 1)
        assert progress == 45
        assert not finished
        assert status == "Update failed, please do it manually."
