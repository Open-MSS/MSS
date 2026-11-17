# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_change_signals
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    After each change of a flight track all views show the current data, and each costly update of
    the views happens at most once: the WMS requests of the side and linear views, the redraws of
    the top view and of the x-axis of the side view.

    This file is part of MSS.

    :copyright: Copyright 2026 by the MSS team, see AUTHORS.
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
import contextlib
import datetime
import json

import mock
import numpy as np
import pytest

from PyQt5 import QtCore, QtGui, QtTest, QtWidgets

from mslib.msui import flighttrack as ft
from mslib.msui import msui, linearview, sideview, tableview, topview
from mslib.msui.aircraft import AIRCRAFT_DUMMY, SimpleAircraft


COMMENTS = len(ft.TABLE_FULL) - 1

# the waypoint data each plot shows
SHOWN = {
    "top": ("lat", "lon", "location"),
    "side": ("lat", "lon", "flightlevel", "pressure", "location", "utc_time"),
    "linear": ("lat", "lon", "flightlevel", "pressure"),
}


def _set(column, value):
    return lambda model: model.setData(model.index(1, column), value)


def _set_performance(model):
    model.set_performance_settings(dict(model.performance_settings, fuel=1000))


def _replace(model):
    model.replace_waypoints([ft.Waypoint(5., 5., 100.), ft.Waypoint(6., 6., 200.), ft.Waypoint(7., 7., 300.)])


def _shown(plot, waypoints):
    return [tuple(getattr(waypoint, name) for name in SHOWN[plot]) for waypoint in waypoints]


# Changes of the flight track model, and the costly updates each view does for them.
CHANGES = [
    ("lat", (_set(ft.LAT, 1.5), {"top": 1, "vsec": 1, "xaxis": 1, "lsec": 1})),
    ("lon", (_set(ft.LON, 1.5), {"top": 1, "vsec": 1, "xaxis": 1, "lsec": 1})),
    ("flightlevel", (_set(ft.FLIGHTLEVEL, 300), {"top": 1, "vsec": 0, "xaxis": 1, "lsec": 1})),
    ("pressure", (_set(ft.PRESSURE, 250), {"top": 1, "vsec": 0, "xaxis": 1, "lsec": 1})),
    ("location", (_set(ft.LOCATION, "Somewhere"), {"top": 1, "vsec": 0, "xaxis": 0, "lsec": 0})),
    ("comments", (_set(COMMENTS, "a comment"), {"top": 0, "vsec": 0, "xaxis": 0, "lsec": 0})),
    ("time", (_set(ft.TIME_UTC, "2030-01-01 12:00:00"), {"top": 0, "vsec": 0, "xaxis": 1, "lsec": 0})),
    ("insert", (lambda model: model.insertRows(1), {"top": 1, "vsec": 1, "xaxis": 1, "lsec": 1})),
    ("remove", (lambda model: model.removeRows(1), {"top": 1, "vsec": 1, "xaxis": 1, "lsec": 1})),
    ("invert", (lambda model: model.invert_direction(), {"top": 1, "vsec": 1, "xaxis": 1, "lsec": 1})),
    ("replace", (_replace, {"top": 1, "vsec": 1, "xaxis": 1, "lsec": 1})),
    ("performance", (_set_performance, {"top": 0, "vsec": 0, "xaxis": 1, "lsec": 0})),
]


class PaintedRegion(QtCore.QObject):
    """
    The region of a widget painted since the start.
    """

    def __init__(self, widget):
        super().__init__()
        self.region = QtGui.QRegion()
        widget.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Paint:
            self.region = self.region.united(event.region())
        return False


