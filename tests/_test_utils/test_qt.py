# -*- coding: utf-8 -*-
"""

    tests._test_utils.test_qt
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions for mslib.utils.qt

    This file is part of MSS.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017-2024 by the MSS team, see AUTHORS.
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
    assert mqt.get_pickertype("fs") == "fs"
    with pytest.raises(FatalUserError) as exc_info:
        mqt.get_pickertype("undefined")
        assert type(exc_info.value.__cause__) is FatalUserError


def test_get_open_filename():
    filename = "example.csv"
    with mock.patch("mslib.utils.qt.get_open_filename_qt", return_value="example.csv"):
        _filename = mqt.get_open_filename(None, "", "", "csv", pickertype="qt")
        assert _filename == filename
    with mock.patch("mslib.utils.qt.getOpenFileName", return_value="example.csv"):
        _filename = mqt.get_open_filename(None, "", "", "csv", pickertype="fs")
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
    with mock.patch("mslib.utils.qt.getSaveFileName", return_value="example.csv"):
        _filename = mqt.get_save_filename(None, "", "", filename, pickertype="fs")
        assert _filename == filename
    with mock.patch("mslib.utils.qt.get_save_filename_qt", return_value="example.csv"):
        _filename = mqt.get_save_filename(None, "", "", filename, pickertype="qt")
        assert _filename == filename
    with pytest.raises(FatalUserError) as exc_info:
        _filename = mqt.get_save_filename(None, "", "", filename, pickertype="undefined")
        assert type(exc_info.value.__cause__) is FatalUserError
    with mock.patch("mslib.utils.qt.get_save_filename_qt", return_value=""):
        _filename = mqt.get_save_filename(None, "", "", "", pickertype="qt")
        assert _filename is None
