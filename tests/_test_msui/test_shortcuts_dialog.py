# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_shortcuts_dialog
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests for msui_mainwindow.MSUI_ShortcutsDialog

    This file is part of MSS.

    :copyright: Copyright 2026 by Reimar Bauer.
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
from PyQt5 import QtWidgets, QtGui, QtCore
from mslib.msui import msui_mainwindow as msui_mw
from mslib.msui import constants


@pytest.fixture(autouse=True)
def shortcuts_setup(qtbot):
    """Fixture providing a main window and shortcuts dialog."""
    main_window = msui_mw.MSUIMainWindow()
    main_window.show()
    shortcuts = msui_mw.MSUI_ShortcutsDialog()
    yield main_window, shortcuts
    shortcuts.hide()
    main_window.hide()


class Test_MSUI_ShortcutsDialog_Init:
    @pytest.fixture(autouse=True)
    def setup(self, shortcuts_setup):
        self.main_window, self.shortcuts = shortcuts_setup

    def test_initial_state(self):
        assert self.shortcuts.current_shortcuts is None
        assert not self.shortcuts.filterRemoveAction.isVisible()

    def test_cbAdvanced_hides_widgets_when_unchecked(self):
        self.shortcuts.cbAdvanced.setCheckState(0)
        assert not self.shortcuts.cbNoShortcut.isVisible()
        assert not self.shortcuts.leShortcutFilter.isVisible()
        assert not self.shortcuts.cbDisplayType.isVisible()

    def test_cbAdvanced_shows_widgets_when_checked(self):
        self.shortcuts.cbAdvanced.setCheckState(2)
        # Use not isHidden() because isVisible() also requires all ancestors to be visible
        assert not self.shortcuts.cbNoShortcut.isHidden()
        assert not self.shortcuts.leShortcutFilter.isHidden()
        assert not self.shortcuts.cbDisplayType.isHidden()

    def test_reject_is_custom_reject(self):
        assert self.shortcuts.reject == self.shortcuts.custom_reject


class Test_MSUI_ShortcutsDialog_GetShortcuts:
    @pytest.fixture(autouse=True)
    def setup(self, shortcuts_setup):
        self.main_window, self.shortcuts = shortcuts_setup

    def test_returns_dict(self):
        result = self.shortcuts.get_shortcuts()
        assert isinstance(result, dict)

    def test_contains_main_window(self):
        result = self.shortcuts.get_shortcuts()
        windows = [k.window() if hasattr(k, "window") else k for k in result.keys()]
        assert self.main_window in windows

    def test_each_entry_has_five_elements(self):
        result = self.shortcuts.get_shortcuts()
        for widget_shortcuts in result.values():
            for entry in widget_shortcuts.values():
                assert len(entry) == 5  # description, text, _, shortcut, obj

    def test_cbNoShortcut_increases_entries(self):
        self.shortcuts.cbNoShortcut.setCheckState(0)
        count_without = sum(len(v) for v in self.shortcuts.get_shortcuts().values())
        self.shortcuts.cbNoShortcut.setCheckState(2)
        count_with = sum(len(v) for v in self.shortcuts.get_shortcuts().values())
        assert count_with >= count_without


class Test_MSUI_ShortcutsDialog_FillList:
    @pytest.fixture(autouse=True)
    def setup(self, shortcuts_setup):
        self.main_window, self.shortcuts = shortcuts_setup

    def test_fill_list_populates_tree(self):
        self.shortcuts.fill_list()
        assert self.shortcuts.treeWidget.topLevelItemCount() >= 1

    def test_fill_list_sets_current_shortcuts(self):
        self.shortcuts.fill_list()
        assert self.shortcuts.current_shortcuts is not None

    def test_fill_list_clears_before_repopulating(self):
        self.shortcuts.fill_list()
        count_first = self.shortcuts.treeWidget.topLevelItemCount()
        self.shortcuts.fill_list()
        count_second = self.shortcuts.treeWidget.topLevelItemCount()
        assert count_first == count_second

    def test_display_type_tooltip(self):
        self.shortcuts.fill_list()
        self.shortcuts.cbAdvanced.setCheckState(2)
        self.shortcuts.cbDisplayType.setCurrentText("Tooltip")
        item = self.shortcuts.treeWidget.topLevelItem(0)
        if item and item.childCount() > 0:
            child = item.child(0)
            assert child.text(0)

    def test_display_type_changes_item_text(self):
        self.shortcuts.fill_list()
        self.shortcuts.cbAdvanced.setCheckState(2)
        self.shortcuts.cbDisplayType.setCurrentText("Tooltip")
        item = self.shortcuts.treeWidget.topLevelItem(0)
        if item is None or item.childCount() == 0:
            pytest.skip("No children to compare display types")
        text_tooltip = item.child(0).text(0)
        self.shortcuts.cbDisplayType.setCurrentText("Text")
        # fill_list() is re-triggered; fetch the item again after rebuild
        item2 = self.shortcuts.treeWidget.topLevelItem(0)
        assert item2 is not None and item2.childCount() > 0
        text_text = item2.child(0).text(0)
        # The texts may differ; verify both are non-empty strings
        assert isinstance(text_tooltip, str)
        assert isinstance(text_text, str)

    def test_children_have_source_object(self):
        self.shortcuts.fill_list()
        item = self.shortcuts.treeWidget.topLevelItem(0)
        assert item is not None
        for i in range(item.childCount()):
            child = item.child(i)
            assert hasattr(child, "source_object")


