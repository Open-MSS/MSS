# -*- coding: utf-8 -*-
"""

    mslib.msui.sideview
    ~~~~~~~~~~~~~~~~~~~

    Side view module of the msui

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2017 by the mss team, see AUTHORS.
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

import functools
import logging
from mslib.utils import config_loader, save_settings_pickle, load_settings_pickle
from mslib.msui import MissionSupportSystemDefaultConfig as mss_default

# related third party imports
from mslib.msui.mss_qt import QtGui, QtWidgets, QString

# local application imports
from mslib.msui.mss_qt import ui_sideview_window as ui
from mslib.msui.mss_qt import ui_sideview_options as ui_opt
from mslib.msui.viewwindows import MSSMplViewWindow
from mslib.msui import flighttrack as ft
from mslib.msui import mpl_pathinteractor as mpl_pi
from mslib.msui import wms_control as wms


# Dock window indices.
WMS = 0


class MSS_SV_OptionsDialog(QtWidgets.QDialog, ui_opt.Ui_SideViewOptionsDialog):
    """Dialog to specify sideview options. User interface is specified
       in "ui_sideview_options.py".
    """

    def __init__(self, parent=None, settings_dict=None):
        """
        Arguments:
        parent -- Qt widget that is parent to this widget.
        settings_dict -- dictionary containing sideview options.
        """
        super(MSS_SV_OptionsDialog, self).__init__(parent)
        self.setupUi(self)

        default_settings_dict = {"vertical_extent": (1050, 180),
                                 "flightlevels": [300, 320, 340],
                                 "draw_flightlevels": True,
                                 "draw_flighttrack": True,
                                 "fill_flighttrack": True,
                                 "label_flighttrack": True,
                                 "colour_ft_vertices": (0, 0, 0, 0),
                                 "colour_ft_waypoints": (0, 0, 0, 0),
                                 "colour_ft_fill": (0, 0, 0, 0)}
        default_settings_dict.update(settings_dict)
        settings_dict = default_settings_dict

        self.sbPbot.setValue(settings_dict["vertical_extent"][0])
        self.sbPtop.setValue(settings_dict["vertical_extent"][1])

        flightlevels = settings_dict["flightlevels"]
        self.tableWidget.setRowCount(len(flightlevels))
        flightlevels.sort()
        for i, level in enumerate(flightlevels):
            tableitem = QtWidgets.QTableWidgetItem(str(int(level)))
            self.tableWidget.setItem(i, 0, tableitem)

        self.cbDrawFlightLevels.setChecked(settings_dict["draw_flightlevels"])
        self.cbDrawFlightTrack.setChecked(settings_dict["draw_flighttrack"])
        self.cbFillFlightTrack.setChecked(settings_dict["fill_flighttrack"])
        self.cbLabelFlightTrack.setChecked(settings_dict["label_flighttrack"])

        for button, ids in [(self.btFillColour, "colour_ft_fill"),
                            (self.btWaypointsColour, "colour_ft_waypoints"),
                            (self.btVerticesColour, "colour_ft_vertices")]:
            palette = QtGui.QPalette(button.palette())
            colour = QtGui.QColor()
            colour.setRgbF(*settings_dict[ids])
            palette.setColor(QtGui.QPalette.Button, colour)
            button.setPalette(palette)

        # Connect colour button signals.
        self.btFillColour.clicked.connect(functools.partial(self.setColour, "ft_fill"))
        self.btWaypointsColour.clicked.connect(functools.partial(self.setColour, "ft_waypoints"))
        self.btVerticesColour.clicked.connect(functools.partial(self.setColour, "ft_vertices"))

        self.btAdd.clicked.connect(self.addItem)
        self.btDelete.clicked.connect(self.deleteSelected)

        self.tableWidget.itemChanged.connect(self.itemChanged)

    def setColour(self, which):
        """Slot for the colour buttons: Opens a QColorDialog and sets the
           new button face colour.
        """
        if which == "ft_fill":
            button = self.btFillColour
        elif which == "ft_vertices":
            button = self.btVerticesColour
        elif which == "ft_waypoints":
            button = self.btWaypointsColour

        palette = QtGui.QPalette(button.palette())
        colour = palette.color(QtGui.QPalette.Button)
        colour = QtWidgets.QColorDialog.getColor(colour)
        if colour.isValid():
            if which == "ft_fill":
                # Fill colour is transparent with an alpha value of 0.15. If
                # you like to change this, modify the PathInteractor class.
                colour.setAlphaF(0.15)
            palette.setColor(QtGui.QPalette.Button, colour)
            button.setPalette(palette)

    def addItem(self):
        """Add a new item (i.e. flight level) to the table.
        """
        self.tableWidget.insertRow(0)
        self.tableWidget.setItem(0, 0, QtWidgets.QTableWidgetItem("0"))
        self.tableWidget.sortItems(0)

    def deleteSelected(self):
        """Remove the selected items (i.e. flight levels) from the table.
        """
        selecteditems = self.tableWidget.selectedItems()
        for item in selecteditems:
            self.tableWidget.removeRow(item.row())

    def itemChanged(self, item):
        """Slot that is called when an item has been changed. Checks for
           a valid integer in the range 0..999. Other values or non-numeric
           values are corrected.
        """
        try:
            flightlevel = int(float(unicode(item.text())))
        except:
            flightlevel = 0
        if flightlevel < 0:
            flightlevel = 0
        if flightlevel > 999:
            flightlevel = 999
        item.setText(str(int(flightlevel)))
        self.tableWidget.sortItems(0)

    def getFlightLevels(self):
        """Returns the flight level values contained in the table.
        """
        return [int(unicode(self.tableWidget.item(row, 0).text()))
                for row in range(self.tableWidget.rowCount())]

    def getSettings(self):
        """Return settings dictionary with values from the GUI elements.
        """
        settings_dict = {
            "vertical_extent": (int(self.sbPbot.value()), int(self.sbPtop.value())),
            "flightlevels": self.getFlightLevels(),
            "draw_flightlevels": self.cbDrawFlightLevels.isChecked(),
            "draw_flighttrack": self.cbDrawFlightTrack.isChecked(),
            "fill_flighttrack": self.cbFillFlightTrack.isChecked(),
            "label_flighttrack": self.cbLabelFlightTrack.isChecked(),
            "colour_ft_vertices":
                QtGui.QPalette(self.btVerticesColour.palette()).color(QtGui.QPalette.Button).getRgbF(),
            "colour_ft_waypoints":
                QtGui.QPalette(self.btWaypointsColour.palette()).color(QtGui.QPalette.Button).getRgbF(),
            "colour_ft_fill":
                QtGui.QPalette(self.btFillColour.palette()).color(QtGui.QPalette.Button).getRgbF()
        }
        return settings_dict


class MSSSideViewWindow(MSSMplViewWindow, ui.Ui_SideViewWindow):
    """PyQt4 window implementing a matplotlib canvas as an interactive
       side view flight track editor.
    """
    name = "Side View"

    def __init__(self, parent=None, model=None):
        """Set up user interface, connect signal/slots.
        """
        super(MSSSideViewWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon('icons/64x64/mss-logo.png'))

        # Dock windows [WMS]:
        self.cbTools.clear()
        self.cbTools.addItems(["(select to open control)", "Vertical Section WMS"])
        self.docks = [None]

        self.setFlightTrackModel(model)

        self.settings_tag = "sideview"
        self.loadSettings()

        # Connect slots and signals.
        # ==========================

        # Buttons to set sideview options.
        self.btOptions.clicked.connect(self.setOptions)

        # Tool opener.
        self.cbTools.currentIndexChanged.connect(self.openTool)

        # Controls to interact with the flight track.
        # (For usage of the functools.partial() function, see Chapter 4 (Section
        # Signals and Slots) of 'Rapid GUI Programming with Python and Qt: The
        # Definitive Guide to PyQt Programming' (Mark Summerfield).)
        wpi = self.mpl.canvas.waypoints_interactor
        self.btMvWaypoint.clicked.connect(functools.partial(wpi.set_edit_mode, mpl_pi.MOVE))
        self.btInsWaypoint.clicked.connect(functools.partial(wpi.set_edit_mode, mpl_pi.INSERT))
        self.btDelWaypoint.clicked.connect(functools.partial(wpi.set_edit_mode, mpl_pi.DELETE))

    def __del__(self):
        del self.mpl.canvas.waypoints_interactor

    def openTool(self, index):
        """Slot that handles requests to open tool windows.
        """
        index = self.controlToBeCreated(index)
        if index >= 0:
            if index == WMS:
                # Open a WMS control widget.
                title = "Web Service Plot Control"
                widget = wms.VSecWMSControlWidget(default_WMS=config_loader(dataset="default_VSEC_WMS",
                                                                            default=mss_default.default_VSEC_WMS),
                                                  waypoints_model=self.waypoints_model,
                                                  view=self.mpl.canvas,
                                                  wms_cache=config_loader(dataset="wms_cache",
                                                                          default=mss_default.wms_cache))
            else:
                raise IndexError("invalid control index")
            # Create the actual dock widget containing <widget>.
            self.createDockWidget(index, title, widget)

    def setFlightTrackModel(self, model):
        """Set the QAbstractItemModel instance that the view displays.
        """
        super(MSSSideViewWindow, self).setFlightTrackModel(model)
        if self.docks[WMS] is not None:
            self.docks[WMS].widget().setFlightTrackModel(model)

    def setOptions(self):
        """Slot to open a dialog that lets the user specifiy sideview options.
        """
        settings = self.getView().getSettings()
        dlg = MSS_SV_OptionsDialog(parent=self, settings_dict=settings)
        dlg.setModal(True)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            settings = dlg.getSettings()
            self.getView().setSettings(settings)
            self.saveSettings()
        dlg.destroy()

    def saveSettings(self):
        """Save the current settings (vertical extent, displayed flightlevels
           etc.) to the file self.settingsfile.
        """
        # TODO: ConfigParser and a central configuration file might be the better solution than pickle.
        # http://stackoverflow.com/questions/200599/whats-the-best-way-to-store-simple-user-settings-in-python
        settings = self.getView().getSettings()
        save_settings_pickle(self.settings_tag, settings)

    def loadSettings(self):
        """Load settings from the file self.settingsfile.
        """
        settings = load_settings_pickle(self.settings_tag)
        self.getView().setSettings(settings)
