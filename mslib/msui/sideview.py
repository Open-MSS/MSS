# -*- coding: utf-8 -*-
"""

    mslib.msui.sideview
    ~~~~~~~~~~~~~~~~~~~

    Side view module of the msui

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2025 by the MSS team, see AUTHORS.
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

import logging
import functools
import traceback
from PyQt5 import QtGui, QtWidgets, QtCore
from mslib.msui.qt5 import ui_sideview_window as ui
from mslib.msui.qt5 import ui_sideview_options as ui_opt
from mslib.msui.viewwindows import MSUIMplViewWindow
from mslib.msui import wms_control as wms
from mslib.msui.icons import icons
from mslib.utils import thermolib
from mslib.utils.config import config_loader
from mslib.utils.units import units, convert_to
from mslib.msui import autoplot_dockwidget as apd
from mslib.utils.colordialog import CustomColorDialog
from mslib.msui.flighttrack import Waypoint

# Dock window indices.
WMS = 0
AUTOPLOT = 1


class MSUI_SV_OptionsDialog(QtWidgets.QDialog, ui_opt.Ui_SideViewOptionsDialog):
    """
    Dialog to specify sideview options. User interface is specified
    in "ui_sideview_options.py".
    """
    signal_line_thickness_change = QtCore.pyqtSignal(float)
    signal_line_style_change = QtCore.pyqtSignal(str)
    signal_transparency_change = QtCore.pyqtSignal(float)

    def __init__(self, parent=None, settings=None):
        """
        Arguments:
        parent -- Qt widget that is parent to this widget.
        settings -- dictionary containing sideview options.
        """
        super().__init__(parent)
        self.setupUi(self)

        self._suffixes = ['hPa', 'km', 'hft']
        assert settings is not None

        self.setBotTopLimits(settings["vertical_axis"])
        self.sbPbot.setValue(settings["vertical_extent"][0])
        self.sbPtop.setValue(settings["vertical_extent"][1])

        flightlevels = settings["flightlevels"]
        self.tableWidget.setRowCount(len(flightlevels))
        flightlevels.sort()
        for i, level in enumerate(flightlevels):
            tableitem = QtWidgets.QTableWidgetItem(str(int(level)))
            self.tableWidget.setItem(i, 0, tableitem)

        for i in range(self.cbVerticalAxis.count()):
            if self.cbVerticalAxis.itemText(i) == settings["vertical_axis"]:
                self.cbVerticalAxis.setCurrentIndex(i)
                self.sbPbot.setSuffix(" " + self._suffixes[i])
                self.sbPtop.setSuffix(" " + self._suffixes[i])
        for i in range(self.cbVerticalAxis2.count()):
            if self.cbVerticalAxis2.itemText(i) == settings["secondary_axis"]:
                self.cbVerticalAxis2.setCurrentIndex(i)

        # Shows previously selected element in the fontsize comboboxes as the current index.
        for i in range(self.cbtitlesize.count()):
            if self.cbtitlesize.itemText(i) == settings["plot_title_size"]:
                self.cbtitlesize.setCurrentIndex(i)
        for i in range(self.cbaxessize.count()):
            if self.cbaxessize.itemText(i) == settings["axes_label_size"]:
                self.cbaxessize.setCurrentIndex(i)

        self.cbDrawFlightLevels.setChecked(settings["draw_flightlevels"])
        self.cbDrawFlightTrack.setChecked(settings["draw_flighttrack"])
        self.cbFillFlightTrack.setChecked(settings["fill_flighttrack"])
        self.cbLabelFlightTrack.setChecked(settings["label_flighttrack"])
        self.cbDrawCeiling.setChecked(settings["draw_ceiling"])
        self.cbVerticalLines.setChecked(settings["draw_verticals"])
        self.cbDrawMarker.setChecked(settings["draw_marker"])

        self.sbLineThickness.setValue(settings.get("line_thickness", 2))
        self.cbLineStyle.addItems(["Solid", "Dashed", "Dotted", "Dash-dot"])  # Item added in the list
        self.cbLineStyle.setCurrentText(settings.get("line_style", "Solid"))
        self.hsTransparencyControl.setValue(int(settings.get("line_transparency", 1.0) * 100))

        for button, ids in [(self.btFillColour, "colour_ft_fill"),
                            (self.btWaypointsColour, "colour_ft_waypoints"),
                            (self.btVerticesColour, "colour_ft_vertices"),
                            (self.btCeilingColour, "colour_ceiling")]:
            palette = QtGui.QPalette(button.palette())
            colour = QtGui.QColor()
            colour.setRgbF(*settings[ids])
            palette.setColor(QtGui.QPalette.Button, colour)
            button.setPalette(palette)

        # Connect colour button signals.
        self.cbVerticalAxis.currentIndexChanged.connect(self.verticalunitsclicked)
        self.btFillColour.clicked.connect(functools.partial(self.setColour, "ft_fill"))
        self.btWaypointsColour.clicked.connect(functools.partial(self.setColour, "ft_waypoints"))
        self.btVerticesColour.clicked.connect(functools.partial(self.setColour, "ft_vertices"))
        self.btCeilingColour.clicked.connect(functools.partial(self.setColour, "ceiling"))

        self.btAdd.clicked.connect(self.addItem)
        self.btDelete.clicked.connect(self.deleteSelected)

        self.tableWidget.itemChanged.connect(self.itemChanged)

        # Store values instead of emitting signals immediately
        self.line_thickness = settings.get("line_thickness", 2)
        self.line_style = settings.get("line_style", "Solid")
        self.line_transparency = settings.get("line_transparency", 1.0)

        self.sbLineThickness.valueChanged.connect(self.onLineThicknessChanged)
        self.cbLineStyle.currentTextChanged.connect(self.onLineStyleChanged)
        self.hsTransparencyControl.valueChanged.connect(self.onTransparencyChanged)

    def onLineThicknessChanged(self, value):
        self.line_thickness = value

    def onLineStyleChanged(self, value):
        self.line_style = value

    def onTransparencyChanged(self, value):
        self.line_transparency = value / 100

    def setBotTopLimits(self, axis_type):
        bot, top = {
            "maximum": (0, 2132),
            "pressure": (0.1, 1050),
            "pressure altitude": (0, 65),
            "flight level": (0, 2132),
        }[axis_type]
        for button in (self.sbPbot, self.sbPtop):
            button.setMinimum(bot)
            button.setMaximum(top)

    def setColour(self, which):
        """
        Slot for the colour buttons: Opens a QColorDialog and sets the
        new button face colour.
        """
        if which == "ft_fill":
            button = self.btFillColour
        elif which == "ft_vertices":
            button = self.btVerticesColour
        elif which == "ft_waypoints":
            button = self.btWaypointsColour
        elif which == "ceiling":
            button = self.btCeilingColour

        dialog = CustomColorDialog(self)
        dialog.color_selected.connect(lambda color: self.on_color_selected(which, color, button))
        dialog.show()

    def on_color_selected(self, which, color, button):
        if color.isValid():
            if which == "ft_fill":
                # Fill colour is transparent with an alpha value of 0.15. If
                # you like to change this, modify the PathInteractor class.
                color.setAlphaF(0.15)
            palette = QtGui.QPalette(button.palette())
            palette.setColor(QtGui.QPalette.Button, color)
            button.setPalette(palette)

    def addItem(self):
        """
        Add a new item (i.e. flight level) to the table.
        """
        self.tableWidget.insertRow(0)
        self.tableWidget.setItem(0, 0, QtWidgets.QTableWidgetItem("0"))
        self.tableWidget.sortItems(0)

    def deleteSelected(self):
        """
        Remove the selected items (i.e. flight levels) from the table.
        """
        selecteditems = self.tableWidget.selectedItems()
        for item in selecteditems:
            self.tableWidget.removeRow(item.row())

    def itemChanged(self, item):
        """
        Slot that is called when an item has been changed. Checks for
        a valid integer in the range 0..999. Other values or non-numeric
        values are corrected.
        """
        try:
            flightlevel = int(item.text())
        except Exception as ex:
            logging.debug("Wildecard Exception %s - %s.", type(ex), ex)
            flightlevel = 0
        if flightlevel < 0:
            flightlevel = 0
        if flightlevel > 999:
            flightlevel = 999
        item.setText(str(flightlevel))
        self.tableWidget.sortItems(0)

    def get_flight_levels(self):
        """
        Returns the flight level values contained in the table.
        """
        return [int(self.tableWidget.item(row, 0).text())
                for row in range(self.tableWidget.rowCount())]

    def get_settings(self):
        """
        Return settings dictionary with values from the GUI elements.
        """
        settings = {
            "vertical_extent": (float(self.sbPbot.value()), float(self.sbPtop.value())),
            "vertical_axis": self.cbVerticalAxis.currentText(),
            "secondary_axis": self.cbVerticalAxis2.currentText(),
            "plot_title_size": self.cbtitlesize.currentText(),
            "axes_label_size": self.cbaxessize.currentText(),
            "flightlevels": self.get_flight_levels(),
            "draw_ceiling": self.cbDrawCeiling.isChecked(),
            "draw_verticals": self.cbVerticalLines.isChecked(),
            "draw_marker": self.cbDrawMarker.isChecked(),
            "draw_flightlevels": self.cbDrawFlightLevels.isChecked(),
            "draw_flighttrack": self.cbDrawFlightTrack.isChecked(),
            "fill_flighttrack": self.cbFillFlightTrack.isChecked(),
            "label_flighttrack": self.cbLabelFlightTrack.isChecked(),
            "line_thickness": self.line_thickness,
            "line_style": self.line_style,
            "line_transparency": self.line_transparency,
            "colour_ft_vertices":
                QtGui.QPalette(self.btVerticesColour.palette()).color(QtGui.QPalette.Button).getRgbF(),
            "colour_ft_waypoints":
                QtGui.QPalette(self.btWaypointsColour.palette()).color(QtGui.QPalette.Button).getRgbF(),
            "colour_ft_fill":
                QtGui.QPalette(self.btFillColour.palette()).color(QtGui.QPalette.Button).getRgbF(),
            "colour_ceiling":
                QtGui.QPalette(self.btCeilingColour.palette()).color(QtGui.QPalette.Button).getRgbF(),
        }
        return settings

    def verticalunitsclicked(self, index):
        new_unit = self._suffixes[index]
        old_unit = self.sbPbot.suffix().strip()
        if new_unit == old_unit:
            return
        self.setBotTopLimits("maximum")
        for sb in (self.sbPbot, self.sbPtop):
            sb.setSuffix(" " + new_unit)
            if new_unit == "hPa":
                sb.setValue(thermolib.flightlevel2pressure(
                    convert_to(sb.value(), old_unit, "hft", 1) * units.hft).to(units.hPa).magnitude)
            elif old_unit == "hPa":
                sb.setValue(convert_to(
                    thermolib.pressure2flightlevel(sb.value() * units.hPa).magnitude, "hft", new_unit))
            else:
                sb.setValue(convert_to(sb.value(), old_unit, new_unit, 1))
        self.setBotTopLimits(self.cbVerticalAxis.currentText())


class MSUISideViewWindow(MSUIMplViewWindow, ui.Ui_SideViewWindow):
    """
    PyQt window implementing a matplotlib canvas as an interactive
    side view flight track editor.
    """
    name = "Side View"

    refresh_signal_send = QtCore.pyqtSignal()
    refresh_signal_emit = QtCore.pyqtSignal()
    item_selected = QtCore.pyqtSignal(str, str, str, str)
    vtime_vals = QtCore.pyqtSignal([list])
    itemSecs_selected = QtCore.pyqtSignal(str)

    def __init__(self, parent=None, mainwindow=None, model=None, _id=None, config_settings=None, tutorial_mode=False):
        """
        Set up user interface, connect signal/slots.
        """
        super().__init__(parent, model, _id)
        self.tutorial_mode = tutorial_mode
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(icons('64x64')))
        self.settings_tag = "sideview"
        # Dock windows [WMS]:
        self.cbTools.clear()
        self.cbTools.addItems(["(select to open control)", "Vertical Section WMS", "Autoplot"])
        self.docks = [None, None]

        self.setFlightTrackModel(model)

        self.currurl = ""
        self.currlayer = ""
        self.currlevel = self.getView().get_settings()["vertical_axis"]
        self.currstyles = ""
        self.currflights = ""
        self.currvertical = ', '.join(map(str, self.getView().get_settings()["vertical_extent"]))
        self.currvtime = ""
        self.curritime = ""
        self.currlayerobj = None

        # Connect slots and signals.
        # ==========================
        # ToDo review 2026 after EOL of Win 10 if we can use parent again
        if mainwindow is not None:
            mainwindow.refresh_signal_connect.connect(self.refresh_signal_send.emit)

        # Buttons to set sideview options.
        self.btOptions.clicked.connect(self.open_settings_dialog)

        # Tool opener.
        self.cbTools.currentIndexChanged.connect(lambda ind: self.openTool(
            index=ind, parent=mainwindow, config_settings=config_settings))
        self.openTool(WMS + 1)
        if self.docks[WMS]:
            self.wms_control = self.docks[WMS].widget()
            self.docks[WMS].setVisible(True)

    def __del__(self):
        del self.mpl.canvas.waypoints_interactor

    def update_predefined_maps(self, extra):
        pass

    def openTool(self, index, parent=None, config_settings=None):
        """
        Slot that handles requests to open tool windows.
        """
        index = self.controlToBeCreated(index)
        if index >= 0:
            if index == WMS:
                # Open a WMS control widget.
                title = "Web Service Plot Control"
                widget = wms.VSecWMSControlWidget(
                    default_WMS=config_loader(dataset="default_VSEC_WMS"),
                    waypoints_model=self.waypoints_model,
                    view=self.mpl.canvas,
                    wms_cache=config_loader(dataset="wms_cache"))
                widget.vtime_data.connect(lambda vtime: self.valid_time_vals(vtime))
                widget.base_url_changed.connect(lambda url: self.url_val_changed(url))
                widget.layer_changed.connect(lambda layer: self.layer_val_changed(layer))
                widget.styles_changed.connect(lambda styles: self.styles_val_changed(styles))
                widget.itime_changed.connect(lambda styles: self.itime_val_changed(styles))
                widget.vtime_changed.connect(lambda styles: self.vtime_val_changed(styles))
                self.item_selected.connect(lambda url, layer, style,
                                           level: widget.row_is_selected(url, layer, style, level, "side"))
                self.itemSecs_selected.connect(lambda vtime: widget.leftrow_is_selected(vtime))
                self.mpl.canvas.waypoints_interactor.signal_get_vsec.connect(widget.call_get_vsec)
            elif index == AUTOPLOT:
                title = "Autoplot (Side View)"
                widget = apd.AutoplotDockWidget(parent=self, parent2=parent,
                                                view="Side View", config_settings=config_settings)
                widget.treewidget_item_selected.connect(
                    lambda url, layer, style, level: self.tree_item_select(url, layer, style, level))
                widget.update_op_flight_treewidget.connect(
                    lambda opfl, flight: parent.update_treewidget_op_fl(opfl, flight))
            else:
                raise IndexError("invalid control index")
            # Create the actual dock widget containing <widget>.
            self.createDockWidget(index, title, widget)

    @QtCore.pyqtSlot()
    def url_val_changed(self, strr):
        self.currurl = strr

    @QtCore.pyqtSlot()
    def layer_val_changed(self, strr):
        self.currlayerobj = strr
        layerstring = str(strr)
        second_colon_index = layerstring.find(':', layerstring.find(':') + 1)
        self.currurl = layerstring[:second_colon_index].strip() if second_colon_index != -1 else layerstring.strip()
        self.currlayer = layerstring.split('|')[1].strip() if '|' in layerstring else None

    @QtCore.pyqtSlot()
    def tree_item_select(self, url, layer, style, level):
        self.item_selected.emit(url, layer, style, level)

    @QtCore.pyqtSlot()
    def level_val_changed(self, strr):
        self.currlevel = strr

    @QtCore.pyqtSlot()
    def styles_val_changed(self, strr):
        if strr is None:
            self.currstyles = ""
        else:
            self.currstyles = strr

    @QtCore.pyqtSlot()
    def vtime_val_changed(self, strr):
        self.currvtime = strr

    @QtCore.pyqtSlot()
    def itime_val_changed(self, strr):
        self.curritime = strr

    @QtCore.pyqtSlot()
    def valid_time_vals(self, vtimes_list):
        self.vtime_vals.emit(vtimes_list)

    @QtCore.pyqtSlot()
    def treePlot_item_select(self, section, vtime):
        self.itemSecs_selected.emit(vtime)

    def setFlightTrackModel(self, model):
        """
        Set the QAbstractItemModel instance that the view displays.
        """
        super().setFlightTrackModel(model)
        if self.docks[WMS] is not None:
            self.docks[WMS].widget().setFlightTrackModel(model)

    def open_settings_dialog(self):
        """
        Slot to open a dialog that lets the user specify sideview options.
        """
        settings = self.getView().get_settings()
        self.currvertical = ', '.join(map(str, settings["vertical_extent"]))
        self.currlevel = settings["vertical_axis"]
        dlg = MSUI_SV_OptionsDialog(parent=self, settings=settings)
        dlg.setModal(True)
        dlg.signal_line_thickness_change.connect(self.set_line_thickness)  # Connect to signal
        dlg.signal_line_style_change.connect(self.set_line_style)
        dlg.signal_transparency_change.connect(self.set_line_transparency)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            settings = dlg.get_settings()
            self.getView().set_settings(settings, save=True)
            self.set_line_thickness(settings["line_thickness"])
            self.set_line_style(settings["line_style"])
            self.set_line_transparency(settings["line_transparency"])
            settings.update(settings)
        self.currvertical = ', '.join(map(str, settings["vertical_extent"]))
        self.currlevel = settings["vertical_axis"]
        dlg.destroy()

    def set_line_thickness(self, thickness):
        """Set the line thickness of the flight track."""
        self.mpl.canvas.waypoints_interactor.set_line_thickness(thickness)

    def set_line_style(self, style):
        """Set the line style of the flight track"""
        self.mpl.canvas.waypoints_interactor.set_line_style(style)

    def set_line_transparency(self, transparency):
        """Set the line transparency of the flight track"""
        self.mpl.canvas.waypoints_interactor.set_line_transparency(transparency)

    def get_settings(self):
        """Return a dictionary of all side view settings."""

        # Get settings from the view (matplotlib canvas)
        view_settings = self.getView().get_settings()

        # Get flight track waypoints
        waypoints = []
        if hasattr(self, 'waypoints_model') and self.waypoints_model is not None:
            wps = self.waypoints_model.waypoints
            waypoints = [
                {"lat": wp.lat, "lon": wp.lon, "flightlevel": wp.flightlevel}
                for wp in wps
            ]

        # Get WMS settings (if connected)
        wms_settings = {}
        if self.docks[0] is not None:
            wms_settings = {
                "url": self.currurl,
                "layer": self.currlayer,
                "level": self.currlevel,
                "styles": self.currstyles,
                "init_time": self.curritime,
                "valid_time": self.currvtime,
            }

        # Get dock widget states
        dock_states = [dock is not None for dock in self.docks]

        return {
            "view_type": "sideview",
            "vertical_axis": view_settings.get("vertical_axis"),
            "vertical_extent": view_settings.get("vertical_extent"),
            "secondary_axis": view_settings.get("secondary_axis"),
            "plot_title_size": view_settings.get("plot_title_size"),
            "axes_label_size": view_settings.get("axes_label_size"),
            "flightlevels": view_settings.get("flightlevels"),
            "draw_ceiling": view_settings.get("draw_ceiling"),
            "draw_verticals": view_settings.get("draw_verticals"),
            "draw_marker": view_settings.get("draw_marker"),
            "draw_flightlevels": view_settings.get("draw_flightlevels"),
            "draw_flighttrack": view_settings.get("draw_flighttrack"),
            "fill_flighttrack": view_settings.get("fill_flighttrack"),
            "label_flighttrack": view_settings.get("label_flighttrack"),
            "line_thickness": view_settings.get("line_thickness"),
            "line_style": view_settings.get("line_style"),
            "line_transparency": view_settings.get("line_transparency"),
            "colour_ft_vertices": view_settings.get("colour_ft_vertices"),
            "colour_ft_waypoints": view_settings.get("colour_ft_waypoints"),
            "colour_ft_fill": view_settings.get("colour_ft_fill"),
            "colour_ceiling": view_settings.get("colour_ceiling"),
            "waypoints": waypoints,
            "wms": wms_settings,
            "docks_open": dock_states,
        }

    def restore_wms_settings(self, wms):
        """
        Restore WMS settings into the Side View WMS control, with waypoint validation.
        """
        logging.debug("Called restore_wms_settings for %s", self.__class__.__name__)

        if not self.wms_control:
            logging.warning("wms_control missing for %s", self.__class__.__name__)
            return

        try:
            url = wms.get("url")
            layer = wms.get("layer")
            level = wms.get("level")
            styles = wms.get("styles", "default")
            init_time = wms.get("init_time")
            valid_time = wms.get("valid_time")

            # Validate waypoints
            waypoints = getattr(self.waypoints_model, 'all_waypoint_data', lambda: [])()
            if len(waypoints) < 2:
                logging.warning("Need at least 2 waypoints, got: %s", waypoints)
                return

            # Initialize WMS service
            combo = getattr(self.wms_control.multilayers, 'cbWMS_URL', None)
            if combo and url:
                self.wms_control.initialise_wms(url, level=level or "")
                combo.setCurrentText(url)
                combo.currentTextChanged.emit(url)
            else:
                logging.warning("cbWMS_URL combobox missing or no URL provided")
                return

            # Get available layers
            available_layers = [
                self.wms_control.multilayers.listLayers.topLevelItem(i).text(0)
                for i in range(self.wms_control.multilayers.listLayers.topLevelItemCount())
            ]

            if layer in available_layers:
                selected_layer = layer
                logging.debug("Applying saved layer: %s", layer)
            else:
                logging.warning("Saved layer '%s' is not in available layers: %s",
                                layer, available_layers)
                return

            # Find and set current layer
            item = getattr(self.wms_control, 'find_layer_item_by_name', lambda _: None)(selected_layer)
            if not item:
                logging.warning("Layer '%s' not found in tree", selected_layer)
                return

            self.wms_control.multilayers.current_layer = item
            self.wms_control.select_layer_and_style(
                self.wms_control.multilayers.listLayers, selected_layer, styles)
            self.wms_control.row_is_selected(url, selected_layer, styles, level or "", "side")

            # Set init/valid times
            if init_time:
                idx = self.wms_control.cbInitTime.findText(init_time)
                if idx >= 0:
                    self.wms_control.cbInitTime.setCurrentIndex(idx)
                else:
                    logging.warning("Init time '%s' not found", init_time)
            if valid_time:
                idx = self.wms_control.cbValidTime.findText(valid_time)
                if idx >= 0:
                    self.wms_control.cbValidTime.setCurrentIndex(idx)
                    self.wms_control.leftrow_is_selected(valid_time)
                elif self.wms_control.cbValidTime.count() > 0:
                    self.wms_control.cbValidTime.setCurrentIndex(0)
                    self.wms_control.leftrow_is_selected(self.wms_control.cbValidTime.currentText())
                else:
                    logging.warning("No valid times available")
                    return

            # Fetch and draw
            if self.wms_control.multilayers.current_layer:
                self.wms_control.get_map()
                self.wms_connected = True
                self.mpl.canvas.redraw_map()
                logging.debug("WMS settings successfully restored for %s", self.__class__.__name__)
            else:
                logging.warning("current_layer is None; cannot get_map")

        except Exception as e:
            logging.error("restore_wms_settings failed: %s\n%s", e, traceback.format_exc())

    def set_settings(self, view):
        """
        Restore Side View settings:
        - vertical cross-section plot settings
        - flight track appearance
        - waypoints
        - dock visibility
        - WMS settings
        """
        try:
            plot_settings = {
                "vertical_axis": view.get("vertical_axis", "pressure"),
                "vertical_extent": view.get("vertical_extent", [1000.0, 100.0]),
                "secondary_axis": view.get("secondary_axis", "no secondary axis"),
                "plot_title_size": view.get("plot_title_size", "default"),
                "axes_label_size": view.get("axes_label_size", "default"),
                "flightlevels": view.get("flightlevels", [0]),
                "draw_ceiling": view.get("draw_ceiling", True),
                "draw_verticals": view.get("draw_verticals", True),
                "draw_marker": view.get("draw_marker", True),
                "draw_flightlevels": view.get("draw_flightlevels", True),
                "draw_flighttrack": view.get("draw_flighttrack", True),
                "fill_flighttrack": view.get("fill_flighttrack", True),
                "label_flighttrack": view.get("label_flighttrack", True),
                "line_thickness": view.get("line_thickness", 2.0),
                "line_style": view.get("line_style", "Solid"),
                "line_transparency": view.get("line_transparency", 1.0),
                "colour_ft_vertices": view.get("colour_ft_vertices", [0, 0, 0, 1]),
                "colour_ft_waypoints": view.get("colour_ft_waypoints", [0, 0, 0, 1]),
                "colour_ft_fill": view.get("colour_ft_fill", [0.5, 0.5, 0.5, 0.5]),
                "colour_ceiling": view.get("colour_ceiling", [0, 0, 1, 0.5]),
            }

            self.mpl.canvas.set_settings(plot_settings, save=True)

            # Restore waypoints
            waypoints = view.get("waypoints", [])
            if waypoints and getattr(self, 'waypoints_model', None):
                logging.debug("Restoring waypoints for Side View: %s", waypoints)

                # Validate waypoints
                valid_waypoints = []
                for wp in waypoints:
                    lat, lon = wp.get("lat"), wp.get("lon")
                    if (isinstance(lat, (int, float)) and isinstance(lon, (int, float)) and
                            -90 <= lat <= 90 and -180 <= lon <= 180):
                        valid_waypoints.append(wp)
                    else:
                        logging.warning("Invalid waypoint skipped: %s", wp)

                if len(valid_waypoints) < 2:
                    logging.warning("Insufficient valid waypoints for Side View; need at least 2: %s", valid_waypoints)
                else:
                    # Clear existing waypoints
                    row_count = self.waypoints_model.rowCount()
                    if row_count > 0:
                        self.waypoints_model.removeRows(0, row_count)

                    # Create new Waypoint objects
                    waypoints_list = [
                        Waypoint(lat=wp.get("lat", 0), lon=wp.get("lon", 0), flightlevel=wp.get("flightlevel", 0))
                        for wp in valid_waypoints
                    ]

                    # Insert new waypoints
                    self.waypoints_model.insertRows(0, rows=len(waypoints_list), waypoints=waypoints_list)

                    # Update plot
                    if getattr(self.mpl.canvas, 'waypoints_interactor', None):
                        self.mpl.canvas.waypoints_interactor.plotter.update_from_waypoints(
                            self.waypoints_model.all_waypoint_data())
                        # Removed redraw_path() to fix AttributeError
                    else:
                        logging.warning("waypoints_interactor not initialized; skipping waypoint plot")
            else:
                logging.warning("No waypoints to restore or waypoints_model not initialized")

            # Restore dock visibility
            docks_open = view.get("docks_open", [False, False])
            if hasattr(self, 'docks') and self.docks:
                for idx, state in enumerate(docks_open):
                    if idx < len(self.docks) and self.docks[idx]:
                        self.docks[idx].setVisible(state)
                    elif state and idx < len(self.docks) and self.docks[idx] is None:
                        self.openTool(idx + 1)
            else:
                logging.warning("Docks not initialized; skipping dock visibility restore")

            # Restore WMS settings
            wms = view.get("wms", {})
            if wms and self.docks[WMS]:
                self.wms_control = self.docks[WMS].widget()
                self.restore_wms_settings(wms)
            else:
                logging.warning("WMS dock not initialized or no WMS settings provided; skipping WMS restoration")

            self.currvertical = ', '.join(map(str, plot_settings["vertical_extent"]))
            self.currlevel = plot_settings["vertical_axis"]
            self.mpl.canvas.draw()
            logging.debug("Finished restoring Side View settings")
        except Exception as e:
            logging.error("Error restoring Side View settings: %s\n%s", str(e), traceback.format_exc())