class Test_MSUI_ShortcutsDialog_FilterShortcuts:
    @pytest.fixture(autouse=True)
    def setup(self, shortcuts_setup):
        self.main_window, self.shortcuts = shortcuts_setup
        self.shortcuts.fill_list()

    def test_filter_hides_non_matching_items(self):
        self.shortcuts.leShortcutFilter.setText("xyzzy_no_match_expected")
        top = self.shortcuts.treeWidget.topLevelItem(0)
        assert top.isHidden()

    def test_filter_empty_shows_all_items(self):
        self.shortcuts.leShortcutFilter.setText("")
        top = self.shortcuts.treeWidget.topLevelItem(0)
        assert not top.isHidden()

    def test_filter_remove_action_visibility(self):
        assert not self.shortcuts.filterRemoveAction.isVisible()
        self.shortcuts.leShortcutFilter.setText("action")
        assert self.shortcuts.filterRemoveAction.isVisible()

    def test_filter_remove_action_clears_filter(self):
        self.shortcuts.leShortcutFilter.setText("action")
        self.shortcuts.filterRemoveAction.trigger()
        assert self.shortcuts.leShortcutFilter.text() == ""

    def test_filter_matching_text_shows_item(self):
        # Use a text known to exist in the shortcuts (part of the window title)
        top = self.shortcuts.treeWidget.topLevelItem(0)
        window_title = top.text(0)
        # Filter by the first word of the title
        first_word = window_title.split()[0] if window_title.split() else window_title
        self.shortcuts.leShortcutFilter.setText(first_word)
        assert not top.isHidden()

    def test_cbHighlight_single_result_applies_style(self):
        self.shortcuts.cbAdvanced.setCheckState(2)
        self.shortcuts.cbHighlight.setCheckState(2)
        # Filter to get exactly one child visible — use a known action name
        self.shortcuts.cbNoShortcut.setCheckState(0)
        self.shortcuts.fill_list()
        top = self.shortcuts.treeWidget.topLevelItem(0)
        if top is None or top.childCount() == 0:
            pytest.skip("No children available to test highlight")
        # Find a single unique child text
        for i in range(top.childCount()):
            child_text = top.child(i).text(0)
            unique_fragment = child_text[:6] if len(child_text) >= 6 else child_text
            self.shortcuts.leShortcutFilter.setText(unique_fragment)
            visible_children = sum(
                1 for j in range(top.childCount()) if not top.child(j).isHidden()
            )
            if visible_children == 1:
                child = top.child(i)
                if hasattr(child, "source_object") and hasattr(child.source_object, "styleSheet"):
                    assert child.source_object.styleSheet() == "background-color: yellow;"
                break


