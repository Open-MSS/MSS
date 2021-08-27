# -*- coding: utf-8 -*-
"""

    mslib.msui.airdata_dockwidget
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Control to load airports and airspaces into the top view.

    This file is part of mss.

    :copyright: Copyright 2021 May Bär
    :copyright: Copyright 2021 by the mss team, see AUTHORS.
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
import pycountry
from mslib.msui.mss_qt import ui_airdata_dockwidget as ui
from PyQt5 import QtWidgets, QtCore
from mslib.utils.config import save_settings_qsettings, load_settings_qsettings
from mslib.utils.airdata import _airspace_cache, update_airspace, get_airports


class AirdataDockwidget(QtWidgets.QWidget, ui.Ui_AirdataDockwidget):
    def __init__(self, parent=None, view=None):
        super(AirdataDockwidget, self).__init__(parent)
        self.setupUi(self)
        self.view = view
        self.view.redrawn.connect(self.redraw_map)

        code_to_name = {country.alpha_2.lower(): country.name for country in pycountry.countries}
        self.cbAirspaces.addItems([f"{code_to_name.get(airspace[0].split('_')[0], 'Unknown')} "
                                   f"{airspace[0].split('_')[0]}"
                                   for airspace in _airspace_cache])
        self.cbAirportType.addItems(["small_airport", "medium_airport", "large_airport", "heliport", "balloonport",
                                     "seaplane_base", "closed"])

        self.settings_tag = "airdatadock"
        settings = load_settings_qsettings(self.settings_tag, {"draw_airports": False, "draw_airspaces": False,
                                                               "airspaces": [], "airport_type": [],
                                                               "filter_airspaces": False, "filter_from": 0,
                                                               "filter_to": 100})

        self.btDownload.clicked.connect(lambda: get_airports(True))
        self.btDownloadAsp.clicked.connect(lambda: update_airspace(True, [airspace.split(" ")[-1] for airspace in
                                                                          self.cbAirspaces.currentData()]))
        self.btApply.clicked.connect(self.redraw_map)

        self.cbDrawAirports.setChecked(settings["draw_airports"])
        self.cbDrawAirspaces.setChecked(settings["draw_airspaces"])
        for airspace in settings["airspaces"]:
            i = self.cbAirspaces.findText(airspace)
            if i != -1:
                self.cbAirspaces.model().item(i).setCheckState(QtCore.Qt.Checked)
        for airport in settings["airport_type"]:
            i = self.cbAirportType.findText(airport)
            if i != -1:
                self.cbAirportType.model().item(i).setCheckState(QtCore.Qt.Checked)
        self.cbAirspaces.updateText()
        self.cbFilterAirspaces.setChecked(settings["filter_airspaces"])
        self.sbFrom.setValue(settings["filter_from"])
        self.sbTo.setValue(settings["filter_to"])

    def redraw_map(self):
        if self.view.map is not None:
            self.view.map.set_draw_airports(self.cbDrawAirports.isChecked(), port_type=self.cbAirportType.currentData())
            self.view.map.set_draw_airspaces(self.cbDrawAirspaces.isChecked(), self.cbAirspaces.currentData(),
                                             (self.sbFrom.value(), self.sbTo.value())
                                             if self.cbFilterAirspaces.isChecked() else None)
            self.view.draw()
        self.save_settings()

    def save_settings(self):
        settings_dict = {
            "draw_airports": self.cbDrawAirports.isChecked(),
            "airport_type": self.cbAirportType.currentData(),
            "draw_airspaces": self.cbDrawAirspaces.isChecked(),
            "airspaces": self.cbAirspaces.currentData(),
            "filter_airspaces": self.cbFilterAirspaces.isChecked(),
            "filter_from": self.sbFrom.value(),
            "filter_to": self.sbTo.value(),
        }
        save_settings_qsettings(self.settings_tag, settings_dict)
