# -*- coding: utf-8 -*-
"""

    mslib.msui.linearview
    ~~~~~~~~~~~~~~~~~~~

    Linear view module of the msui

    This file is part of MSS.

    :copyright: Copyright 2021 May Baer
    :copyright: Copyright 2021-2025 by the MSS team, see AUTHORS.
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
import traceback
from mslib.utils.config import config_loader
from PyQt5 import QtGui, QtWidgets, QtCore
from mslib.msui.qt5 import ui_linearview_window as ui
from mslib.msui.qt5 import ui_linearview_options as ui_opt
from mslib.msui.viewwindows import MSUIMplViewWindow
from mslib.msui import wms_control as wms
from mslib.msui.icons import icons
from mslib.msui import autoplot_dockwidget as apd
from mslib.msui import flighttrack as ft

# Dock window indices.
WMS = 0
AUTOPLOT = 1


class MSUI_LV_Options_Dialog(QtWidgets.QDialog, ui_opt.Ui_LinearViewOptionsDialog):
    """
    Dialog class to specify Linear View Options.
    """

    def __init__(self, parent=None, settings=None):
        """
        Arguments:
        parent -- Qt widget that is parent to this widget.
        settings_dict -- dictionary containing sideview options.
        """
        super().__init__(parent)
        self.setupUi(self)

        assert settings is not None

        for i in range(self.lv_cbtitlesize.count()):
            if self.lv_cbtitlesize.itemText(i) == settings["plot_title_size"]:
                self.lv_cbtitlesize.setCurrentIndex(i)

        for i in range(self.lv_cbaxessize.count()):
            if self.lv_cbaxessize.itemText(i) == settings["axes_label_size"]:
                self.lv_cbaxessize.setCurrentIndex(i)

    def get_settings(self):
        """
        Returns the specified settings from the GUI elements.
        """
        settings = {
            "plot_title_size": self.lv_cbtitlesize.currentText(),
            "axes_label_size": self.lv_cbaxessize.currentText()
        }

        return settings


class MSUILinearViewWindow(MSUIMplViewWindow, ui.Ui_LinearWindow):
    """
    PyQt window implementing a matplotlib canvas as linear flight track view.
    """
    name = "Linear View"

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
        self.settings_tag = "linearview"
        self.tutorial_mode = tutorial_mode

        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(icons('64x64')))

        # Dock windows [WMS]:
        self.cbTools.clear()
        self.cbTools.addItems(["(select to open control)", "Linear Section WMS", "Autoplot"])
        self.docks = [None, None]

        self.setFlightTrackModel(model)

        self.currurl = ""
        self.currlayer = ""
        self.currlevel = ""
        self.currstyles = ""
        self.currflights = ""
        self.currvertical = ""
        self.currvtime = ""

        # Connect slots and signals.
        # ==========================
        # ToDo review 2026 after EOL of Win 10 if we can use parent again
        if mainwindow is not None:
            mainwindow.refresh_signal_connect.connect(self.refresh_signal_send.emit)

        # Tool opener.
        self.cbTools.currentIndexChanged.connect(lambda ind: self.openTool(
            index=ind, parent=mainwindow, config_settings=config_settings))
        self.lvoptionbtn.clicked.connect(self.open_settings_dialog)

        self.openTool(WMS + 1)

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
                widget = wms.LSecWMSControlWidget(
                    default_WMS=config_loader(dataset="default_LSEC_WMS"),
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
                                           level: widget.row_is_selected(url, layer, style, level, "linear"))
                self.itemSecs_selected.connect(lambda vtime: widget.leftrow_is_selected(vtime))
                self.mpl.canvas.waypoints_interactor.signal_get_lsec.connect(widget.call_get_lsec)
            elif index == AUTOPLOT:
                title = "Autoplot (Linear View)"
                widget = apd.AutoplotDockWidget(parent=self, parent2=parent,
                                                view="Linear View", config_settings=config_settings)
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
    def level_val_changed(self, strr):
        self.currlevel = strr

    @QtCore.pyqtSlot()
    def styles_val_changed(self, strr):
        if strr is None:
            self.currstyles = ""
        else:
            self.currstyles = strr

    @QtCore.pyqtSlot()
    def itime_val_changed(self, strr):
        self.curritime = strr

    @QtCore.pyqtSlot()
    def tree_item_select(self, url, layer, style, level):
        self.item_selected.emit(url, layer, style, level)

    @QtCore.pyqtSlot()
    def valid_time_vals(self, vtimes_list):
        self.vtime_vals.emit(vtimes_list)

    @QtCore.pyqtSlot()
    def treePlot_item_select(self, section, vtime):
        self.itemSecs_selected.emit(vtime)

    @QtCore.pyqtSlot()
    def vtime_val_changed(self, strr):
        self.currvtime = strr

    @QtCore.pyqtSlot()
    def vertical_val_changed(self, strr):
        self.currvertical = strr

    def setFlightTrackModel(self, model):
        """
        Set the QAbstractItemModel instance that the view displays.
        """
        super().setFlightTrackModel(model)
        if self.docks[WMS] is not None:
            self.docks[WMS].widget().setFlightTrackModel(model)

    def open_settings_dialog(self):
        settings = self.getView().get_settings()
        dlg = MSUI_LV_Options_Dialog(parent=self, settings=settings)
        dlg.setModal(True)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            settings = dlg.get_settings()
            self.getView().plotter.set_settings(settings, save=True)
        dlg.destroy()

    def get_settings(self):
        """Return a dictionary of all linear view settings."""
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

        # Get WMS settings
        wms_settings = {}
        if self.docks and self.docks[0] is not None:
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
            "view_type": "linearview",
            "plot_title_size": view_settings.get("plot_title_size", "10pt"),
            "axes_label_size": view_settings.get("axes_label_size", "10pt"),
            "waypoints": waypoints,
            "wms": wms_settings,
            "docks_open": dock_states,
        }
    
    def set_settings(self, view):
        """
        Restore Linear View settings from a dictionary.
        """
        try:
            logging.debug("Entering set_settings for Linear View at %s", QtCore.QDateTime.currentDateTimeUtc().toString())
            view_settings = None
            if isinstance(view, list):
                for v in view:
                    if v.get("view_type") == "linearview":
                        view_settings = v
                        break
                if view_settings is None:
                    logging.warning("No linearview settings found; using defaults")
                    view_settings = {}
            else:
                view_settings = view

            if not hasattr(self, 'docks') or not self.docks:
                self.docks = [None, None]

            # Restore plot settings
            plot_settings = {
                "plot_title_size": str(view_settings.get("plot_title_size", "10pt")),
                "axes_label_size": str(view_settings.get("axes_label_size", "10pt")),
                "x_axis": view_settings.get("x_axis", "distance"),
                "y_axis": view_settings.get("y_axis", "pressure"),
                "y_extent": view_settings.get("y_extent", [1000.0, 100.0]),
                "line_thickness": view_settings.get("line_thickness", 2.0),
                "line_style": view_settings.get("line_style", "Solid"),
                "line_transparency": view_settings.get("line_transparency", 1.0),
                "colour_waypoints": view_settings.get("colour_waypoints", [0, 0, 0, 1]),
                "colour_path": view_settings.get("colour_path", [0.5, 0.5, 0.5, 0.5]),
                "draw_markers": view_settings.get("draw_markers", True),
                "label_waypoints": view_settings.get("label_waypoints", True)
            }
            if hasattr(self, 'mpl') and self.mpl.canvas:
                self.mpl.canvas.plotter.set_settings(plot_settings, save=True)
                logging.debug("Restored plot settings: %s", plot_settings)

            # Restore waypoints
            waypoints = view_settings.get("waypoints", [])
            if waypoints and hasattr(self, 'waypoints_model') and self.waypoints_model:
                valid_waypoints = []
                for wp in waypoints:
                    lat, lon = wp.get("lat"), wp.get("lon")
                    flightlevel = wp.get("flightlevel", 0)
                    if (isinstance(lat, (int, float)) and isinstance(lon, (int, float)) and
                            -90 <= lat <= 90 and -180 <= lon <= 180 and
                            isinstance(flightlevel, (int, float)) and flightlevel >= 50):
                        valid_waypoints.append(ft.Waypoint(
                            lat=lat,
                            lon=lon,
                            flightlevel=flightlevel,
                            location=wp.get("location", ""),
                            comments=wp.get("comments", "")
                        ))
                    else:
                        logging.warning("Invalid waypoint skipped: %s", wp)
                
                if len(valid_waypoints) < 2:
                    valid_waypoints = [
                        ft.Waypoint(lat=48.137, lon=11.575, flightlevel=300, location="Munich"),
                        ft.Waypoint(lat=52.520, lon=13.405, flightlevel=300, location="Berlin")
                    ]
                    logging.info("Inserted default waypoints: %s", [
                        {"lat": wp.lat, "lon": wp.lon, "flightlevel": wp.flightlevel}
                        for wp in valid_waypoints
                    ])
                
                row_count = self.waypoints_model.rowCount()
                if row_count > 0:
                    self.waypoints_model.removeRows(0, row_count)
                self.waypoints_model.insertRows(0, rows=len(valid_waypoints), waypoints=valid_waypoints)
                
                if hasattr(self, 'mpl') and self.mpl.canvas and hasattr(self.mpl.canvas, 'waypoints_interactor'):
                    try:
                        self.mpl.canvas.waypoints_interactor.plotter.update_from_waypoints(
                            self.waypoints_model.all_waypoint_data())
                        logging.debug("Updated Linear View with waypoints")
                    except Exception as e:
                        logging.error("Error updating waypoints in plotter: %s", str(e))
                else:
                    logging.warning("waypoints_interactor not initialized; skipping waypoint plot")
            else:
                logging.warning("No waypoints to restore or waypoints_model not initialized")

            # Restore WMS settings
            wms_settings = view_settings.get("wms", {})
            if wms_settings:
                if len(self.docks) < 1 or self.docks[0] is None:
                    self.openTool(WMS + 1)
                if len(self.docks) > 0 and self.docks[0] is not None:
                    self.wms_control = self.docks[0].widget()
                    if self.wms_control and isinstance(self.wms_control, wms.LSecWMSControlWidget):
                        self.restore_wms_settings(wms_settings)
                    else:
                        logging.warning("WMS control widget not available; got %s", type(self.wms_control))
                else:
                    logging.warning("WMS dock not initialized")
            else:
                logging.debug("No WMS settings provided; skipping WMS restoration")

            # Restore dock states
            docks_open = view_settings.get("docks_open", [False, False])
            if hasattr(self, 'docks') and self.docks:
                for idx, state in enumerate(docks_open):
                    if idx < len(self.docks):
                        if state and self.docks[idx] is None:
                            self.openTool(idx + 1)
                        elif self.docks[idx]:
                            self.docks[idx].setVisible(state)

            # Redraw canvas
            if hasattr(self, 'mpl') and self.mpl.canvas:
                self.mpl.canvas.draw()
                logging.debug("Redrew Linear View canvas")
        except Exception as e:
            logging.error("Error in set_settings: %s\n%s", str(e), traceback.format_exc())

    def restore_wms_settings(self, wms):
        """
        Restore WMS settings for Linear View.
        """
        if self.wms_control is None:
            logging.warning("Cannot restore WMS settings for %s: wms_control does not exist", self.__class__.__name__)
            return

        try:
            url = wms.get("url", config_loader(dataset="default_LSEC_WMS"))
            layer = wms.get("layer", "")
            level = wms.get("level", "")
            styles = wms.get("styles", "default")
            init_time = wms.get("init_time", "")
            valid_time = wms.get("valid_time", "")

            waypoints = self.waypoints_model.all_waypoint_data() if hasattr(self, 'waypoints_model') else []
            if not waypoints or len(waypoints) < 2:
                default_waypoints = [
                    ft.Waypoint(lat=48.137, lon=11.575, flightlevel=300, location="Munich"),
                    ft.Waypoint(lat=52.520, lon=13.405, flightlevel=300, location="Berlin")
                ]
                if hasattr(self, 'waypoints_model') and self.waypoints_model:
                    row_count = self.waypoints_model.rowCount()
                    if row_count > 0:
                        self.waypoints_model.removeRows(0, row_count)
                    self.waypoints_model.insertRows(0, rows=len(default_waypoints), waypoints=default_waypoints)
                    waypoints = self.waypoints_model.all_waypoint_data()
                    logging.info("Inserted default waypoints for WMS: %s", waypoints)

            for wp in waypoints:
                if not (isinstance(wp.lat, (int, float)) and isinstance(wp.lon, (int, float)) and
                        -90 <= wp.lat <= 90 and -180 <= wp.lon <= 180 and
                        isinstance(wp.flightlevel, (int, float)) and wp.flightlevel >= 50):
                    logging.warning("Invalid waypoint coordinates or flightlevel: %s", wp)
                    return

            wms_url_combo = getattr(self.wms_control.multilayers, 'cbWMS_URL', None)
            if wms_url_combo is None:
                logging.error("WMS URL combobox 'cbWMS_URL' not found in multilayers")
                return
            if url:
                self.wms_control.initialise_wms(url, level=level)
                wms_url_combo.setCurrentText(url)
                wms_url_combo.currentTextChanged.emit(url)

            available_layers = [self.wms_control.multilayers.listLayers.topLevelItem(i).text(0)
                                for i in range(self.wms_control.multilayers.listLayers.topLevelItemCount())]
            selected_layer = layer if layer in available_layers else available_layers[0] if available_layers else None
            if selected_layer:
                self.wms_control.multilayers.current_layer = self.wms_control.find_layer_item_by_name(selected_layer)
                if self.wms_control.multilayers.current_layer:
                    self.wms_control.select_layer_and_style(self.wms_control.multilayers.listLayers, selected_layer, styles)
                    self.wms_control.row_is_selected(url, selected_layer, styles, level, "linear")
                else:
                    logging.warning("Layer '%s' not found in WMS service; skipping WMS plot", layer)
                    return
            else:
                logging.warning("No valid layers available; skipping WMS plot")
                return

            available_init_times = [self.wms_control.cbInitTime.itemText(i)
                                    for i in range(self.wms_control.cbInitTime.count())]
            if init_time and init_time in available_init_times:
                self.wms_control.cbInitTime.setCurrentText(init_time)
            elif self.wms_control.cbInitTime.count() > 0:
                self.wms_control.cbInitTime.setCurrentIndex(0)

            available_valid_times = [self.wms_control.cbValidTime.itemText(i)
                                    for i in range(self.wms_control.cbValidTime.count())]
            if valid_time and valid_time in available_valid_times:
                self.wms_control.cbValidTime.setCurrentText(valid_time)
                self.wms_control.leftrow_is_selected(valid_time)
            elif self.wms_control.cbValidTime.count() > 0:
                self.wms_control.cbValidTime.setCurrentIndex(0)
                self.wms_control.leftrow_is_selected(self.wms_control.cbValidTime.currentText())

            if self.wms_control.multilayers.current_layer:
                try:
                    self.wms_control.get_map()
                    if hasattr(self, 'mpl') and self.mpl.canvas:
                        self.mpl.canvas.redraw_map()
                    logging.debug("Successfully restored WMS settings")
                except Exception as e:
                    logging.error("WMS error during get_map: %s", str(e))
            else:
                logging.warning("No valid layer selected; skipping get_map")
        except Exception as e:
            logging.error("Error restoring WMS settings: %s\n%s", str(e), traceback.format_exc())
