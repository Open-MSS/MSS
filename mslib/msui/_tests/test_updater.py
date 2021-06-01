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
from PyQt5 import QtWidgets, QtTest

from mslib.msui.updater import UpdaterUI, Updater
from mslib.utils import Worker


def no_conda(args=None, **named_args):
    raise FileNotFoundError


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
        self.updater = Updater()
        self.status = ""
        self.update_available = False
        self.update_finished = False

        def update_signal(old, new):
            self.update_available = True

        def update_finished_signal():
            self.update_finished = True

        def status_signal(s):
            self.status = s

        self.updater.on_update_available.connect(update_signal)
        self.updater.on_status_update.connect(status_signal)
        self.updater.on_update_finished.connect(update_finished_signal)
        self.application = QtWidgets.QApplication(sys.argv)

    def teardown(self):
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    @mock.patch("subprocess.Popen", new=SubprocessDifferentVersionMock)
    @mock.patch("subprocess.run", new=SubprocessDifferentVersionMock)
    @mock.patch("mslib.utils.Worker.create", create_mock)
    def test_update_recognised(self):
        self.updater.run()

        assert self.updater.new_version == "999.999.999"
        assert self.update_available
        self.updater.new_version = "0.0.0"

        self.updater.update_mss()
        assert self.status == "Update successful. Please restart MSS."
        assert self.update_finished

    @mock.patch("subprocess.Popen", new=SubprocessSameMock)
    @mock.patch("subprocess.run", new=SubprocessSameMock)
    @mock.patch("mslib.utils.Worker.create", create_mock)
    def test_no_update(self):
        self.updater.run()
        assert self.status == "Your MSS is up to date."
        assert not self.update_available
        assert not self.update_finished

    @mock.patch("subprocess.Popen", new=SubprocessDifferentVersionMock)
    @mock.patch("subprocess.run", new=SubprocessDifferentVersionMock)
    @mock.patch("mslib.utils.Worker.create", create_mock)
    def test_update_failed(self):
        self.updater.run()
        assert self.updater.new_version == "999.999.999"
        assert self.update_available
        self.updater.new_version = "1000.1000.1000"
        self.updater.update_mss()
        assert self.status == "Update failed. Please try it manually or " \
                              "by creating a new environment!"

    @mock.patch("subprocess.Popen", new=no_conda)
    @mock.patch("subprocess.run", new=no_conda)
    @mock.patch("mslib.utils.Worker.create", create_mock)
    def test_no_conda(self):
        self.updater.run()
        assert self.updater.new_version is None and self.updater.old_version is None
        assert not self.update_available
        assert not self.update_finished

    @mock.patch("subprocess.Popen", new=no_conda)
    @mock.patch("subprocess.run", new=no_conda)
    @mock.patch("mslib.utils.Worker.create", create_mock)
    def test_exception(self):
        self.updater.new_version = "999.999.999"
        self.updater.old_version = "999.999.999"
        self.updater.update_mss()
        assert self.status == "Update failed, please do it manually."
        assert not self.update_finished

    @mock.patch("subprocess.Popen", new=SubprocessSameMock)
    @mock.patch("subprocess.run", new=SubprocessSameMock)
    @mock.patch("PyQt5.QtWidgets.QMessageBox.information", return_value=QtWidgets.QMessageBox.Yes)
    @mock.patch("mslib.utils.Worker.create", create_mock)
    def test_ui(self, mock):
        ui = UpdaterUI()
        ui.updater.on_update_available.emit("", "")
        QtTest.QTest.qWait(100)
        assert ui.statusLabel.text() == "Update successful. Please restart MSS."
        assert ui.btRestart.isEnabled()
