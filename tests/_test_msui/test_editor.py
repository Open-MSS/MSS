# -*- coding: utf-8 -*-
"""

    tests._test.msui.test_editor
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    testscript for the config editor

    This file is part of MSS.

    :copyright: Copyright 2020 Vaibhav Mehra <veb7vmehra@gmail.com>
    :copyright: Copyright 2020-2026 by the MSS team, see AUTHORS.
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
from PyQt5 import QtWidgets
from mslib.msui import editor
from tests import constants


def test_import_config_reports_ignored_entries(qtbot, tmp_path):
    import_file = tmp_path / "import.json"
    import_file.write_text('{"num_labels": "12", "num_interpolation_points": 30}')
    window = editor.ConfigurationEditorWindow()
    with mock.patch("mslib.msui.editor.get_open_filename", return_value=str(import_file)), \
            mock.patch("PyQt5.QtWidgets.QMessageBox.information") as m:
        window.import_config()
    assert m.call_count == 1
    assert "'num_labels': '12' has the wrong type" in m.call_args[0][2]
    assert window.statusbar.currentMessage() == "Imported config, 1 entries ignored"
    data = window.json_model.serialize()
    assert data["num_interpolation_points"] == 30
    assert data["num_labels"] == 10
    with mock.patch("PyQt5.QtWidgets.QMessageBox.warning", return_value=QtWidgets.QMessageBox.No):
        window.close()


@pytest.mark.skip("To be done for new UI")
class Test_Editor:
    sample_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "msui_settings.json"))
    sample_file = sample_file.replace('\\', '/')

    save_file_name = constants.MSUI_CONFIG_PATH / "testeditor_save.json"

    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        with mock.patch("PyQt5.QtWidgets.QMessageBox.warning", return_value=QtWidgets.QMessageBox.Yes):
            self.window = editor.EditorMainWindow()
            self.save_file_name = self.save_file_name
            self.window.show()
            yield
            if os.path.exists(self.save_file_name):
                os.remove(self.save_file_name)
            self.window.hide()

    @mock.patch("mslib.msui.editor.get_open_filename", return_value=sample_file)
    def test_file_open(self, mockfile):
        self.window.file_open()
        assert "location" in self.window.file_content

    @pytest.mark.skip("needs to be run isolated! With the restart of MSS the config for all other tests is changed")
    @mock.patch("mslib.msui.editor.get_open_filename", return_value=sample_file)
    def test_file_save_and_quit(self, mockfile):
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