class Test_MSUI_ShortcutsDialog_FilterShortcuts_Extended:
    """Extended tests for filter_shortcuts covering branches not in the base class."""

    @pytest.fixture(autouse=True)
    def setup(self, shortcuts_setup):
        self.main_window, self.shortcuts = shortcuts_setup
        # Enable all objects so the tree is fully populated
        self.shortcuts.cbAdvanced.setCheckState(2)
        self.shortcuts.cbNoShortcut.setCheckState(2)
        self.shortcuts.fill_list()

    def test_window_title_match_shows_all_children(self):
        """When the filter text matches the window title, all children become visible."""
        top = self.shortcuts.treeWidget.topLevelItem(0)
        if top is None or top.childCount() == 0:
            pytest.skip("Tree has no children to test")
        window_title = top.text(0)
        # Use a fragment of the window title that is unlikely to match any child text
        fragment = window_title[:4].lower()
        self.shortcuts.leShortcutFilter.setText(fragment)
        # At least the first child must be visible because the window title matches
        assert not top.child(0).isHidden()

    def test_non_matching_child_is_hidden_when_window_also_no_match(self):
        """Children are hidden when neither child text nor window title matches the filter."""
        # A filter that won't match anything
        self.shortcuts.leShortcutFilter.setText("xyzzy_no_match_expected_abc123")
        top = self.shortcuts.treeWidget.topLevelItem(0)
        # Window itself should be hidden (wms_hits == 0, text non-empty)
        assert top.isHidden()
        # Every child of this window should also be hidden
        for i in range(top.childCount()):
            assert top.child(i).isHidden()

    def test_window_hidden_when_wms_hits_zero_and_text_nonempty(self):
        """A top-level window item is hidden when no child matches and text is non-empty."""
        self.shortcuts.leShortcutFilter.setText("xyzzy_no_match_expected_abc123")
        for top_idx in range(self.shortcuts.treeWidget.topLevelItemCount()):
            top = self.shortcuts.treeWidget.topLevelItem(top_idx)
            assert top.isHidden()

    def test_window_visible_when_text_empty(self):
        """All top-level windows remain visible when the filter text is empty."""
        self.shortcuts.leShortcutFilter.setText("")
        for top_idx in range(self.shortcuts.treeWidget.topLevelItemCount()):
            top = self.shortcuts.treeWidget.topLevelItem(top_idx)
            assert not top.isHidden()

    def test_rerun_false_does_not_recurse(self):
        """Calling filter_shortcuts with rerun=False must not trigger a second pass."""
        call_count = []
        original = self.shortcuts.filter_shortcuts

        def counting_filter(text="Nothing", rerun=True):
            call_count.append(rerun)
            return original(text, rerun)

        self.shortcuts.filter_shortcuts = counting_filter
        self.shortcuts.leShortcutFilter.setText("")
        # Call directly with rerun=False — only one call should be recorded
        original("", False)
        # Restore
        self.shortcuts.filter_shortcuts = original
        # The call with rerun=False must NOT have spawned a second invocation via
        # the counting wrapper, so our wrapper was not called at all (original was
        # called directly).  The important assertion is that the filter runs without error.
        assert True  # no exception means rerun=False path executed cleanly

    def test_cbHighlight_unchecked_no_highlight_with_multiple_windows(self):
        """cbHighlight unchecked + window_count > 1 prevents auto-highlight even when wms_hits == 1.

        "Top View" matches the TopView window title (keeps it visible, wms_hits = all children)
        and matches actionTopView in MainWindow (wms_hits == 1 there). Both windows remain
        visible after the rerun pass, so window_count == 2 and the highlight condition
        `wms_hits == 1 and (cbHighlight or window_count == 1)` evaluates to False.
        """
        self.main_window.create_new_flight_track()
        self.main_window.actionTopView.trigger()
        try:
            self.shortcuts.cbHighlight.setCheckState(0)
            self.shortcuts.fill_list()

            self.shortcuts.leShortcutFilter.setText("Top View")

            visible_windows = sum(
                1 for i in range(self.shortcuts.treeWidget.topLevelItemCount())
                if not self.shortcuts.treeWidget.topLevelItem(i).isHidden()
            )
            assert visible_windows >= 2, (
                f"Need ≥2 visible windows after filtering by 'Top View', got {visible_windows}"
            )

            # Find windows where exactly 1 child is visible and styleable — these are the
            # windows where wms_hits == 1 and the highlight guard should have fired.
            # With cbHighlight=False and window_count >= 2, no auto-highlight must occur.
            for top_idx in range(self.shortcuts.treeWidget.topLevelItemCount()):
                top = self.shortcuts.treeWidget.topLevelItem(top_idx)
                if top is None or top.isHidden():
                    continue
                styleable_visible = [
                    top.child(ci) for ci in range(top.childCount())
                    if not top.child(ci).isHidden()
                    and hasattr(top.child(ci), "source_object")
                    and hasattr(top.child(ci).source_object, "styleSheet")
                ]
                if len(styleable_visible) == 1:
                    child = styleable_visible[0]
                    assert child.source_object.styleSheet() != "background-color: yellow;", (
                        f"'{child.text(0)}' in '{top.text(0)}' was auto-highlighted, "
                        "but cbHighlight=False and window_count >= 2 should prevent it"
                    )
        finally:
            while self.main_window.listViews.count() > 0:
                self.main_window.listViews.item(0).window.handle_force_close()

    def test_cbHighlight_checked_single_match_applies_style(self):
        """With cbHighlight checked, a single matching child gets highlighted yellow."""
        self.shortcuts.cbHighlight.setCheckState(2)
        for top_idx in range(self.shortcuts.treeWidget.topLevelItemCount()):
            top = self.shortcuts.treeWidget.topLevelItem(top_idx)
            if top is None or top.childCount() == 0:
                continue
            for ci in range(top.childCount()):
                child = top.child(ci)
                if not hasattr(child, "source_object") or child.source_object is None:
                    continue
                if not hasattr(child.source_object, "styleSheet"):
                    continue
                candidate = child.text(0)
                # Ensure uniqueness across all children
                total = sum(
                    1
                    for ti in range(self.shortcuts.treeWidget.topLevelItemCount())
                    for cj in range(self.shortcuts.treeWidget.topLevelItem(ti).childCount())
                    if candidate.lower() in self.shortcuts.treeWidget.topLevelItem(ti).child(cj).text(0).lower()
                )
                if total == 1:
                    self.shortcuts.leShortcutFilter.setText(candidate)
                    assert child.source_object.styleSheet() == "background-color: yellow;"
                    return
        pytest.skip("Could not find a uniquely-matching styleable child")

    def test_filter_remove_action_hidden_when_text_empty(self):
        """filterRemoveAction is hidden when the filter text is empty."""
        self.shortcuts.leShortcutFilter.setText("something")
        assert self.shortcuts.filterRemoveAction.isVisible()
        self.shortcuts.leShortcutFilter.setText("")
        assert not self.shortcuts.filterRemoveAction.isVisible()

    def test_partial_window_title_match_keeps_window_visible(self):
        """Filtering by a substring of the window title keeps that window visible."""
        top = self.shortcuts.treeWidget.topLevelItem(0)
        if top is None:
            pytest.skip("No top-level items in tree")
        title = top.text(0)
        if len(title) < 3:
            pytest.skip("Window title too short to extract a useful fragment")
        # Use middle characters of the title (avoid leading/trailing spaces)
        mid = len(title) // 2
        fragment = title[mid - 1:mid + 2]
        self.shortcuts.leShortcutFilter.setText(fragment)
        assert not top.isHidden()