class Test_ChangeSignalsOfViews:
    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        self.qtbot = qtbot
        self.window = msui.MSUIMainWindow()
        self.window.create_new_flight_track()
        self.model = self.window.active_flight_track
        # the views are opened on another flight track, so that the switch moves their connections
        self.window.create_new_flight_track()
        self.other = self.window.active_flight_track
        self.window.show()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        for action in (self.window.actionTopView, self.window.actionSideView, self.window.actionLinearView,
                       self.window.actionTableView):
            action.trigger()
        views = {view.name: view for view in
                 (self.window.listViews.item(i).window for i in range(self.window.listViews.count()))}
        self.window.activate_flight_track(self.window.listFlightTracks.item(0))
        assert self.window.active_flight_track is self.model
        # a flight track keeps at least two waypoints, also after removing one
        self.model.insertRows(1, waypoints=[ft.Waypoint(50., 10., 200.)])
        self.table = views["Table View"].tableWayPoints
        views["Table View"].resize(3000, 400)
        self.top, self.side, self.linear = [
            views[name].mpl.canvas for name in ("Top View", "Side View", "Linear View")]
        qtbot.wait(100)
        yield
        for view in views.values():
            view.hide()
        self.window.hide()

    @pytest.fixture
    def calls(self):
        """
        Count the costly updates of the views.
        """
        counts = dict.fromkeys(("top", "vsec", "xaxis", "lsec"), 0)

        def count(name):
            def inc(*args, **kwargs):
                counts[name] += 1
            return inc

        self.side.waypoints_interactor.signal_get_vsec.connect(count("vsec"))
        self.linear.waypoints_interactor.signal_get_lsec.connect(count("lsec"))
        top_plotter = self.top.waypoints_interactor.plotter
        side_plotter = self.side.plotter
        with mock.patch.object(top_plotter, "redraw_path", side_effect=count("top")), \
                mock.patch.object(side_plotter, "redraw_xaxis", side_effect=count("xaxis")), \
                mock.patch("mslib.msui.flighttrack.save_settings_qsettings"):
            yield counts

    @pytest.fixture
    def plots(self):
        """
        The waypoint data each plot got last.
        """
        shown = {plot: _shown(plot, self.model.waypoints) for plot in SHOWN}

        def spy(plot, update_from_waypoints):
            def update(waypoints, *args, **kwargs):
                shown[plot] = _shown(plot, waypoints)
                return update_from_waypoints(waypoints, *args, **kwargs)
            return update

        plotters = {"top": self.top.waypoints_interactor.plotter, "side": self.side.waypoints_interactor.plotter,
                    "linear": self.linear.waypoints_interactor.plotter}
        patches = [mock.patch.object(plotter, "update_from_waypoints",
                                     side_effect=spy(plot, plotter.update_from_waypoints))
                   for plot, plotter in plotters.items()]
        for patch in patches:
            patch.start()
        yield shown
        for patch in patches:
            patch.stop()

    def _table_texts(self):
        model = self.model
        return [[model.data(model.index(row, column)).value() for column in range(model.columnCount())]
                for row in range(model.rowCount())]

    @pytest.mark.parametrize("change, expected", [change for _, change in CHANGES], ids=[i for i, _ in CHANGES])
    def test_views_are_updated_once(self, calls, plots, change, expected):
        before = self._table_texts()
        painted = PaintedRegion(self.table.viewport())
        change(self.model)
        self.qtbot.wait(100)

        assert calls == expected
        for plot in SHOWN:
            assert plots[plot] == _shown(plot, self.model.waypoints), plot
        # each table cell with a new text is repainted
        viewport = self.table.viewport().rect()
        for row, texts in enumerate(self._table_texts()):
            for column, text in enumerate(texts):
                if row >= len(before) or before[row][column] != text:
                    rect = self.table.visualRect(self.model.index(row, column))
                    assert viewport.contains(rect), (row, column)
                    assert painted.region.contains(rect), (row, column)

    def test_inactive_flight_track_updates_no_view(self, calls):
        self.other.setData(self.other.index(1, ft.LAT), 1.5)
        self.other.insertRows(1)
        assert calls == {"top": 0, "vsec": 0, "xaxis": 0, "lsec": 0}

    @pytest.mark.parametrize("column, value", [(ft.FLIGHTLEVEL, 350), (ft.PRESSURE, 240)],
                             ids=["flightlevel", "pressure"])
    def test_side_view_shows_times_after_altitude_change(self, column, value):
        # an aircraft that is faster at higher altitudes, so the altitude changes the times
        climb = [[weight, altitude, altitude / 1000, altitude / 200, altitude / 20]
                 for weight in (80000, 95000) for altitude in (0, 40000)]
        aircraft = SimpleAircraft({
            "name": "TEST", "takeoff_weight": 91000, "empty_weight": 56000, "climb": climb, "descent": climb,
            "cruise": [[weight, altitude, 380 + altitude / 400, 3000]
                       for weight in (80000, 95000) for altitude in (20000, 40000)]})
        with mock.patch("mslib.msui.flighttrack.save_settings_qsettings"):
            self.model.set_performance_settings(dict(self.model.performance_settings, aircraft=aircraft))

        def labels():
            return [label.get_text() for label in self.side.plotter.ax.get_xticklabels()]

        before = labels()
        self.model.setData(self.model.index(1, column), value)
        after = labels()
        # what a complete redraw of the x-axis shows
        self.side.waypoints_interactor.qt_performance_data_changed_listener()
        assert after == labels() != before

    def test_top_view_redraws_for_time_with_solar_angle(self, calls):
        self.top.waypoints_interactor.plotter.show_solar_angle = ("sun", "angle")
        _set(ft.TIME_UTC, "2030-01-01 12:00:00")(self.model)
        assert calls == {"top": 1, "vsec": 0, "xaxis": 1, "lsec": 0}


