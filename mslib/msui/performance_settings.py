# -*- coding: utf-8 -*-
"""

    mslib.msui.performance_settings
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module defines the performance settings dialog

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

import json

from PyQt5 import QtCore, QtWidgets

from mslib.utils import FatalUserError
from mslib.msui import aircraft, constants
from mslib.msui.utils.qt import get_open_filename, plain_text_as_html
from mslib.msui.qt5 import ui_performance_dockwidget as ui_dw


DEFAULT_PERFORMANCE = {
    "aircraft": aircraft.SimpleAircraft(aircraft.AIRCRAFT_DUMMY),
    # take off fuel, the take off weight is empty_weight + fuel
    "fuel": aircraft.AIRCRAFT_DUMMY["takeoff_weight"] - aircraft.AIRCRAFT_DUMMY["empty_weight"],
    "takeoff_time": QtCore.QDateTime.currentDateTimeUtc(),
    "empty_weight": aircraft.AIRCRAFT_DUMMY["empty_weight"],
    "ceiling_alt": [410],
}


class MSUI_PerformanceSettingsWidget(QtWidgets.QWidget, ui_dw.Ui_PerformanceDockWidget):
    """
    This class implements setting the performance settings as a dockable widget.
    """

    def __init__(self, parent=None, view=None, settings_dict=None):
        """
        Arguments:
        parent -- Qt widget that is parent to this widget.
        view -- reference to mpl canvas class
        settings_dict -- dictionary containing topview options
        """
        super().__init__(parent)
        self.setupUi(self)
        self.view = view
        self.parent = parent

        if not settings_dict:
            settings_dict = DEFAULT_PERFORMANCE
        self.aircraft = settings_dict["aircraft"]
        self.lbAircraftName.setText(self.aircraft.name)
        self.dsbEmptyWeight.setValue(settings_dict["empty_weight"])

        # Connecting signals. Each update recomputes and redraws the flight
        # track, the spin box has no keyboard tracking, so that typing a
        # value emits valueChanged once, not on every key stroke.
        self.pbLoadPerformance.clicked.connect(self.load_performance)
        self.dsbEmptyWeight.valueChanged.connect(self.update_parent_performance)

    def get_settings(self, fuel=None):
        """
        Encapsulates GUI selections in a python dictionary.

        fuel -- take off fuel, by default the one of the flight track

        :return:
         Dictionary of all setting information
        """
        performance = self.parent.waypoints_model.performance_settings
        settings_dict = {
            "aircraft": self.aircraft,
            # The take off time and fuel are set by editing the table view.
            "takeoff_time": performance["takeoff_time"],
            "fuel": performance["fuel"] if fuel is None else fuel,
            "empty_weight": self.dsbEmptyWeight.value()
        }
        return settings_dict

    def update_parent_performance(self):
        self.parent.setPerformance(self.get_settings())

    def load_performance(self):
        """
        Gets a filename for a JSON file specifying aircraft performance and initializes an SimpleAircraft model.
        """
        filename = get_open_filename(
            self, "Open Aircraft Performance JSON File", constants.MSUI_CONFIG_PATH,
            "Performance File (*.json)", pickertype="default")
        if filename is None:
            return
        try:
            with open(filename) as tf:
                performance = json.load(tf)
            if not isinstance(performance, dict):
                raise ValueError("The file holds no JSON object.")
            # SimpleAircraft takes missing weights as 0
            if "takeoff_weight" not in performance:
                raise KeyError("takeoff_weight")
            if "empty_weight" not in performance and "fuel" not in performance:
                raise KeyError("empty_weight")
            new_aircraft = aircraft.SimpleAircraft(performance)
        except KeyError as ex:
            QtWidgets.QMessageBox.critical(self, self.tr("Performance JSON Load"),
                                           plain_text_as_html(self.tr(f"JSON File missing '{ex}' entry")))
            return
        except (FatalUserError, ValueError) as ex:
            QtWidgets.QMessageBox.critical(self, self.tr("Performance JSON Load"),
                                           plain_text_as_html(self.tr(f"JSON File has Syntax Problems:\n{ex}")))
            return
        self.aircraft = new_aircraft
        self.lbAircraftName.setText(self.aircraft.name)
        # Apply the new aircraft once, not for the changed weight as well.
        with QtCore.QSignalBlocker(self.dsbEmptyWeight):
            self.dsbEmptyWeight.setValue(self.aircraft.empty_weight)
        # The take off fuel of the file's take off weight
        self.parent.setPerformance(self.get_settings(fuel=self.aircraft.takeoff_weight - self.aircraft.empty_weight))
