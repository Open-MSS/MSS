# -*- coding: utf-8 -*-
"""

    mslib.msui.test_editor
    ~~~~~~~~~~~~~~~~~~~~~~

    testscript for the config editor

    This file is part of mss.

    :copyright: Copyright 2020 Vaibhav Mehra <veb7vmehra@gmail.com>
    :copyright: Copyright 2020-2021 by the mss team, see AUTHORS.
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
import mock
import os
import fs
import sys
from PyQt5 import QtWidgets
from mslib.msui import editor
from mslib._tests.constants import ROOT_DIR


class Test_Editor(object):
    sample_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs",
                                  "samples", "config", "mss", "mss_settings.json.sample"))
    sample_file = sample_file.replace('\\', '/')

    save_file_name = fs.path.join(ROOT_DIR, "testeditor_save.json")

    @mock.patch("PyQt5.QtWidgets.QMessageBox.warning", return_value=QtWidgets.QMessageBox.Yes)
    def setup(self, mockmessage):
        self.application = QtWidgets.QApplication(sys.argv)

        self.window = editor.EditorMainWindow()
        self.save_file_name = self.save_file_name
        self.window.show()

    def teardown(self):
        if os.path.exists(self.save_file_name):
            os.remove(self.save_file_name)
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    @mock.patch("mslib.msui.editor.get_open_filename", return_value=sample_file)
    def test_file_open(self, mockfile):
        self.window.file_open()
        assert "location" in self.window.file_content

    @mock.patch("mslib.msui.editor.get_open_filename", return_value=sample_file)
    def test_file_save_and_quit(self, mockfile):
        pytest.skip('needs to be run isolated! With the restart of MSS the config for all other tests is changed')
        self.window.file_open()
        self.window.path = self.save_file_name
        self.window.editor.setPlainText(self.window.editor.toPlainText() + " ")
        self.window.file_save_and_quit()
        assert os.path.exists(self.save_file_name)

    @mock.patch("mslib.msui.editor.get_open_filename", return_value=sample_file)
    @mock.patch("mslib.msui.editor.get_save_filename", return_value=save_file_name)
    def test_file_saveas(self, mocksaveas, mockfile):
        self.window.file_open()
        self.window.path = None
        self.window.editor.setPlainText(self.window.editor.toPlainText() + " ")
        self.window.file_saveas()
        assert os.path.exists(self.save_file_name)
