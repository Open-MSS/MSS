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
import mock
import pytest

from PyQt5 import QtCore, QtGui, QtTest

from mslib.msui import flighttrack as ft
from mslib.msui import msui
from mslib.msui.aircraft import SimpleAircraft


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
    model.set_performance_settings(dict(model.performance_settings, takeoff_weight=1000))


def _replace(model):
    model.replace_waypoints([ft.Waypoint(5., 5., 100.), ft.Waypoint(6., 6., 200.), ft.Waypoint(7., 7., 300.)])


def _shown(plot, waypoints):
    return [tuple(getattr(waypoint, name) for name in SHOWN[plot]) for waypoint in waypoints]


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

    @pytest.mark.parametrize("change, expected", [
        (_set(ft.LAT, 1.5), {"top": 1, "vsec": 1, "xaxis": 1, "lsec": 1}),
        (_set(ft.LON, 1.5), {"top": 1, "vsec": 1, "xaxis": 1, "lsec": 1}),
        (_set(ft.FLIGHTLEVEL, 300), {"top": 1, "vsec": 0, "xaxis": 1, "lsec": 1}),
        (_set(ft.PRESSURE, 250), {"top": 1, "vsec": 0, "xaxis": 1, "lsec": 1}),
        (_set(ft.LOCATION, "Somewhere"), {"top": 1, "vsec": 0, "xaxis": 0, "lsec": 0}),
        (_set(COMMENTS, "a comment"), {"top": 0, "vsec": 0, "xaxis": 0, "lsec": 0}),
        (_set(ft.TIME_UTC, "2030-01-01 12:00:00"), {"top": 0, "vsec": 0, "xaxis": 1, "lsec": 0}),
        (lambda model: model.insertRows(1), {"top": 1, "vsec": 1, "xaxis": 1, "lsec": 1}),
        (lambda model: model.removeRows(1), {"top": 1, "vsec": 1, "xaxis": 1, "lsec": 1}),
        (lambda model: model.invert_direction(), {"top": 1, "vsec": 1, "xaxis": 1, "lsec": 1}),
        (_replace, {"top": 1, "vsec": 1, "xaxis": 1, "lsec": 1}),
        (_set_performance, {"top": 0, "vsec": 0, "xaxis": 1, "lsec": 0}),
    ], ids=["lat", "lon", "flightlevel", "pressure", "location", "comments", "time", "insert", "remove",
            "invert", "replace", "performance"])
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