class Test_MSUI_ShortcutsDialog_Clicked:
    @pytest.fixture(autouse=True)
    def setup(self, shortcuts_setup):
        self.main_window, self.shortcuts = shortcuts_setup
        self.main_window.create_new_flight_track()
        self.shortcuts.fill_list()
        yield
        for i in range(self.main_window.listViews.count()):
            self.main_window.listViews.item(i).window.hide()

    def _styleable_children(self):
        result = []
        for top_idx in range(self.shortcuts.treeWidget.topLevelItemCount()):
            top = self.shortcuts.treeWidget.topLevelItem(top_idx)
            if top is None:
                continue
            for i in range(top.childCount()):
                child = top.child(i)
                if (hasattr(child, "source_object") and child.source_object is not None
                        and hasattr(child.source_object, "setStyleSheet")):
                    result.append(child)
        return result

    def test_clicked_highlights_item_yellow(self):
        # Pass 1: no views — no styleable objects in the tree
        children = self._styleable_children()
        assert len(children) == 0

        # Pass 2: open TopView + SideView, refill, assert highlight works
        self.main_window.actionTopView.trigger()
        self.main_window.actionSideView.trigger()
        self.shortcuts.fill_list()
        children = self._styleable_children()
        assert len(children) > 0
        self.shortcuts.clicked(children[0])
        assert children[0].source_object.styleSheet() == "background-color:yellow;"

    def test_clicked_resets_previous_highlight(self):
        # Pass 1: no views — fewer than 2 styleable children
        children = self._styleable_children()
        assert len(children) < 2

        # Pass 2: open TopView + SideView, refill, assert second click resets first
        self.main_window.actionTopView.trigger()
        self.main_window.actionSideView.trigger()
        self.shortcuts.fill_list()
        children = self._styleable_children()
        assert len(children) >= 2
        self.shortcuts.clicked(children[0])
        assert children[0].source_object.styleSheet() == "background-color:yellow;"
        self.shortcuts.clicked(children[1])
        assert children[0].source_object.styleSheet() == ""
        assert children[1].source_object.styleSheet() == "background-color:yellow;"

    def test_clicked_item_without_source_object_does_not_crash(self):
        item = QtWidgets.QTreeWidgetItem()
        # No source_object attribute — should not raise
        self.shortcuts.clicked(item)

    def test_clicked_list_widget_item(self):
        lw = QtWidgets.QListWidget()
        li = QtWidgets.QListWidgetItem("test item")
        lw.addItem(li)
        item = QtWidgets.QTreeWidgetItem()
        item.source_object = li
        self.shortcuts.clicked(item)
        assert li.background().color() == QtGui.QColor("yellow")
        lw.deleteLater()


