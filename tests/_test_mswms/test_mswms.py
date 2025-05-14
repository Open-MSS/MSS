# -*- coding: utf-8 -*-
"""

    tests._test_mswms.test_mswms
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.msui

    This file is part of MSS.

    :copyright: Copyright 2022 Reimar Bauer
    :copyright: Copyright 2022-2025 by the MSS team, see AUTHORS.
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


import mock
import sys
import argparse
import pytest
from mslib.mswms import mswms


def test_main_version(monkeypatch, capsys):
    """Test if --version flag outputs the correct version and exits"""
    monkeypatch.setattr(sys, "argv",  ["mswms", "--version"])
    with pytest.raises(SystemExit):
        mswms.main()
    captured = capsys.readouterr()
    assert "Mission Support System" in captured.out
    assert "Version:" in captured.out


def test_main_host_argument(monkeypatch, capsys):
    """Test if --host argument parses correctly"""
    monkeypatch.setattr(sys, "argv", ["mswms", "--host", "127.0.0.2"])
    with pytest.raises(SystemExit):
        mswms.main()
    captured = capsys.readouterr()
    assert "Running on http://127.0.0.2" in captured.out


def test_main_port_argument(monkeypatch, capsys):
    """Test if --port argument parses correctly"""
    monkeypatch.setattr(sys, "argv", ["mswms", "--port", "80001"])
    with pytest.raises(SystemExit):
        mswms.main()
    captured = capsys.readouterr()
    assert ":80001" in captured.out


def test_main_debug_option(monkeypatch, capsys):
    """Test if --debug flag activates the debug mode"""
    monkeypatch.setattr(sys, "argv", ["mswms", "--debug"])
    with pytest.raises(SystemExit):
        mswms.main()
    captured = capsys.readouterr()
    assert "Debug mode: on" in captured.out
    assert "_internal._log" in captured.out


def test_main_invalid_argument(monkeypatch, capsys):
    """Test invalid command-line argument handling"""
    monkeypatch.setattr(sys, "argv", ["mswms", "--invalid"])
    with pytest.raises(SystemExit):
        mswms.main()
    captured = capsys.readouterr()
    assert "unrecognized arguments: --invalid" in captured.err


def test_main_gallery_create(monkeypatch, capsys):
    """Test gallery subcommand with create option"""
    monkeypatch.setattr(sys, "argv", ["mswms", "gallery", "--create", "--plot_types", "Top"])
    with pytest.raises(SystemExit):
        mswms.main()
    captured = capsys.readouterr()
    assert "Gallery generation done" in captured.out