def _edit(column, *texts):
    """
    Edits a cell of row 1 (0 for the fuel) in the table view, as the user does; the text by the view.
    """
    def change(test, table, which):
        text = texts[which]
        model = test.model
        index = model.index(0 if column == ft.REM_FUEL else 1, column)
        delegate = table.tableWayPoints.itemDelegate()
        editor = delegate.createEditor(table.tableWayPoints, QtWidgets.QStyleOptionViewItem(), index)
        delegate.setEditorData(editor, index)
        if isinstance(editor, QtWidgets.QDateTimeEdit):
            editor.setDateTime(ft.utc_qdatetime(datetime.datetime.strptime(text, "%Y-%m-%d %H:%M:%S")))
        elif isinstance(editor, QtWidgets.QComboBox):
            editor.setCurrentText(text)
        else:
            editor.setText(text)
        delegate.setModelData(editor, model, index)
    return change


def _drag(test, window, which):
    """
    Drags waypoint 1 in a top or side view with the mouse.
    """
    canvas = window.mpl.canvas
    interactor = canvas.waypoints_interactor
    path = interactor.plotter.pathpatch.get_path()
    vertices = np.asarray(path.wp_vertices if hasattr(path, "wp_vertices") else path.vertices)
    x, y = interactor.plotter.pathpatch.get_transform().transform(vertices[1])
    ratio = canvas.devicePixelRatioF()
    start = QtCore.QPoint(round(x / ratio), round(canvas.height() - y / ratio))
    assert canvas.rect().contains(start), start
    end = start + QtCore.QPoint(15, -15)
    window.mpl.navbar._actions["move_wp"].trigger()
    QtTest.QTest.mousePress(canvas, QtCore.Qt.LeftButton, pos=start)
    # QTest.mouseMove moves without a button held, i.e. no drag
    QtWidgets.QApplication.sendEvent(canvas, QtGui.QMouseEvent(
        QtCore.QEvent.MouseMove, QtCore.QPointF(end), QtCore.Qt.NoButton, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier))
    QtTest.QTest.mouseRelease(canvas, QtCore.Qt.LeftButton, pos=end)


def _load_aircraft(test, table, which):
    filename = test.aircraft_file.with_name(f"other{which}.json")
    filename.write_text(json.dumps(dict(AIRCRAFT_DUMMY, name=f"OTHER{which}", takeoff_weight=80000 + which,
                                        empty_weight=50000 + which)))
    with mock.patch("mslib.msui.performance_settings.get_open_filename", return_value=str(filename)):
        QtTest.QTest.mouseClick(table.docks[1].widget().pbLoadPerformance, QtCore.Qt.LeftButton)


def _empty_weight(test, table, which):
    box = table.docks[1].widget().dsbEmptyWeight
    box.setValue(box.value() + 1000)


