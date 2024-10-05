# -*- coding: utf-8 -*-
"""

    mslib.msui.sideview
    ~~~~~~~~~~~~~~~~~~~

    Side view module of the msui

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2024 by the MSS team, see AUTHORS.
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

# Dock window indices.
WMS = 0
AUTOPLOT = 1


class MSUI_SV_OptionsDialog(QtWidgets.QDialog, ui_opt.Ui_SideViewOptionsDialog):
    """
    Dialog to specify sideview options. User interface is specified
    in "ui_sideview_options.py".
    """

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
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            settings = dlg.get_settings()
            self.getView().set_settings(settings, save=True)
        self.currvertical = ', '.join(map(str, settings["vertical_extent"]))
        self.currlevel = settings["vertical_axis"]
        dlg.destroy()
