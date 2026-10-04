# -*- coding: utf-8 -*-
"""

    tests._test_utils.test_qt
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions for mslib.utils.qt

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

import ast
from pathlib import Path

import pytest
import mock
import mslib
import mslib.utils.qt as mqt
import PyQt5 as pqt
from mslib.utils.config import config_loader
from mslib.utils import FatalUserError


def test_variant():
    for test_val in [-12.2, 2, 0, 12.2]:
        var = pqt.QtCore.QVariant(test_val)
        val = var.value()
        assert isinstance(val, (int, float))
        assert abs(val - test_val) < 1e-6

    for test_val in ["-12.2", "2", "0", u"12.2", "abc", u"aöc"]:
        var = pqt.QtCore.QVariant(test_val)
        val = var.value()
        assert val == test_val


def test_localized_conversion():
    value, ok = pqt.QtCore.QLocale(pqt.QtCore.QLocale.English).toDouble("12.2")
    assert ok is True
    assert value == 12.2
    value, ok = pqt.QtCore.QLocale(pqt.QtCore.QLocale.German).toDouble("12,2")
    assert ok is True
    assert value == 12.2
    value, ok = pqt.QtCore.QLocale(pqt.QtCore.QLocale.German).toDouble("1.200")
    assert ok is True
    assert value == 1200
    value, ok = pqt.QtCore.QLocale(pqt.QtCore.QLocale.French).toDouble("12,2")
    assert ok is True
    assert value == 12.2


def test_variant_to_string():
    for value, variant in [("5", "5"), ("5", "5"), (u"öäü", u"öäü"), ("abc", "abc")]:
        conv_value = mqt.variant_to_string(pqt.QtCore.QVariant(variant))
        assert value == conv_value


def test_variant_to_float():
    for value, variant in [(5, "5"), (5, 5), (5.5, 5.5), (-5.5, -5.5)]:
        conv_value = mqt.variant_to_float(pqt.QtCore.QVariant(variant))
        assert value == conv_value

    german_locale = pqt.QtCore.QLocale(pqt.QtCore.QLocale.German)
    for value, string in [(5, "5"), (5.5, "5,5"), (1000, "1.000")]:
        conv_value = mqt.variant_to_float(pqt.QtCore.QVariant(string), locale=german_locale)
        assert conv_value == value
    # A plain "." decimal point is accepted even under a locale that
    # expects a comma, e.g. text handed back unmodified by QItemDelegate's
    # default setEditorData, which does not reformat it for the locale.
    conv_value = mqt.variant_to_float(pqt.QtCore.QVariant("40.66"), locale=german_locale)
    assert conv_value == 40.66
    french_locale = pqt.QtCore.QLocale(pqt.QtCore.QLocale.French)
    for value, string in [(5, "5"), (5.5, "5,5"), (1000, "1 000")]:
        conv_value = mqt.variant_to_float(pqt.QtCore.QVariant(string), locale=french_locale)
        assert conv_value == value
    english_locale = pqt.QtCore.QLocale(pqt.QtCore.QLocale.English)
    for value, string in [(5, "5"), (5.5, "5.5"), (1000, "1,000")]:
        conv_value = mqt.variant_to_float(pqt.QtCore.QVariant(string), locale=english_locale)
        assert conv_value == value


def test_get_open_filename_qt():
    filename = "example.csv"
    with mock.patch("mslib.utils.qt.QtWidgets.QFileDialog.getOpenFileName", return_value=(filename, )):
        _filename = mqt.get_open_filename_qt()
        assert _filename == filename
    with mock.patch("mslib.utils.qt.QtWidgets.QFileDialog.getOpenFileName", return_value=filename):
        _filename = mqt.get_open_filename_qt()
        assert _filename == filename


def test_get_open_filenames_qt():
    filename = "example.csv"
    with mock.patch("mslib.utils.qt.QtWidgets.QFileDialog.getOpenFileNames", return_value=(filename, )):
        _filename = mqt.get_open_filenames_qt()
        assert _filename == filename
    with mock.patch("mslib.utils.qt.QtWidgets.QFileDialog.getOpenFileNames", return_value=filename):
        _filename = mqt.get_open_filenames_qt()
        assert _filename == filename


def test_get_pickertype():
    assert mqt.get_pickertype() == config_loader(dataset="filepicker_default")
    assert mqt.get_pickertype("default") == config_loader(dataset="filepicker_default")
    assert mqt.get_pickertype("qt") == "qt"
    with pytest.raises(FatalUserError) as exc_info:
        mqt.get_pickertype("undefined")
        assert type(exc_info.value.__cause__) is FatalUserError


def test_get_open_filename():
    filename = "example.csv"
    with mock.patch("mslib.utils.qt.get_open_filename_qt", return_value="example.csv"):
        _filename = mqt.get_open_filename(None, "", "", "csv", pickertype="qt")
        assert _filename == filename
    with mock.patch("mslib.utils.qt.get_open_filename_qt", return_value=""):
        _filename = mqt.get_open_filename(None, "", "", "csv", pickertype="qt")
        assert _filename is None
    with pytest.raises(FatalUserError) as exc_info:
        mqt.get_open_filename(None, "", "", "csv", pickertype="undefined")
        assert type(exc_info.value.__cause__) is FatalUserError


def test_get_open_filenames():
    filenames = ["example1.csv", "example2.csv"]
    with mock.patch("mslib.utils.qt.get_open_filenames_qt", return_value=filenames):
        _filenames = mqt.get_open_filenames(None, "", "", "csv", pickertype="qt")
        assert _filenames == filenames
    with pytest.raises(FatalUserError) as exc_info:
        mqt.get_open_filenames(None, "", "", "csv", pickertype="undefined")
        assert type(exc_info.value.__cause__) is FatalUserError
    with mock.patch("mslib.utils.qt.get_open_filenames_qt", return_value=[]):
        filenames = mqt.get_open_filenames(None, "", "", "csv", pickertype="qt")
        assert filenames is None


def test_save_filename():
    filename = "example.csv"
    with mock.patch("mslib.utils.qt.get_save_filename_qt", return_value="example.csv"):
        _filename = mqt.get_save_filename(None, "", "", filename, pickertype="qt")
        assert _filename == filename
    with pytest.raises(FatalUserError) as exc_info:
        _filename = mqt.get_save_filename(None, "", "", filename, pickertype="undefined")
        assert type(exc_info.value.__cause__) is FatalUserError
    with mock.patch("mslib.utils.qt.get_save_filename_qt", return_value=""):
        _filename = mqt.get_save_filename(None, "", "", "", pickertype="qt")
        assert _filename is None


@pytest.mark.parametrize("text", [
    '<img src="file://attacker.example/share/x.png">',
    'Temperature <b>bold</b> &amp; <a href="file:///etc/passwd">link</a>',
    'first line\n<img src="file:///x.png"> on the second line',
    "T<300K> mean",
    "plain text",
    "",
])
def test_plain_text_as_html(qtbot, text):
    shown = mqt.plain_text_as_html(text)
    # tooltips and message boxes decide with Qt.mightBeRichText how they show it
    if pqt.QtCore.Qt.mightBeRichText(shown):
        # rich text that shows the text itself, markup included
        document = pqt.QtGui.QTextDocument()
        document.setHtml(shown)
        assert document.toPlainText() == text
        # no image or link is in the rendered document
        assert "<img" not in document.toHtml() and "<a " not in document.toHtml()
    else:
        # shown as plain text anyway, so it stays as it is, e.g. for the messages tests compare
        assert shown == text


def test_show_popup_shows_text_as_it_is(qtbot):
    message = '<img src="file://attacker.example/share/x.png">Not found'
    with mock.patch("PyQt5.QtWidgets.QMessageBox.critical") as critical, \
            mock.patch("PyQt5.QtWidgets.QMessageBox.information") as information:
        mqt.show_popup(None, "Error", message)
        mqt.show_popup(None, "Information", "plain message", icon=1)
    assert critical.call_args.args[2] == mqt.plain_text_as_html(message) != message
    information.assert_called_once_with(None, "Information", "plain message")


def test_plain_text_message_box(qtbot):
    box = mqt.plain_text_message_box(pqt.QtWidgets.QMessageBox.Warning, "title", "<b>text</b>",
                                     pqt.QtWidgets.QMessageBox.Ok, None)
    assert box.textFormat() == pqt.QtCore.Qt.PlainText
    assert box.text() == "<b>text</b>"


# Texts of message boxes and tooltips that are not constants can come from a server or another user. Every one
# goes through plain_text_as_html (or show_popup or plain_text_message_box), see mslib/msui/CLAUDE.md.
# Exceptions build their HTML on purpose and escape every value in it.
RICH_TEXT_BUILT_ON_PURPOSE = {("mslib/msui/mscolab.py", "view_description")}
MESSAGE_BOX_FUNCTIONS = ("critical", "warning", "information", "question", "about")


def _is_constant_text(node):
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, ast.Call):
        function = ast.unparse(node.func)
        if function.endswith("plain_text_as_html"):
            return True
        # self.tr("...") of a constant
        if function.endswith(".tr") and all(isinstance(arg, ast.Constant) for arg in node.args):
            return True
    return False


def _texts_not_shown_as_plain_text():
    root = Path(mslib.__file__).parent.parent
    found = []
    for path in sorted((root / "mslib").rglob("*.py")):
        relative = path.relative_to(root)
        # the generated Qt UI files and the server packages, which show no Qt widgets
        if "qt5" in relative.parts or relative.parts[1] in ("mscolab", "mswms", "msidp"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        function_of = {}
        for function in ast.walk(tree):
            if isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for node in ast.walk(function):
                    function_of.setdefault(id(node), function.name)
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                continue
            if (node.func.attr in MESSAGE_BOX_FUNCTIONS and "QMessageBox" in ast.unparse(node.func.value)
                    and len(node.args) >= 3):
                text = node.args[2]
            elif node.func.attr == "setToolTip" and node.args:
                text = node.args[-1]
            else:
                continue
            place = (relative.as_posix(), function_of.get(id(node)))
            if not _is_constant_text(text) and place not in RICH_TEXT_BUILT_ON_PURPOSE:
                found.append(f"{relative.as_posix()}:{node.lineno}: {ast.unparse(text)[:80]}")
    return found


def test_message_box_and_tooltip_texts_are_shown_as_plain_text():
    assert _texts_not_shown_as_plain_text() == []
