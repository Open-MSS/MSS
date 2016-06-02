"""Top view implementation for the MSUI.

********************************************************************************

   Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

********************************************************************************

This file is part of the Mission Support System User Interface (MSUI).

See the reference documentation, Supplement, for details on the
implementation.

AUTHORS:
========

* Marc Rautenhaus (mr)

"""

# standard library imports
import functools
import os
import sys
import logging
import pickle
import datetime

# related third party imports
from PyQt4 import QtGui, QtCore  # Qt4 bindings

# local application imports
import ui_topview_window as ui
import ui_topview_mapappearance as ui_ma
import mss_qt
import mpl_pathinteractor as mpl_pi
import mss_settings
import flighttrack as ft
import wms_control as wms
import satellite_dockwidget as sat

################################################################################

# Dock window indices.
WMS = 0
SATELLITE = 1


################################################################################
###                       DIALOG for map appearance                          ###
################################################################################

class MSS_TV_MapAppearanceDialog(QtGui.QDialog, ui_ma.Ui_MapAppearanceDialog):
    """Dialog to set map appearance parameters. User interface is
       defined in "ui_topview_mapappearance.py".
    """

    def __init__(self, parent=None, settings_dict=None):
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
                             "draw_tangents": True,
                             "show_solar_angle": True,
                             "colour_water": (0, 0, 0, 0),
                             "colour_land": (0, 0, 0, 0),
                             "colour_ft_vertices": (0, 0, 0, 0),
                             "colour_ft_waypoints": (0, 0, 0, 0),
                             "colour_tangents": (0, 0, 0, 0)}

        if "draw_tangents" not in settings_dict.keys():
            settings_dict["draw_tangents"] = True
        if "tangent_height" not in settings_dict.keys():
            settings_dict["tangent_height"] = 1.
        if "show_solar_angle" not in settings_dict.keys():
            settings_dict["show_solar_angle"] = True
        if "start_time" not in settings_dict.keys():
            settings_dict["start_time"] = datetime.datetime.now()
        if "colour_tangents" not in settings_dict.keys():
            settings_dict["colour_tangents"] = (0, 0, 0, 0)

        self.cbDrawGraticule.setChecked(settings_dict["draw_graticule"])
        self.cbDrawCoastlines.setChecked(settings_dict["draw_coastlines"])
        self.cbFillWaterBodies.setChecked(settings_dict["fill_waterbodies"])
        self.cbFillContinents.setChecked(settings_dict["fill_continents"])
        self.cbDrawFlightTrack.setChecked(settings_dict["draw_flighttrack"])
        self.cbLabelFlightTrack.setChecked(settings_dict["label_flighttrack"])
        self.cbDrawTangents.setChecked(settings_dict["draw_tangents"])
        self.dsbTangentHeight.setValue(settings_dict["tangent_height"])
        self.cbShowSolarAngle.setChecked(settings_dict["show_solar_angle"])
        self.dteStartTime.setDateTime(settings_dict["start_time"])

        for button, ids in [(self.btWaterColour, "colour_water"),
                            (self.btLandColour, "colour_land"),
                            (self.btWaypointsColour, "colour_ft_waypoints"),
                            (self.btVerticesColour, "colour_ft_vertices"),
                            (self.btTangentsColour, "colour_tangents")]:
            palette = QtGui.QPalette(button.palette())
            colour = QtGui.QColor()
            colour.setRgbF(*settings_dict[ids])
            palette.setColor(QtGui.QPalette.Button, colour)
            button.setPalette(palette)

        # Connect colour button signals.
        self.connect(self.btWaterColour, QtCore.SIGNAL("clicked()"),
                     functools.partial(self.setColour, "water"))
        self.connect(self.btLandColour, QtCore.SIGNAL("clicked()"),
                     functools.partial(self.setColour, "land"))
        self.connect(self.btWaypointsColour, QtCore.SIGNAL("clicked()"),
                     functools.partial(self.setColour, "ft_waypoints"))
        self.connect(self.btVerticesColour, QtCore.SIGNAL("clicked()"),
                     functools.partial(self.setColour, "ft_vertices"))
        self.connect(self.btTangentsColour, QtCore.SIGNAL("clicked()"),
                     functools.partial(self.setColour, "tangents"))

    def getSettings(self):
        """
        """
        settings_dict = {
            "draw_graticule": self.cbDrawGraticule.isChecked(),
            "draw_coastlines": self.cbDrawCoastlines.isChecked(),
            "fill_waterbodies": self.cbFillWaterBodies.isChecked(),
            "fill_continents": self.cbFillContinents.isChecked(),
            "draw_flighttrack": self.cbDrawFlightTrack.isChecked(),
            "label_flighttrack": self.cbLabelFlightTrack.isChecked(),
            "draw_tangents": self.cbDrawTangents.isChecked(),
            "tangent_height": self.dsbTangentHeight.value(),
            "show_solar_angle": self.cbShowSolarAngle.isChecked(),
            "start_time": self.dteStartTime.dateTime().toPyDateTime(),

            "colour_water":
                QtGui.QPalette(self.btWaterColour.palette()).color(QtGui.QPalette.Button).getRgbF(),
            "colour_land":
                QtGui.QPalette(self.btLandColour.palette()).color(QtGui.QPalette.Button).getRgbF(),
            "colour_ft_vertices":
                QtGui.QPalette(self.btVerticesColour.palette()).color(QtGui.QPalette.Button).getRgbF(),
            "colour_ft_waypoints":
                QtGui.QPalette(self.btWaypointsColour.palette()).color(QtGui.QPalette.Button).getRgbF(),
            "colour_tangents":
                QtGui.QPalette(self.btTangentsColour.palette()).color(QtGui.QPalette.Button).getRgbF()
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
        elif which == "tangents":
            button = self.btTangentsColour

        palette = QtGui.QPalette(button.palette())
        colour = palette.color(QtGui.QPalette.Button)
        colour = QtGui.QColorDialog.getColor(colour)
        if colour.isValid():
            palette.setColor(QtGui.QPalette.Button, colour)
            button.setPalette(palette)


################################################################################
###                        CLASS FlightPlanTopView                           ###
################################################################################

class MSSTopViewWindow(mss_qt.MSSMplViewWindow, ui.Ui_TopViewWindow):
    """PyQt4 window implementing a MapCanvas as an interactive flight track
       editor.
    """
    name = "Top View"

    def __init__(self, parent=None, model=None):
        """Set up user interface, connect signal/slots.
        """
        super(MSSTopViewWindow, self).__init__(parent, model)
        self.setupUi(self)

        # Dock windows [WMS, Satellite, Trajectories]:
        self.docks = [None, None, None]

        self.settingsfile = "mss.topview.cfg"
        self.loadSettings()

        # Initialise the GUI elements (map view, items of combo boxes etc.).
        self.setupTopView()

        # Connect slots and signals.
        # ==========================

        # Map controls.
        self.connect(self.btMapRedraw, QtCore.SIGNAL("clicked()"),
                     self.mpl.canvas.redrawMap)
        self.connect(self.cbChangeMapSection, QtCore.SIGNAL("activated(int)"),
                     self.changeMapSection)

        # Settings
        self.connect(self.btSettings, QtCore.SIGNAL("clicked()"),
                     self.settingsDlg)

        # Tool opener.
        self.connect(self.cbTools, QtCore.SIGNAL("currentIndexChanged(int)"),
                     self.openTool)

        # Controls to interact with the flight track.
        # (For usage of the functools.partial() function, see Chapter 4 (Section
        # Signals and Slots) of 'Rapid GUI Programming with Python and Qt: The
        # Definitive Guide to PyQt Programming' (Mark Summerfield).)
        wpi = self.mpl.canvas.waypoints_interactor
        self.connect(self.btMvWaypoint, QtCore.SIGNAL("clicked()"),
                     functools.partial(wpi.set_edit_mode, mpl_pi.MOVE))
        self.connect(self.btInsWaypoint, QtCore.SIGNAL("clicked()"),
                     functools.partial(wpi.set_edit_mode, mpl_pi.INSERT))
        self.connect(self.btDelWaypoint, QtCore.SIGNAL("clicked()"),
                     functools.partial(wpi.set_edit_mode, mpl_pi.DELETE))

    def setupTopView(self):
        """Initialise GUI elements. (This method is called before signals/slots
           are connected).
        """
        toolitems = ["(select to open control)", "Web Map Service", "Satellite Tracks"]
        self.cbTools.clear()
        self.cbTools.addItems(toolitems)

        # Fill combobox for predefined map sections.
        self.cbChangeMapSection.clear()
        items = mss_settings.predefined_map_sections.keys()
        items.sort()
        self.cbChangeMapSection.addItems(items)

        # Initialise the map and the flight track. Get the initial projection
        # parameters from the tables in mss_settings.
        kwargs = self.changeMapSection(only_kwargs=True)
        self.mpl.canvas.initMap(**kwargs)
        self.setFlightTrackModel(self.waypoints_model)

    def openTool(self, index):
        """Slot that handles requests to open control windows.
        """
        index = self.controlToBeCreated(index)
        if index >= 0:
            if index == WMS:
                # Create a new WMSDockWidget.
                title = "Web Map Service (Top View)"
                widget = wms.HSecWMSControlWidget(
                    default_WMS=mss_settings.default_WMS,
                    view=self.mpl.canvas,
                    wms_cache=mss_settings.wms_cache)
                settings = self.getView().getMapAppearance()
                if settings["draw_tangents"]:
                    widget.set_tp_height(settings["tangent_height"])
            elif index == SATELLITE:
                title = "Satellite Track Prediction"
                widget = sat.SatelliteControlWidget(view=self.mpl.canvas)
            else:
                raise IndexError("invalid control index")

            # Create the actual dock widget containing <widget>.
            self.createDockWidget(index, title, widget)

    def changeMapSection(self, index=0, only_kwargs=False):
        """Change the current map section to one of the predefined regions.
        """
        # Get the initial projection parameters from the tables in mss_settings.
        current_map_key = str(self.cbChangeMapSection.currentText())
        current_map = mss_settings.predefined_map_sections[current_map_key]

        # Create a keyword arguments dictionary for basemap that contains
        # the projection parameters.
        kwargs = current_map["map"]
        kwargs.update({"CRS": current_map["CRS"]})
        kwargs.update({"BBOX_UNITS": mss_settings.crs_to_mpl_basemap_table[current_map["CRS"]]["bbox"]})
        kwargs.update(mss_settings.crs_to_mpl_basemap_table[current_map["CRS"]]["basemap"])

        if only_kwargs:
            # Return kwargs dictionary and do NOT redraw the map.
            return kwargs

        logging.debug("switching to map section %s", current_map_key)
        self.mpl.canvas.redrawMap(kwargs)

    def setIdentifier(self, identifier):
        super(MSSTopViewWindow, self).setIdentifier(identifier)
        self.mpl.canvas.map.set_identifier(identifier)

    def settingsDlg(self):
        """
        """
        settings = self.getView().getMapAppearance()
        dlg = MSS_TV_MapAppearanceDialog(parent=self, settings_dict=settings)
        dlg.setModal(True)
        if dlg.exec_() == QtGui.QDialog.Accepted:
            settings = dlg.getSettings()
            self.getView().setMapAppearance(settings)
            self.saveSettings()
            if self.docks[WMS]:
                if settings["draw_tangents"]:
                    self.docks[WMS].widget().set_tp_height(settings["tangent_height"])
                else:
                    self.docks[WMS].widget().set_tp_height(None)
            tph = None
            if settings["draw_tangents"]:
                tph = "{:.1f} km".format(settings["tangent_height"])
            if self.docks[WMS]:
                wms_widget = self.docks[WMS].widget()
                layer = wms_widget.getLayer()
                style = wms_widget.getStyle()
                if style != "":
                    style_title = wms_widget.get_layer_object(layer).styles[style]["title"]
                else:
                    style_title = None
                level = wms_widget.getLevel()
                init_time = wms_widget.getInitTime()
                valid_time = wms_widget.getValidTime()
                self.mpl.canvas.drawMetadata(title=wms_widget.get_layer_object(layer).title,
                                             init_time=init_time,
                                             valid_time=valid_time,
                                             level=level,
                                             style=style_title,
                                             tp=tph)
            else:
                self.mpl.canvas.drawMetadata(title="Top view", tp=tph)
            self.mpl.canvas.waypoints_interactor.redraw_path()
        dlg.destroy()

    def saveSettings(self):
        """Save the current settings (map appearance) to the file
           self.settingsfile.
        """
        # TODO: ConfigParser and a central configuration file might be the better solution than pickle.
        # http://stackoverflow.com/questions/200599/whats-the-best-way-to-store-simple-user-settings-in-python
        settings = self.getView().getMapAppearance()
        logging.debug("storing settings to %s" % self.settingsfile)
        fileobj = open(self.settingsfile, "w")
        pickle.dump(settings, fileobj)
        fileobj.close()

    def loadSettings(self):
        """Load settings from the file self.settingsfile.
        """
        settings = None
        if os.path.exists(self.settingsfile):
            logging.debug("loading settings from %s" % self.settingsfile)
            fileobj = open(self.settingsfile, "r")
            settings = pickle.load(fileobj)
            fileobj.close()
        self.getView().setMapAppearance(settings)


################################################################################
################################################################################

# Main program to test the window during development. The following code
# will not be executed if the view is opened from the Mission Support
# System user interface.

if __name__ == "__main__":
    # Log everything, and send it to stderr.
    # See http://docs.python.org/library/logging.html for more information
    # on the Python logging module.
    # NOTE: http://docs.python.org/library/logging.html#formatter-objects
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s (%(module)s.%(funcName)s): %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")

    import sys

    # Create an initital flight track.
    initial_waypoints = [ft.Waypoint(48.10, 11.27, 0, comments="take off"),
                         ft.Waypoint(52.32, 09.21, 200),
                         ft.Waypoint(55.10, 11.27, 0, comments="landing")]
    initial_waypoints = [ft.Waypoint(40., 25., 0),
                         ft.Waypoint(60., -10., 0),
                         ft.Waypoint(40., 10, 0)]

    waypoints_model = ft.WaypointsTableModel(QtCore.QString(""))
    waypoints_model.insertRows(0, rows=len(initial_waypoints),
                               waypoints=initial_waypoints)

    app = QtGui.QApplication(sys.argv)
    win = MSSTopViewWindow(model=waypoints_model)
    win.show()
    sys.exit(app.exec_())