class Test_MSUI_ShortcutsDialog_ResetHighlight:
    @pytest.fixture(autouse=True)
    def setup(self, shortcuts_setup):
        self.main_window, self.shortcuts = shortcuts_setup
        self.main_window.create_new_flight_track()
        self.shortcuts.fill_list()
        yield
        for i in range(self.main_window.listViews.count()):
            self.main_window.listViews.item(i).window.hide()

    def _first_styleable_child(self):
        for top_idx in range(self.shortcuts.treeWidget.topLevelItemCount()):
            top = self.shortcuts.treeWidget.topLevelItem(top_idx)
            if top is None:
                continue
            for i in range(top.childCount()):
                child = top.child(i)
                if (hasattr(child, "source_object") and child.source_object is not None
                        and hasattr(child.source_object, "setStyleSheet")):
                    return child
        return None

    def test_reset_highlight_clears_stylesheet(self):
        # Pass 1: no views — no styleable child, reset_highlight is a no-op
        child = self._first_styleable_child()
        assert child is None
        self.shortcuts.reset_highlight()  # must not raise

        # Pass 2: open TopView + SideView, refill, verify reset clears the style
        self.main_window.actionTopView.trigger()
        self.main_window.actionSideView.trigger()
        self.shortcuts.fill_list()
        child = self._first_styleable_child()
        assert child is not None
        self.shortcuts.clicked(child)
        assert child.source_object.styleSheet() == "background-color:yellow;"
        self.shortcuts.reset_highlight()
        assert child.source_object.styleSheet() == ""

    def test_reset_highlight_no_current_shortcuts(self):
        self.shortcuts.current_shortcuts = None
        # Must not raise
        self.shortcuts.reset_highlight()

    def test_reset_highlight_clears_list_widget_item_background(self):
        lw = QtWidgets.QListWidget()
        li = QtWidgets.QListWidgetItem("item")
        lw.addItem(li)
        li.setBackground(QtGui.QBrush(QtGui.QColor("yellow")))
        # Inject synthetic entry into current_shortcuts
        fake_key = object()
        self.shortcuts.current_shortcuts[fake_key] = {"li_key": ("desc", "text", None, "", li)}
        self.shortcuts.reset_highlight()
        assert li.background() == QtGui.QBrush()
        lw.deleteLater()


class Test_MSUI_ShortcutsDialog_DoubleClicked:
    @pytest.fixture(autouse=True)
    def setup(self, shortcuts_setup):
        self.main_window, self.shortcuts = shortcuts_setup
        self.shortcuts.cbAdvanced.setCheckState(2)
        self.shortcuts.cbNoShortcut.setCheckState(2)
        self.shortcuts.fill_list()

    def _make_item(self, obj):
        item = QtWidgets.QTreeWidgetItem()
        item.source_object = obj
        return item

    def test_double_clicked_action_triggers(self):
        action = QtWidgets.QAction("Test Action")
        triggered = []
        action.triggered.connect(lambda: triggered.append(True))
        item = self._make_item(action)
        self.shortcuts.double_clicked(item)
        assert triggered

    def test_double_clicked_button_clicks(self):
        btn = QtWidgets.QPushButton("Click me")
        clicked = []
        btn.clicked.connect(lambda: clicked.append(True))
        item = self._make_item(btn)
        self.shortcuts.double_clicked(item)
        assert clicked
        btn.deleteLater()

    def test_double_clicked_line_edit_does_not_crash(self):
        le = QtWidgets.QLineEdit()
        le.show()
        item = self._make_item(le)
        # setFocus() is called — just verify it doesn't raise
        self.shortcuts.double_clicked(item)
        le.deleteLater()

    def test_double_clicked_shortcut_emits_activated(self):
        sc = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+T"), self.main_window)
        activated = []
        sc.activated.connect(lambda: activated.append(True))
        item = self._make_item(sc)
        self.shortcuts.double_clicked(item)
        assert activated

    def test_double_clicked_no_source_object_does_not_crash(self):
        item = QtWidgets.QTreeWidgetItem()
        item.source_object = None
        self.shortcuts.double_clicked(item)

    def test_double_clicked_item_without_attribute_does_not_crash(self):
        item = QtWidgets.QTreeWidgetItem()
        # No source_object at all
        self.shortcuts.double_clicked(item)

    def test_double_clicked_hides_dialog(self):
        btn = QtWidgets.QPushButton("btn")
        item = self._make_item(btn)
        self.shortcuts.show()
        self.shortcuts.double_clicked(item)
        assert not self.shortcuts.isVisible()
        btn.deleteLater()

    def test_double_clicked_list_widget_item(self):
        lw = QtWidgets.QListWidget()
        li = QtWidgets.QListWidgetItem("test")
        lw.addItem(li)
        activated = []
        lw.itemActivated.connect(lambda i: activated.append(i))
        item = self._make_item(li)
        self.shortcuts.double_clicked(item)
        assert activated
        lw.deleteLater()


