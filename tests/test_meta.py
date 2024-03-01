# -*- coding: utf-8 -*-
"""

    tests.test_meta
    ~~~~~~~~~~~~~~~

    This module provides tests that are "meta" in some way, i.e. that don't test
    application code but test that e.g. other tests follow some convention.

    This file is part of MSS.

    :copyright: Copyright 2024 by the MSS team, see AUTHORS.
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
import pathlib


def test_processEvents_is_not_used_in_tests(request):
    """Check that no test is calling PyQt5.QtWidgets.QApplication.processEvents() explicitly."""
    tests_path = pathlib.Path(request.config.rootdir) / "tests"
    for test_file in tests_path.rglob("*.py"):
        if str(test_file) == request.fspath:
            # Skip the current file
            continue
        assert (
            "processEvents" not in test_file.read_text()
        ), "processEvents is mentioned in {}".format(test_file.relative_to(request.config.rootdir))


def test_qWait_is_not_used_in_tests(request):
    """Check that no test is calling PyQt5.QtTest.QTest.qWait explicitly."""
    tests_path = pathlib.Path(request.config.rootdir) / "tests"
    for test_file in tests_path.rglob("*.py"):
        if str(test_file) == request.fspath:
            # Skip the current file
            continue
        assert (
            "qWait(" not in test_file.read_text()
        ), "qWait is mentioned in {}".format(test_file.relative_to(request.config.rootdir))
