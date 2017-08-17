# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_local
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions for msui.mss_qt

    This file is part of mss.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017 by the mss team, see AUTHORS.
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

import mslib.msui.mss_qt as mqt


def test_variant():
    for test_val in [-12.2, 2, 0, 12.2]:
        var = mqt.QtCore.QVariant(test_val)
        val = var.value()
        assert isinstance(val, (int, float))
        assert abs(val - test_val) < 1e-6

    for test_val in ["-12.2", "2", "0", u"12.2", "abc", u"aöc"]:
        var = mqt.QtCore.QVariant(test_val)
        val = var.value()
        assert val == test_val


def test_localized_conversion():
    value, ok = mqt.QtCore.QLocale(mqt.QtCore.QLocale.English).toDouble("12.2")
    assert ok is True
    assert value == 12.2
    value, ok = mqt.QtCore.QLocale(mqt.QtCore.QLocale.German).toDouble("12,2")
    assert ok is True
    assert value == 12.2
    value, ok = mqt.QtCore.QLocale(mqt.QtCore.QLocale.German).toDouble("1.200")
    assert ok is True
    assert value == 1200
    value, ok = mqt.QtCore.QLocale(mqt.QtCore.QLocale.French).toDouble("12,2")
    assert ok is True
    assert value == 12.2


def test_variant_to_string():
    for value, variant in [("5", "5"), ("5", "5"), (u"öäü", u"öäü"), ("abc", "abc")]:
        conv_value = mqt.variant_to_string(mqt.QtCore.QVariant(variant))
        assert value == conv_value


def test_variant_to_float():
    for value, variant in [(5, "5"), (5, 5), (5.5, 5.5), (-5.5, -5.5)]:
        conv_value = mqt.variant_to_float(mqt.QtCore.QVariant(variant))
        assert value == conv_value

    german_locale = mqt.QtCore.QLocale(mqt.QtCore.QLocale.German)
    for value, string in [(5, "5"), (5.5, "5,5"), (1000, "1.000")]:
        conv_value = mqt.variant_to_float(mqt.QtCore.QVariant(string), locale=german_locale)
        assert conv_value == value
    french_locale = mqt.QtCore.QLocale(mqt.QtCore.QLocale.French)
    for value, string in [(5, "5"), (5.5, "5,5"), (1000, "1 000")]:
        conv_value = mqt.variant_to_float(mqt.QtCore.QVariant(string), locale=french_locale)
        assert conv_value == value
    english_locale = mqt.QtCore.QLocale(mqt.QtCore.QLocale.English)
    for value, string in [(5, "5"), (5.5, "5.5"), (1000, "1,000")]:
        conv_value = mqt.variant_to_float(mqt.QtCore.QVariant(string), locale=english_locale)
        assert conv_value == value