@mock.patch("PyQt5.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.Yes)
def _hexagon(test, table, which, mockbox):
    QtTest.QTest.mouseClick(table.docks[0].widget().pbAddHexagon, QtCore.Qt.LeftButton)


# Changes made in one view: which kind of view, the change, the costly updates each view does for it.
VIEW_CHANGES = [
    ("table-lat", ("table", _edit(ft.LAT, "1.5", "2.5"), {"top": 1, "vsec": 1, "xaxis": 1, "lsec": 1})),
    ("table-flightlevel", ("table", _edit(ft.FLIGHTLEVEL, "300", "310"), {"top": 1, "vsec": 0, "xaxis": 1, "lsec": 1})),
    ("table-location", ("table", _edit(ft.LOCATION, "Somewhere", "Elsewhere"),
                        {"top": 1, "vsec": 0, "xaxis": 0, "lsec": 0})),
    ("table-time", ("table", _edit(ft.TIME_UTC, "2030-01-01 12:00:00", "2030-01-01 13:00:00"),
                    {"top": 0, "vsec": 0, "xaxis": 1, "lsec": 0})),
    ("table-fuel", ("table", _edit(ft.REM_FUEL, "20000", "21000"), {"top": 0, "vsec": 0, "xaxis": 1, "lsec": 0})),
    ("table-aircraft", ("table", _load_aircraft, {"top": 0, "vsec": 0, "xaxis": 1, "lsec": 0})),
    ("table-empty-weight", ("table", _empty_weight, {"top": 0, "vsec": 0, "xaxis": 1, "lsec": 0})),
    ("table-hexagon", ("table", _hexagon, {"top": 1, "vsec": 1, "xaxis": 1, "lsec": 1})),
    ("top-drag", ("top", _drag, {"top": 1, "vsec": 1, "xaxis": 1, "lsec": 1})),
    ("side-drag", ("side", _drag, {"top": 1, "vsec": 0, "xaxis": 1, "lsec": 1})),
]


class Test_SeveralViewsOfOneFlightTrack:
    """
    Two views of each kind show the active flight track, the table views with their performance
    settings and hexagon docks. Whatever changes the flight track, directly or in any one of the
    views, all views and docks show the result, and each view does its costly updates once.
    """

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, tmp_path):
        self.qtbot = qtbot
        self.window = msui.MSUIMainWindow()
        self.window.create_new_flight_track()
        self.model = self.window.active_flight_track
        # the views are opened on another flight track, so that the switch moves their connections
        self.window.create_new_flight_track()
        self.window.show()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        for action in (self.window.actionTopView, self.window.actionSideView, self.window.actionLinearView,
                       self.window.actionTableView):
            action.trigger()
            action.trigger()
        windows = [self.window.listViews.item(i).window for i in range(self.window.listViews.count())]
        self.views = {kind: [window for window in windows if isinstance(window, cls)] for kind, cls in (
            ("top", topview.MSUITopViewWindow), ("side", sideview.MSUISideViewWindow),
            ("linear", linearview.MSUILinearViewWindow), ("table", tableview.MSUITableViewWindow))}
        assert all(len(views) == 2 for views in self.views.values()), self.views
        for table in self.views["table"]:
            table.cbTools.currentIndexChanged.emit(1)
            table.cbTools.currentIndexChanged.emit(2)
            table.resize(3000, 1200)
        self.window.activate_flight_track(self.window.listFlightTracks.item(0))
        assert self.window.active_flight_track is self.model
        self.model.insertRows(1, waypoints=[ft.Waypoint(50., 10., 200.)])
        self.aircraft_file = tmp_path / "other.json"
        qtbot.wait(100)
        yield
        for views in self.views.values():
            for view in views:
                view.hide()
        self.window.hide()

    @pytest.fixture
    def calls(self):
        """
        Count the costly updates of each view.
        """
        counts = {}

        def count(key):
            counts[key] = 0

            def inc(*args, **kwargs):
                counts[key] += 1
            return inc

        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch("mslib.msui.flighttrack.save_settings_qsettings"))
            for i, view in enumerate(self.views["top"]):
                stack.enter_context(mock.patch.object(view.mpl.canvas.waypoints_interactor.plotter, "redraw_path",
                                                      side_effect=count(("top", i))))
            for i, view in enumerate(self.views["side"]):
                view.mpl.canvas.waypoints_interactor.signal_get_vsec.connect(count(("vsec", i)))
                stack.enter_context(mock.patch.object(view.mpl.canvas.plotter, "redraw_xaxis",
                                                      side_effect=count(("xaxis", i))))
            for i, view in enumerate(self.views["linear"]):
                view.mpl.canvas.waypoints_interactor.signal_get_lsec.connect(count(("lsec", i)))
            yield counts

    @pytest.fixture
    def plots(self):
        """
        The waypoint data each plot got last.
        """
        plotters = {(kind, i): view.mpl.canvas.waypoints_interactor.plotter
                    for kind in SHOWN for i, view in enumerate(self.views[kind])}
        shown = {key: _shown(key[0], self.model.waypoints) for key in plotters}

        def spy(key, update_from_waypoints):
            def update(waypoints, *args, **kwargs):
                shown[key] = _shown(key[0], waypoints)
                return update_from_waypoints(waypoints, *args, **kwargs)
            return update

        with contextlib.ExitStack() as stack:
            for key, plotter in plotters.items():
                stack.enter_context(mock.patch.object(plotter, "update_from_waypoints",
                                                      side_effect=spy(key, plotter.update_from_waypoints)))
            yield shown

    def _table_texts(self):
        model = self.model
        return [[model.data(model.index(row, column)).value() for column in range(model.columnCount())]
                for row in range(model.rowCount())]

    def _check(self, step, change, calls, plots, expected, extra=None):
        """
        Makes the change and checks that all views and docks show its result, each costly update done once.

        extra -- further updates of single views, e.g. a dragged view follows the mouse
        """
        for counter in calls:
            calls[counter] = 0
        before = self._table_texts()
        painted = [PaintedRegion(table.tableWayPoints.viewport()) for table in self.views["table"]]
        change()
        self.qtbot.wait(100)

        expected_calls = {(kind, i): count for kind, count in expected.items() for i in range(2)}
        for key, count in (extra or {}).items():
            expected_calls[key] += count
        assert calls == expected_calls, step
        for key in plots:
            assert plots[key] == _shown(key[0], self.model.waypoints), (step, key)
        for table, region in zip(self.views["table"], painted):
            viewport = table.tableWayPoints.viewport().rect()
            for row, texts in enumerate(self._table_texts()):
                for column, text in enumerate(texts):
                    if row >= len(before) or before[row][column] != text:
                        rect = table.tableWayPoints.visualRect(self.model.index(row, column))
                        assert viewport.contains(rect), (step, row, column)
                        assert region.region.contains(rect), (step, row, column)
            dock = table.docks[1].widget()
            settings = self.model.performance_settings
            assert dock.lbAircraftName.text() == settings["aircraft"].name, step
            assert dock.dsbEmptyWeight.value() == settings["empty_weight"], step

    # The changes are made one after the other, the views are costly to open.

    def test_views_are_updated_once(self, calls, plots):
        for step, (change, expected) in CHANGES:
            self._check(step, lambda: change(self.model), calls, plots, expected)

    def test_change_in_one_view(self, calls, plots):
        """
        A change made in the first or the second view of a kind reaches all views alike.
        """
        for step, (kind, change, expected) in VIEW_CHANGES:
            for which in range(2):
                before = ([(waypoint.lat, waypoint.lon, waypoint.flightlevel, waypoint.location)
                           for waypoint in self.model.waypoints], dict(self.model.performance_settings))
                # the dragged top view redraws its path for the one mouse move as well
                extra = {("top", which): 1} if change is _drag and kind == "top" else None
                self._check((step, which), lambda: change(self, self.views[kind][which], which), calls, plots,
                            expected, extra)
                after = ([(waypoint.lat, waypoint.lon, waypoint.flightlevel, waypoint.location)
                          for waypoint in self.model.waypoints], self.model.performance_settings)
                # the change was made, in the second view too
                assert after != before, (step, which)

    def test_views_follow_the_active_flight_track(self, calls, plots):
        """
        Switching the flight track and back leaves every view connected once.
        """
        self.window.activate_flight_track(self.window.listFlightTracks.item(1))
        self.window.activate_flight_track(self.window.listFlightTracks.item(0))
        self._check("switch", lambda: _set(ft.LAT, 2.5)(self.model), calls, plots,
                    {"top": 1, "vsec": 1, "xaxis": 1, "lsec": 1})
