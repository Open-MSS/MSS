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
import json
from pathlib import Path

import mock
from PyQt5 import QtWidgets
from mslib.msui import editor


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


def _editor_with_change(tmp_path):
    """
    An editor window that saves to tmp_path, with one value changed by an import
    """
    import_file = tmp_path / "import.json"
    import_file.write_text('{"num_interpolation_points": 30}')
    window = editor.ConfigurationEditorWindow()
    window.path = str(tmp_path / "msui_settings.json")
    with mock.patch("mslib.msui.editor.get_open_filename", return_value=str(import_file)):
        window.import_config()
    assert window.check_modified()
    return window


def test_save_config_and_restart(qtbot, tmp_path):
    """
    Saving changes asks for the restart, saves to the window's path and asks the main window
    to restart by a signal; a window without a main window restarts nothing (#1138)
    """
    window = _editor_with_change(tmp_path)
    window.show()
    with mock.patch("PyQt5.QtWidgets.QMessageBox.warning", return_value=QtWidgets.QMessageBox.Yes) as m, \
            qtbot.wait_signal(window.restartApplication, timeout=1000):
        assert window.save_config() is True
    assert "restart" in m.call_args_list[0][0][2]
    assert json.loads(Path(window.path).read_text())["num_interpolation_points"] == 30
    assert not window.isVisible()
    assert not window.check_modified()


def test_save_config_declined(qtbot, tmp_path):
    """
    Declining the restart doesn't save and doesn't restart
    """
    window = _editor_with_change(tmp_path)
    emitted = mock.Mock()
    window.restartApplication.connect(emitted)
    with mock.patch("PyQt5.QtWidgets.QMessageBox.warning", return_value=QtWidgets.QMessageBox.No):
        window.save_config()
    assert not Path(window.path).exists()
    emitted.assert_not_called()
    assert window.check_modified()
    with mock.patch("PyQt5.QtWidgets.QMessageBox.warning", return_value=QtWidgets.QMessageBox.No):
        window.close()


def test_export_config(qtbot, tmp_path):
    """
    Export writes the changed values to the chosen file, without asking for a restart
    """
    window = _editor_with_change(tmp_path)
    export_file = tmp_path / "export.json"
    with mock.patch("mslib.msui.editor.get_save_filename", return_value=str(export_file)):
        window.export_config()
    assert json.loads(export_file.read_text())["num_interpolation_points"] == 30
    assert not Path(window.path).exists()
    with mock.patch("PyQt5.QtWidgets.QMessageBox.warning", return_value=QtWidgets.QMessageBox.No):
        window.close()
