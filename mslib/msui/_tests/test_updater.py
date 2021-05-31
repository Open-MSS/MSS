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

from mslib.msui.updater import Updater
from mslib.utils import Worker


class SubprocessDifferentVersionMock:
    def __init__(self, args=None, **named_args):
        self.returncode = 0
        self.args = args
        if args and "list" in args and "mss" in args:
            self.stdout = "*mss 0.0.0\n"
        else:
            self.stdout = "*mss 999.999.999\n"


class SubprocessSameMock:
    def __init__(self, args=None, **named_args):
        self.stdout = "*mss 999.999.999\n"
        self.returncode = 0
        self.args = args


class SubprocessGitMock:
    def __init__(self, args=None, **named_args):
        self.stdout = "true"
        self.args = args


def create_mock(function, on_success=None, on_failure=None, start=True):
    worker = Worker(function)
    if on_success:
        worker.finished.connect(on_success)
    if on_failure:
        worker.failed.connect(on_failure)
    if start:
        worker.run()
    return worker


class Test_MSS_ShortcutDialog:
    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)
        self.updater = Updater()

    def teardown(self):
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    @mock.patch("subprocess.Popen", new=SubprocessDifferentVersionMock)
    @mock.patch("subprocess.run", new=SubprocessDifferentVersionMock)
    @mock.patch("mslib.utils.Worker.create", create_mock)
    def test_update_recognised(self):
        update_available = False

        def update_signal():
            nonlocal update_available
            update_available = True

        self.updater.on_update_available.connect(update_signal)
        self.updater.run()

        assert self.updater.new_version == "999.999.999"
        assert update_available
        self.updater.new_version = "0.0.0"

        self.updater.update_mss()
        assert self.updater.base_path == "999.999.999"
        assert self.updater.current_path == "999.999.999"
        assert self.updater.progressBar.value() == 100
        assert self.updater.statusLabel.text() == "Update successful. Please restart MSS."

    @mock.patch("subprocess.Popen", new=SubprocessSameMock)
    @mock.patch("subprocess.run", new=SubprocessSameMock)
    @mock.patch("mslib.utils.Worker.create", create_mock)
    def test_no_update(self):
        self.updater.run()
        assert self.updater.statusLabel.text() == "Your MSS is up to date."

    @mock.patch("subprocess.Popen", new=SubprocessGitMock)
    @mock.patch("subprocess.run", new=SubprocessGitMock)
    @mock.patch("mslib.utils.Worker.create", create_mock)
    def test_no_update_on_git(self):
        self.updater.run()
        assert self.updater.new_version is None
        assert self.updater.statusLabel.text() == "Nothing to do"

    @mock.patch("subprocess.Popen", new=SubprocessDifferentVersionMock)
    @mock.patch("subprocess.run", new=SubprocessDifferentVersionMock)
    @mock.patch("mslib.utils.Worker.create", create_mock)
    def test_update_failed(self):
        update_available = False

        def update_signal():
            nonlocal update_available
            update_available = True

        self.updater.on_update_available.connect(update_signal)
        self.updater.run()

        assert self.updater.new_version == "999.999.999"
        assert update_available
        self.updater.new_version = "1000.1000.1000"

        self.updater.update_mss()
        assert self.updater.statusLabel.text() == "Update failed. Please try it manually or " \
                                                  "try replacing the environment!"

    @mock.patch("subprocess.Popen", new=SubprocessDifferentVersionMock)
    @mock.patch("subprocess.run", new=SubprocessDifferentVersionMock)
    def test_environment_replace(self):
        self.updater.new_version = "0.0.0"
        self.updater._set_base_env_path()
        assert self.updater._try_environment_replace()
