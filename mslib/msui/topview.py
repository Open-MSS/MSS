# -*- coding: utf-8 -*-
"""

    mslib.msui.topview
    ~~~~~~~~~~~~~~~~~~

    Top view implementation for the msui.
    See the reference documentation, Supplement, for details on the
    implementation.

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2020 by the mss team, see AUTHORS.
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
from mslib.utils import config_loader, get_projection_params, save_settings_qsettings, load_settings_qsettings
from mslib.msui import MissionSupportSystemDefaultConfig as mss_default
from mslib.msui.mss_qt import QtGui, QtWidgets, QtCore
from mslib.msui.mss_qt import ui_topview_window as ui
from mslib.msui.mss_qt import ui_topview_mapappearance as ui_ma
from mslib.msui.viewwindows import MSSMplViewWindow
from mslib.msui import wms_control as wc
from mslib.msui import satellite_dockwidget as sat
from mslib.msui import remotesensing_dockwidget as rs
from mslib.msui import kmloverlay_dockwidget as kml
from mslib.msui.icons import icons
from mslib.msui.flighttrack import Waypoint

# Dock window indices.
WMS = 0
SATELLITE = 1
REMOTESENSING = 2
KMLOVERLAY = 3


class MSS_TV_MapAppearanceDialog(QtWidgets.QDialog, ui_ma.Ui_MapAppearanceDialog):
    """Dialog to set map appearance parameters. User interface is
       defined in "ui_topview_mapappearance.py".
    """

    def __init__(self, parent=None, settings_dict=None, wms_connected=False):
        """
        Arguments:
        parent -- Qt widget that is parent to this widget.
        settings_dict -- dictionary containing topview options.
        """
        super(MSS_TV_MapAppearanceDialog, self).__init__(parent)
        self.setupUi(self)
        if settings_dict is None:
            settings_dict = {"draw_graticule": True,
                             "draw_coastlines": True,
                             "fill_waterbodies": True,
                             "fill_continents": True,
                             "draw_flighttrack": True,
                             "label_flighttrack": True,
                             "colour_water": (0, 0, 0, 0),
                             "colour_land": (0, 0, 0, 0),
                             "colour_ft_vertices": (0, 0, 0, 0),
                             "colour_ft_waypoints": (0, 0, 0, 0)}

        settings_dict["fill_waterbodies"] = True  # removing water bodies does not work properly

        self.wms_connected = wms_connected
        # check parent.wms_connected to disable cbFillWaterBodies and cbFillContinents
        if self.wms_connected:
            self.cbFillContinents.setChecked(False)
            self.cbFillWaterBodies.setChecked(False)
            self.cbFillContinents.setEnabled(False)
            self.cbFillContinents.setStyleSheet("color: black")
            self.cbFillWaterBodies.setStyleSheet("color: black")
        else:
            self.cbFillWaterBodies.setChecked(settings_dict["fill_waterbodies"])
            self.cbFillWaterBodies.setEnabled(False)
            self.cbFillContinents.setChecked(settings_dict["fill_continents"])
            self.cbFillContinents.setEnabled(True)

        self.cbDrawGraticule.setChecked(settings_dict["draw_graticule"])
        self.cbDrawCoastlines.setChecked(settings_dict["draw_coastlines"])
        self.cbDrawFlightTrack.setChecked(settings_dict["draw_flighttrack"])
        self.cbLabelFlightTrack.setChecked(settings_dict["label_flighttrack"])

        for button, ids in [(self.btWaterColour, "colour_water"),
                            (self.btLandColour, "colour_land"),
                            (self.btWaypointsColour, "colour_ft_waypoints"),
                            (self.btVerticesColour, "colour_ft_vertices")]:
            palette = QtGui.QPalette(button.palette())
            colour = QtGui.QColor()
            colour.setRgbF(*settings_dict[ids])
            palette.setColor(QtGui.QPalette.Button, colour)
            button.setPalette(palette)

        # Connect colour button signals.
        self.btWaterColour.clicked.connect(functools.partial(self.setColour, "water"))
        self.btLandColour.clicked.connect(functools.partial(self.setColour, "land"))
        self.btWaypointsColour.clicked.connect(functools.partial(self.setColour, "ft_waypoints"))
        self.btVerticesColour.clicked.connect(functools.partial(self.setColour, "ft_vertices"))

    def get_settings(self):
        """
        """
        settings_dict = {
            "draw_graticule": self.cbDrawGraticule.isChecked(),
            "draw_coastlines": self.cbDrawCoastlines.isChecked(),
            "fill_waterbodies": self.cbFillWaterBodies.isChecked(),
            "fill_continents": self.cbFillContinents.isChecked(),
            "draw_flighttrack": self.cbDrawFlightTrack.isChecked(),
            "label_flighttrack": self.cbLabelFlightTrack.isChecked(),

            "colour_water":
                QtGui.QPalette(self.btWaterColour.palette()).color(QtGui.QPalette.Button).getRgbF(),
            "colour_land":
                QtGui.QPalette(self.btLandColour.palette()).color(QtGui.QPalette.Button).getRgbF(),
            "colour_ft_vertices":
                QtGui.QPalette(self.btVerticesColour.palette()).color(QtGui.QPalette.Button).getRgbF(),
            "colour_ft_waypoints":
                QtGui.QPalette(self.btWaypointsColour.palette()).color(QtGui.QPalette.Button).getRgbF(),
        }
        return settings_dict

    def setColour(self, which):
        """Slot for the colour buttons: Opens a QColorDialog and sets the
           new button face colour.
        """
        if which == "water":
            button = self.btWaterColour
        elif which == "land":
            button = self.btLandColour
        elif which == "ft_vertices":
            button = self.btVerticesColour
        elif which == "ft_waypoints":
            button = self.btWaypointsColour

        palette = QtGui.QPalette(button.palette())
        colour = palette.color(QtGui.QPalette.Button)
        colour = QtWidgets.QColorDialog.getColor(colour)
        if colour.isValid():
            palette.setColor(QtGui.QPalette.Button, colour)
            button.setPalette(palette)


class MSSTopViewWindow(MSSMplViewWindow, ui.Ui_TopViewWindow):
    """PyQt window implementing a MapCanvas as an interactive flight track
       editor.
    """
    name = "Top View"

    def __init__(self, parent=None, model=None, _id=None):
        """Set up user interface, connect signal/slots.
        """
        super(MSSTopViewWindow, self).__init__(parent, model, _id)
        logging.debug(_id)
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(icons('64x64')))

        # Dock windows [WMS, Satellite, Trajectories, Remote Sensing, KML Overlay]:
        self.docks = [None, None, None, None, None]

        self.settings_tag = "topview"
        self.load_settings()

        # Initialise the GUI elements (map view, items of combo boxes etc.).
        self.setup_top_view()

        # Boolean to store active wms connection
        self.wms_connected = False

        # Connect slots and signals.
        # ==========================

        # Map controls.
        self.btMapRedraw.clicked.connect(self.mpl.canvas.redraw_map)
        self.cbChangeMapSection.activated.connect(self.changeMapSection)

        # Settings
        self.btSettings.clicked.connect(self.settings_dialogue)

        # Roundtrip
        self.btRoundtrip.clicked.connect(self.make_roundtrip)

        # Tool opener.
        self.cbTools.currentIndexChanged.connect(self.openTool)

    def __del__(self):
        del self.mpl.canvas.waypoints_interactor

    def setup_top_view(self):
        """Initialise GUI elements. (This method is called before signals/slots
           are connected).
        """
        toolitems = ["(select to open control)", "Web Map Service", "Satellite Tracks", "Remote Sensing", "KML Overlay"]
        self.cbTools.clear()
        self.cbTools.addItems(toolitems)

        # Fill combobox for predefined map sections.
        self.update_predefined_maps()

        # Initialise the map and the flight track. Get the initial projection
        # parameters from the tables in mss_settings.
        kwargs = self.changeMapSection(only_kwargs=True)
        self.mpl.canvas.init_map(**kwargs)
        self.setFlightTrackModel(self.waypoints_model)

        # Automatically enable or disable roundtrip when data changes
        self.waypoints_model.dataChanged.connect(self.update_roundtrip_enabled)
        self.update_roundtrip_enabled()

    def update_predefined_maps(self, extra=None):
        self.cbChangeMapSection.clear()
        predefined_map_sections = config_loader(
            dataset="predefined_map_sections", default=mss_default.predefined_map_sections)
        self.cbChangeMapSection.addItems(sorted(predefined_map_sections.keys()))
        if extra is not None and len(extra) > 0:
            self.cbChangeMapSection.insertSeparator(self.cbChangeMapSection.count())
            self.cbChangeMapSection.addItems(sorted(extra))

    def openTool(self, index):
        """Slot that handles requests to open control windows.
        """
        index = self.controlToBeCreated(index)
        if index >= 0:
            if index == WMS:
                # Create a new WMSDockWidget.
                title = "Web Map Service (Top View)"
                widget = wc.HSecWMSControlWidget(
                    default_WMS=config_loader(dataset="default_WMS", default=mss_default.default_WMS),
                    view=self.mpl.canvas,
                    wms_cache=config_loader(dataset="wms_cache", default=mss_default.wms_cache))
                widget.signal_disable_cbs.connect(self.disable_cbs)
                widget.signal_enable_cbs.connect(self.enable_cbs)
            elif index == SATELLITE:
                title = "Satellite Track Prediction"
                widget = sat.SatelliteControlWidget(view=self.mpl.canvas)
            elif index == REMOTESENSING:
                title = "Remote Sensing Tools"
                widget = rs.RemoteSensingControlWidget(view=self.mpl.canvas)
            elif index == KMLOVERLAY:
                title = "KML Overlay"
                widget = kml.KMLOverlayControlWidget(view=self.mpl.canvas)
            else:
                raise IndexError("invalid control index")

            # Create the actual dock widget containing <widget>.
            self.createDockWidget(index, title, widget)

    @QtCore.Slot()
    def disable_cbs(self):
        self.wms_connected = True

    @QtCore.Slot()
    def enable_cbs(self):
        self.wms_connected = False

    def changeMapSection(self, index=0, only_kwargs=False):
        """Change the current map section to one of the predefined regions.
        """
        # Get the initial projection parameters from the tables in mss_settings.
        current_map_key = self.cbChangeMapSection.currentText()
        predefined_map_sections = config_loader(
            dataset="predefined_map_sections", default=mss_default.predefined_map_sections)
        current_map = predefined_map_sections.get(
            current_map_key, {"CRS": current_map_key, "map": {}})
        proj_params = get_projection_params(current_map["CRS"])

        # Create a keyword arguments dictionary for basemap that contains
        # the projection parameters.
        kwargs = current_map["map"]
        kwargs.update({"CRS": current_map["CRS"], "BBOX_UNITS": proj_params["bbox"]})
        kwargs.update(proj_params["basemap"])

        if only_kwargs:
            # Return kwargs dictionary and do NOT redraw the map.
            return kwargs

        logging.debug("switching to map section '%s' - '%s'", current_map_key, kwargs)
        self.mpl.canvas.redraw_map(kwargs)

    def setIdentifier(self, identifier):
        super(MSSTopViewWindow, self).setIdentifier(identifier)
        self.mpl.canvas.map.set_identifier(identifier)

    def settings_dialogue(self):
        """
        """
        settings = self.getView().get_map_appearance()
        dlg = MSS_TV_MapAppearanceDialog(parent=self, settings_dict=settings, wms_connected=self.wms_connected)
        dlg.setModal(True)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            settings = dlg.get_settings()
            self.getView().set_map_appearance(settings)
            self.save_settings()
            self.mpl.canvas.waypoints_interactor.redraw_path()
        dlg.destroy()

    def save_settings(self):
        """Save the current settings (map appearance) to the file
           self.settingsfile.
        """
        settings = self.getView().get_map_appearance()
        save_settings_qsettings(self.settings_tag, settings)

    def load_settings(self):
        """Load settings from the file self.settingsfile.
        """
        settings = load_settings_qsettings(self.settings_tag, {})
        self.getView().set_map_appearance(settings)

    def make_roundtrip(self):
        """
        Copies the first waypoint and inserts it at the back of the list again
        Essentially creating a roundtrip
        """
        # This case should never be True for users, but might be for developers at some point
        if not self.is_roundtrip_possible():
            return

        first_waypoint = self.waypoints_model.waypoint_data(0)
        last_waypoint = self.waypoints_model.waypoint_data(self.waypoints_model.rowCount() - 1)

        self.waypoints_model.insertRows(self.waypoints_model.rowCount(), rows=1, waypoints=[
            Waypoint(lat=first_waypoint.lat, lon=first_waypoint.lon, flightlevel=first_waypoint.flightlevel,
                     location=first_waypoint.location)])

    def is_roundtrip_possible(self):
        """
        Checks if there are at least 2 waypoints, and the first and last are not the same
        """
        condition = self.waypoints_model.rowCount() > 1

        if condition:
            first_waypoint = self.waypoints_model.waypoint_data(0)
            last_waypoint = self.waypoints_model.waypoint_data(self.waypoints_model.rowCount() - 1)

            condition = first_waypoint.lat != last_waypoint.lat or first_waypoint.lon != last_waypoint.lon or \
                        first_waypoint.flightlevel != last_waypoint.flightlevel

        return condition

    def update_roundtrip_enabled(self):
        self.btRoundtrip.setEnabled(self.is_roundtrip_possible())
