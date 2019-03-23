# -*- coding: utf-8 -*-
"""

    mslib.msui.performance_settings
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module defines the performance settings dialog

    This file is part of mss.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017-2019 by the mss team, see AUTHORS.
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

from mslib.msui.mss_qt import QtCore, QtWidgets, get_open_filename
from mslib.utils import config_loader, FatalUserError
from mslib.msui import aircrafts
from mslib.msui import constants
from mslib.msui.mss_qt import ui_performance_settings as ui_ps


DEFAULT_PERFORMANCE = {
    "aircraft": aircrafts.SimpleAircraft(aircrafts.AIRCRAFT_DUMMY),
    "visible": False,
    "takeoff_weight": 0,
    "takeoff_time": QtCore.QDateTime.currentDateTimeUtc(),
    "fuel": 0
}


class MSS_PerformanceSettingsDialog(QtWidgets.QDialog, ui_ps.Ui_PerformanceSettingsDialog):
    """Dialog to set map appearance parameters. User interface is
       defined in "ui_topview_mapappearance.py".
    """

    def __init__(self, parent=None, settings_dict=None):
        """
        Arguments:
        parent -- Qt widget that is parent to this widget.
        settings_dict -- dictionary containing topview options.
        """
        super(MSS_PerformanceSettingsDialog, self).__init__(parent)
        self.setupUi(self)

        if not settings_dict:
            settings_dict = DEFAULT_PERFORMANCE
        self.aircraft = settings_dict["aircraft"]
        self.lbAircraftName.setText(self.aircraft.name)
        self.cbShowPerformance.setChecked(settings_dict["visible"])
        self.dsbTakeoffWeight.setValue(settings_dict["takeoff_weight"])
        self.dsbFuel.setValue(settings_dict["fuel"])
        self.dteTakeoffTime.setDateTime(settings_dict["takeoff_time"])

        self.pbLoadPerformance.clicked.connect(self.load_performance)

    def get_settings(self):
        """
        Encapsulates GUI selections in a python dictionary.

        :return:
         Dictionary of all setting informations
        """
        settings_dict = {
            "aircraft": self.aircraft,
            "visible": self.cbShowPerformance.isChecked(),
            "takeoff_weight": self.dsbTakeoffWeight.value(),
            "takeoff_time": self.dteTakeoffTime.dateTime(),
            "fuel": self.dsbFuel.value()
        }
        return settings_dict

    def load_performance(self):
        """
        Gets a filename for a JSON file specifying aircraft performance and initializes an SimpleAircraft model.
        """
        filename = get_open_filename(
            self, "Open Aircraft Performance JSON File", constants.MSS_CONFIG_PATH,
            "Performance File (*.json)", pickertag="filepicker_performance")
        if filename is not None:
            try:
                performance = config_loader(config_file=filename)
                self.aircraft = aircrafts.SimpleAircraft(performance)
                self.lbAircraftName.setText(self.aircraft.name)
                self.dsbTakeoffWeight.setValue(self.aircraft.takeoff_weight)
                self.dsbFuel.setValue(self.aircraft.fuel)

            except KeyError as ex:
                QtWidgets.QMessageBox.critical(self, self.tr("Performance JSON Load"),
                                               self.tr(u"JSON File missing '{}' entry".format(ex)))
            except (FatalUserError, ValueError) as ex:
                QtWidgets.QMessageBox.critical(self, self.tr("Performance JSON Load"),
                                               self.tr(u"JSON File has Syntax Problems:\n{}".format(ex)))
