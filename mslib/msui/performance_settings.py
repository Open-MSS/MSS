# -*- coding: utf-8 -*-
"""

    mslib.msui.performance_settings
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module defines the performance settings dialog

    This file is part of mss.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017-2021 by the mss team, see AUTHORS.
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

from mslib.msui.mss_qt import get_open_filename
from PyQt5 import QtCore, QtWidgets
from mslib.utils import config_loader, FatalUserError
from mslib.msui import aircrafts
from mslib.msui import constants
from mslib.msui.mss_qt import ui_performance_dockwidget as ui_dw


DEFAULT_PERFORMANCE = {
    "aircraft": aircrafts.SimpleAircraft(aircrafts.AIRCRAFT_DUMMY),
    "visible": False,
    "takeoff_weight": 0,
    "takeoff_time": QtCore.QDateTime.currentDateTimeUtc(),
    "empty_weight": 0,
    "ceiling_alt": [410],
}


class MSS_PerformanceSettingsWidget(QtWidgets.QWidget, ui_dw.Ui_PerformanceDockWidget):
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
        super(MSS_PerformanceSettingsWidget, self).__init__(parent)
        self.setupUi(self)
        self.view = view
        self.parent = parent

        if not settings_dict:
            settings_dict = DEFAULT_PERFORMANCE
        self.aircraft = settings_dict["aircraft"]
        self.lbAircraftName.setText(self.aircraft.name)
        self.cbShowPerformance.setChecked(settings_dict["visible"])
        self.dsbTakeoffWeight.setValue(settings_dict["takeoff_weight"])
        self.dsbEmptyWeight.setValue(
            settings_dict.get("empty_weight", settings_dict["takeoff_weight"] - settings_dict.get("fuel", 0)))
        self.dteTakeoffTime.setDateTime(settings_dict["takeoff_time"])

        # Connecting signals
        self.pbLoadPerformance.clicked.connect(self.load_performance)
        self.cbShowPerformance.stateChanged.connect(self.update_parent_performance)
        self.dteTakeoffTime.dateTimeChanged.connect(self.update_parent_performance)
        self.dsbTakeoffWeight.valueChanged.connect(self.update_parent_performance)
        self.dsbEmptyWeight.valueChanged.connect(self.update_parent_performance)

    def get_settings(self):
        """
        Encapsulates GUI selections in a python dictionary.

        :return:
         Dictionary of all setting informations
        """
        settings_dict = {
            "aircraft": self.aircraft,
            "visible": self.cbShowPerformance.isChecked(),
            "takeoff_time": self.dteTakeoffTime.dateTime(),
            "takeoff_weight": self.dsbTakeoffWeight.value(),
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
            self, "Open Aircraft Performance JSON File", constants.MSS_CONFIG_PATH,
            "Performance File (*.json)", pickertag="filepicker_default")
        if filename is not None:
            try:
                performance = config_loader(config_file=filename)
                self.aircraft = aircrafts.SimpleAircraft(performance)
                self.lbAircraftName.setText(self.aircraft.name)
                self.dsbTakeoffWeight.setValue(self.aircraft.takeoff_weight)
                if not any(hasattr(self.aircraft, _x) for _x in ("fuel", "empty_weight")):
                    raise KeyError("empty_weight")
                if hasattr(self.aircraft, "empty_weight"):
                    self.dsbEmptyWeight.setValue(self.aircraft.empty_weight)
                else:
                    self.dsbEmptyWeight.setValue(self.aircraft.takeoff_weight - self.aircraft.fuel)

                self.update_parent_performance()

            except KeyError as ex:
                QtWidgets.QMessageBox.critical(self, self.tr("Performance JSON Load"),
                                               self.tr(f"JSON File missing '{ex}' entry"))
            except (FatalUserError, ValueError) as ex:
                QtWidgets.QMessageBox.critical(self, self.tr("Performance JSON Load"),
                                               self.tr(f"JSON File has Syntax Problems:\n{ex}"))