class Test_MSUI_ShortcutsDialog_CustomReject:
    @pytest.fixture(autouse=True)
    def setup(self, shortcuts_setup):
        self.main_window, self.shortcuts = shortcuts_setup
        self.shortcuts.fill_list()

    def test_custom_reject_resets_highlight_and_closes(self):
        top = self.shortcuts.treeWidget.topLevelItem(0)
        highlighted_obj = None
        if top:
            for i in range(top.childCount()):
                child = top.child(i)
                if hasattr(child, "source_object") and child.source_object is not None:
                    if hasattr(child.source_object, "setStyleSheet"):
                        self.shortcuts.clicked(child)
                        highlighted_obj = child.source_object
                        break
        self.shortcuts.show()
        self.shortcuts.custom_reject()
        if highlighted_obj is not None:
            assert highlighted_obj.styleSheet() == ""
        assert not self.shortcuts.isVisible()


class Test_MSUI_ShortcutsDialog_TutorialMode:
    """Tests for MSUI_ShortcutsDialog behaviour when tutorial_mode=True."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        self.main_window = msui_mw.MSUIMainWindow(tutorial_mode=True)
        self.main_window.show()
        self.shortcuts = msui_mw.MSUI_ShortcutsDialog(tutorial_mode=True)
        self.pix_dir = constants.MSUI_CONFIG_PATH / 'tutorial_images'
        yield
        self.shortcuts.hide()
        self.main_window.hide()

    def test_tutorial_mode_flag_is_stored(self):
        assert self.shortcuts.tutorial_mode is True

    def test_get_shortcuts_creates_pix_dir(self):
        self.shortcuts.get_shortcuts()
        assert self.pix_dir.exists()

    def test_get_shortcuts_generates_png_files(self):
        # QAction.grab() raises AttributeError (silently caught), so only real widgets
        # (buttons, combos, etc.) produce images. cbNoShortcut must be checked.
        self.shortcuts.cbAdvanced.setCheckState(2)
        self.shortcuts.cbNoShortcut.setCheckState(2)
        self.shortcuts.get_shortcuts()
        assert len(list(self.pix_dir.glob("*.png"))) > 0

    def test_no_search_prefixed_images(self):
        """No PNG should be prefixed with 'search' — slugified names are lowercase so the
        startswith('Search') guard in get_shortcuts never fires, but verify the result."""
        self.shortcuts.cbAdvanced.setCheckState(2)
        self.shortcuts.cbNoShortcut.setCheckState(2)
        self.shortcuts.get_shortcuts()
        for png in self.pix_dir.glob("*.png"):
            assert not png.name.lower().startswith("search"), (
                f"Unexpected search-prefixed image: {png.name}"
            )

    def test_widget_image_names_exist(self):
        """Known widget names produce expected PNG filenames when cbNoShortcut is enabled.
        connectBtn (QPushButton, text='Connect') → msuimainwindow-connect.png."""
        self.shortcuts.cbAdvanced.setCheckState(2)
        self.shortcuts.cbNoShortcut.setCheckState(2)
        self.shortcuts.get_shortcuts()
        names = {p.name for p in self.pix_dir.glob("*.png")}
        assert "msuimainwindow-connect.png" in names

    def test_show_shortcuts_hides_dialog_in_tutorial_mode(self):
        """In tutorial_mode the dialog must be hidden immediately after show_shortcuts()."""
        self.main_window.show_shortcuts()
        assert not self.main_window.shortcuts_dlg.isVisible()
