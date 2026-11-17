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

# The largest take off fuel or empty weight msui accepts (lb), the maximum of the
# empty weight box. Rejects e.g. a typed 1e400 (inf).
MAX_WEIGHT = 9999999

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

        self.show_settings(settings_dict or DEFAULT_PERFORMANCE)

        # Connecting signals. Each update recomputes and redraws the flight
        # track, the spin box has no keyboard tracking, so that typing a
        # value emits valueChanged once, not on every key stroke.
        self.pbLoadPerformance.clicked.connect(self.load_performance)
        self.dsbEmptyWeight.valueChanged.connect(self.update_parent_performance)

    def show_settings(self, settings_dict):
        """
        Shows the aircraft and empty weight of settings_dict, the performance settings of the
        flight track, whenever they change. The dock keeps no copy of them: another table view
        of the same flight track may change them.
        """
        self.lbAircraftName.setText(settings_dict["aircraft"].name)
        with QtCore.QSignalBlocker(self.dsbEmptyWeight):
            self.dsbEmptyWeight.setValue(settings_dict["empty_weight"])

    def get_settings(self, **changes):
        """
        The performance settings of the flight track with the empty weight of the dock and changes,
        e.g. aircraft or fuel.

        :return:
         Dictionary of all setting information
        """
        # The take off time and fuel are set by editing the table view.
        settings = dict(self.parent.waypoints_model.performance_settings, empty_weight=self.dsbEmptyWeight.value())
        settings.update(changes)
        return settings

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
            for key in ("takeoff_weight", "empty_weight", "fuel"):
                if key in performance and (isinstance(performance[key], bool) or
                                           not isinstance(performance[key], (int, float))):
                    raise ValueError(f"'{key}' is not a number.")
            new_aircraft = aircraft.SimpleAircraft(performance)
            if not 0 <= new_aircraft.empty_weight <= new_aircraft.takeoff_weight <= MAX_WEIGHT:
                raise ValueError(
                    f"The empty weight must lie between 0 and the take off weight, at most {MAX_WEIGHT}.")
        except OSError as ex:
            QtWidgets.QMessageBox.critical(self, self.tr("Performance JSON Load"),
                                           plain_text_as_html(self.tr(f"JSON File could not be read:\n{ex}")))
            return
        except KeyError as ex:
            QtWidgets.QMessageBox.critical(self, self.tr("Performance JSON Load"),
                                           plain_text_as_html(self.tr(f"JSON File missing '{ex}' entry")))
            return
        except (FatalUserError, ValueError, TypeError) as ex:
            # TypeError: e.g. a performance table of other than numbers
            QtWidgets.QMessageBox.critical(self, self.tr("Performance JSON Load"),
                                           plain_text_as_html(self.tr(f"JSON File has Syntax Problems:\n{ex}")))
            return
        # The box has no decimals: the fuel from the shown empty weight, so that both
        # give the take off weight of the file.
        with QtCore.QSignalBlocker(self.dsbEmptyWeight):
            self.dsbEmptyWeight.setValue(new_aircraft.empty_weight)
        fuel = new_aircraft.takeoff_weight - self.dsbEmptyWeight.value()
        # Applied once; all docks of the flight track show it on performanceDataChanged.
        self.parent.setPerformance(self.get_settings(aircraft=new_aircraft, fuel=fuel))
