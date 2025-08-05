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
        self.active_flighttrack = model
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

        # Get WMS settings
        wms_settings = {}
        if self.docks and self.docks[0] is not None:
            wms_settings = {
                "url": self.currurl,
                "layer": self.currlayer,
                "level": self.currlevel,
                "styles": self.currstyles,
                "flights": self.currflights,
                "vertical": self.currvertical,
            }

        # Get dock widget states
        dock_states = [dock is not None for dock in self.docks]

        return {
            "view_type": "linearview",
            "plot_title_size": view_settings.get("plot_title_size", "10pt"),
            "axes_label_size": view_settings.get("axes_label_size", "10pt"),
            "wms": wms_settings,
            "docks_open": dock_states,
        }

    def set_settings(self, view):
        """Restore Linear View settings from view_settings.json."""
        try:
            if isinstance(view, list):
                view = next((v for v in view if v.get("view_type") == "linearview"), {})

            if not hasattr(self, 'docks') or not self.docks:
                self.docks = [None, None]

            # Restore plot settings
            plot_settings = {
                "plot_title_size": str(view.get("plot_title_size", "10pt")),
                "axes_label_size": str(view.get("axes_label_size", "10pt")),
                "x_axis": view.get("x_axis", "distance"),
                "y_axis": view.get("y_axis", "pressure"),
                "y_extent": view.get("y_extent", [1000.0, 100.0]),
                "line_thickness": view.get("line_thickness", 2.0),
                "line_style": view.get("line_style", "Solid"),
                "line_transparency": view.get("line_transparency", 1.0),
                "colour_waypoints": view.get("colour_waypoints", [0, 0, 0, 1]),
                "colour_path": view.get("colour_path", [0.5, 0.5, 0.5, 0.5]),
                "draw_markers": view.get("draw_markers", True),
                "label_waypoints": view.get("label_waypoints", True)
            }
            if hasattr(self, 'mpl') and self.mpl.canvas:
                try:
                    self.mpl.canvas.plotter.set_settings(plot_settings, save=True)
                except Exception as e:
                    logging.warning("Failed to restore plot settings: %s", str(e))

            # Restore waypoints model
            if hasattr(self, 'waypoints_model') and self.waypoints_model:
                try:
                    self.setFlightTrackModel(self.waypoints_model)
                except Exception as e:
                    logging.error(
                        "Error updating plotter from shared waypoints: %s\n%s",
                        str(e), traceback.format_exc()
                    )
            else:
                logging.warning("waypoints_model not initialized; skipping waypoint redraw")

            # Restore WMS settings
            wms_settings = view.get("wms", {})
            if wms_settings:
                if len(self.docks) <= WMS or self.docks[WMS] is None:
                    self.openTool(WMS + 1)
                if self.docks[WMS]:
                    self.wms_control = self.docks[WMS].widget()
                    if isinstance(self.wms_control, wms.LSecWMSControlWidget):
                        self.restore_wms_settings(wms_settings)
                    else:
                        logging.warning(
                            "WMS control widget not available; got %s", type(self.wms_control)
                        )
                else:
                    logging.warning("WMS dock not initialized")
            else:
                logging.debug("No WMS settings provided; skipping WMS restoration")

            # Restore dock visibility
            docks_open = view.get("docks_open", [False] * len(self.docks))
            for idx, state in enumerate(docks_open):
                if idx < len(self.docks):
                    if state and self.docks[idx] is None:
                        self.openTool(idx + 1)
                    elif self.docks[idx]:
                        self.docks[idx].setVisible(state)

            # Redraw canvas
            if hasattr(self, 'mpl') and self.mpl.canvas:
                self.mpl.canvas.draw()

        except Exception as e:
            logging.error("Error in set_settings: %s\n%s", str(e), traceback.format_exc())

    def restore_wms_settings(self, wms):
        """Restore WMS settings into the existing WMS control widget (Linear View)."""
        if self.wms_control is None:
            logging.warning("Cannot restore WMS settings: wms_control does not exist")
            return

        try:
            url = wms.get("url", "")
            layer = wms.get("layer", "")
            level = wms.get("level", "")
            styles = wms.get("styles", "")
            init_time = wms.get("init_time", "")
            valid_time = wms.get("valid_time", "")

            if not url:
                logging.warning("No WMS URL provided; skipping restoration")
                return

            # Initialize WMS and update attributes
            self.wms_control.initialise_wms(url, level=level or "")
            self.currurl = url
            self.currlayer = layer
            self.currlevel = level
            self.currstyles = styles
            self.currvtime = QtCore.QDateTime.fromString(init_time, QtCore.Qt.ISODate) \
                if init_time else QtCore.QDateTime.currentDateTimeUtc()
            self.currvalidtime = QtCore.QDateTime.fromString(valid_time, QtCore.Qt.ISODate) \
                if valid_time else QtCore.QDateTime.currentDateTimeUtc()

            # Update combobox
            wms_url_combo = getattr(self.wms_control.multilayers, 'cbWMS_URL', None)
            if wms_url_combo:
                wms_url_combo.setCurrentText(url)
                wms_url_combo.currentTextChanged.emit(url)
                QtCore.QCoreApplication.processEvents()
            else:
                logging.error("WMS URL combobox 'cbWMS_URL' not found")
                return

            # Select layer and style
            if hasattr(self.wms_control.multilayers, 'listLayers'):
                self.wms_control.select_layer_and_style(
                    self.wms_control.multilayers.listLayers, layer, styles
                )
            else:
                logging.warning("listLayers not found; skipping layer selection")

            # Select row if waypoints_model exists
            if hasattr(self, 'waypoints_model') and self.waypoints_model:
                self.wms_control.row_is_selected(url, layer, styles, level, "linear")
            else:
                logging.debug("Skipping row_is_selected due to missing waypoints_model")

            # Restore init time
            if init_time and hasattr(self.wms_control, 'cbInitTime'):
                idx = self.wms_control.cbInitTime.findText(init_time)
                if idx >= 0:
                    self.wms_control.cbInitTime.setCurrentIndex(idx)
                else:
                    logging.warning("Init time %s not found in combo box", init_time)

            # Restore valid time
            if valid_time and hasattr(self.wms_control, 'cbValidTime'):
                idx = self.wms_control.cbValidTime.findText(valid_time)
                if idx >= 0:
                    self.wms_control.cbValidTime.setCurrentIndex(idx)
                    self.wms_control.leftrow_is_selected(valid_time)
                else:
                    logging.warning("Valid time %s not found in combo box", valid_time)

            # Final layer selection & canvas update
            target_layer_item = self.wms_control.find_layer_item_by_name(layer)
            if target_layer_item:
                self.wms_control.multilayers.current_layer = target_layer_item
                self.wms_control.call_get_lsec()
                self.wms_connected = True
                if hasattr(self, 'mpl') and self.mpl.canvas:
                    self.mpl.canvas.redraw_map()
            else:
                logging.warning("Layer '%s' not found; skipping call_get_vsec", layer)

        except Exception as e:
            logging.error("Error restoring WMS settings: %s\n%s", str(e), traceback.format_exc())
