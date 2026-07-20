# -*- coding: utf-8 -*-
"""
    tests._test_utils.test_colordialog
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests for mslib.utils.colordialog.

    This file is part of MSS.

    :copyright: Copyright 2026 by Reimar Bauer.
    :license: APACHE-2.0, see LICENSE for details.
"""
import pytest
from mslib.utils.colordialog import CustomColorDialog


@pytest.fixture
def dialog(qtbot):
    dlg = CustomColorDialog()
    qtbot.addWidget(dlg)
    return dlg


def test_dialog_has_object_name(dialog):
    assert dialog.objectName() == "ColorSelectDialog"


def test_every_swatch_has_unique_tutorial_name(dialog):
    names = [b.property("color_name") for b in dialog.color_buttons]
    assert all(n for n in names), "every swatch must carry a color_name"
    assert len(names) == len(dialog.colors)
    assert len(set(names)) == len(names), "swatch names must be unique"


def test_swatch_maps_to_expected_hex(dialog):
    by_name = {b.property("color_name"): dialog.colors[i]
               for i, b in enumerate(dialog.color_buttons)}
    assert by_name["red"] == "#e6194B"
    assert by_name["blue"] == "#0000ff"


def test_marked_swatches_are_captured_in_tutorial_mode(qtbot, tmp_path, monkeypatch):
    """create_tutorial_images() (get_shortcuts in tutorial_mode) writes a PNG per swatch."""
    from mslib.utils import constants
    from mslib.msui.msui_mainwindow import MSUI_ShortcutsDialog
    monkeypatch.setattr(constants, "MSUI_CONFIG_PATH", tmp_path)

    color_dlg = CustomColorDialog()
    qtbot.addWidget(color_dlg)
    color_dlg.show()
    qtbot.waitExposed(color_dlg)

    shortcuts = MSUI_ShortcutsDialog(tutorial_mode=True)
    qtbot.addWidget(shortcuts)
    # The real Ctrl+F search path checks cbNoShortcut so widgets without a
    # keyboard shortcut (the swatches) are included (msui_mainwindow.py ~line 1176).
    shortcuts.cbNoShortcut.setCheckState(2)
    shortcuts.get_shortcuts()

    pix_dir = tmp_path / "tutorial_images"
    written = {p.name for p in pix_dir.glob("*.png")}
    assert "colorselectdialog-red.png" in written
    assert "colorselectdialog-blue.png" in written
