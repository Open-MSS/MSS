"""
    mslib.msui.multilayers
    ~~~~~~~~~~~~~~~~~~~

    This module contains classes for object oriented managing of WMS layers.
    Improves upon the old method of loading each layer on UI changes,
    the layers are all persistent and fully functional without requiring user input.

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
from PyQt5 import QtWidgets, QtCore, QtGui
import logging
import mslib.msui.wms_control
from mslib.msui.icons import icons
from mslib.msui.mss_qt import ui_wms_multilayers as ui
from mslib.utils.config import save_settings_qsettings, load_settings_qsettings


class Multilayers(QtWidgets.QDialog, ui.Ui_MultilayersDialog):
    """
    Contains all layers of all loaded WMS and provides helpful methods to manage them inside a popup dialog
    """

    needs_repopulate = QtCore.pyqtSignal()

    def __init__(self, dock_widget):
        super().__init__(parent=dock_widget)
        self.setupUi(self)
        self.setWindowFlags(QtCore.Qt.Window)
        if isinstance(dock_widget, mslib.msui.wms_control.HSecWMSControlWidget):
            self.setWindowTitle(self.windowTitle() + " (Top View)")
        elif isinstance(dock_widget, mslib.msui.wms_control.VSecWMSControlWidget):
            self.setWindowTitle(self.windowTitle() + " (Side View)")
        elif isinstance(dock_widget, mslib.msui.wms_control.LSecWMSControlWidget):
            self.setWindowTitle(self.windowTitle() + " (Linear View)")
        self.dock_widget = dock_widget
        self.layers = {}
        self.layers_priority = []
        self.current_layer: Layer = None
        self.threads = 0
        self.height = None
        self.scale = self.logicalDpiX() / 96
        self.filter_favourite = False
        self.carry_parameters = {"level": None, "itime": None, "vtime": None}
        self.is_linear = isinstance(dock_widget, mslib.msui.wms_control.LSecWMSControlWidget)
        self.settings = load_settings_qsettings("multilayers",
                                                {"favourites": [], "saved_styles": {}, "saved_colors": {}})
        self.synced_reference = Layer(None, None, None, is_empty=True)
        self.listLayers.itemChanged.connect(self.multilayer_changed)
        self.listLayers.itemClicked.connect(self.multilayer_clicked)
        self.listLayers.itemClicked.connect(self.check_icon_clicked)
        self.listLayers.itemDoubleClicked.connect(self.multilayer_doubleclicked)
        self.listLayers.setVisible(True)

        self.leMultiFilter.setVisible(True)
        self.lFilter.setVisible(True)
        self.filterFavouriteAction = self.leMultiFilter.addAction(QtGui.QIcon(icons("64x64", "star_unfilled.png")),
                                                                  QtWidgets.QLineEdit.TrailingPosition)
        self.filterRemoveAction = self.leMultiFilter.addAction(QtGui.QIcon(icons("64x64", "remove.png")),
                                                               QtWidgets.QLineEdit.TrailingPosition)
        self.filterRemoveAction.setVisible(False)
        self.filterRemoveAction.setToolTip("Click to remove the filter")
        self.filterFavouriteAction.setToolTip("Show only favourite layers")
        self.filterRemoveAction.triggered.connect(lambda x: self.remove_filter_triggered())
        self.filterFavouriteAction.triggered.connect(lambda x: self.filter_favourite_toggled())
        self.cbMultilayering.stateChanged.connect(self.toggle_multilayering)
        self.leMultiFilter.textChanged.connect(self.filter_multilayers)

        self.listLayers.setColumnWidth(2, 50)
        self.listLayers.setColumnWidth(3, 50)
        self.listLayers.setColumnWidth(1, 200)
        self.listLayers.setColumnHidden(2, True)
        self.listLayers.setColumnHidden(3, not self.is_linear)
        self.listLayers.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)

        self.delete_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Delete"), self)
        self.delete_shortcut.activated.connect(self.delete_server)
        self.delete_shortcut.setWhatsThis("Delete selected server")

    def delete_server(self, server=None):
        if not server:
            server = self.listLayers.currentItem()

        if server and not isinstance(server, Layer):
            current = self.get_current_layer()
            if current in self.layers[server.text(0)].values():
                self.current_layer = None
            for child_index in range(server.childCount()):
                widget = server.child(child_index)
                if widget in self.layers_priority:
                    self.layers_priority.remove(widget)

            index = self.listLayers.indexOfTopLevelItem(server)
            self.layers.pop(server.text(0))
            self.listLayers.takeTopLevelItem(index)
            self.update_priority_selection()
            self.needs_repopulate.emit()

    def remove_filter_triggered(self):
        self.leMultiFilter.setText("")
        if self.filter_favourite:
            self.filter_favourite_toggled()

    def filter_favourite_toggled(self):
        self.filter_favourite = not self.filter_favourite
        if self.filter_favourite:
            self.filterFavouriteAction.setIcon(QtGui.QIcon(icons("64x64", "star_filled.png")))
            self.filterFavouriteAction.setToolTip("Disable showing only favourite layers")
        else:
            self.filterFavouriteAction.setIcon(QtGui.QIcon(icons("64x64", "star_unfilled.png")))
            self.filterFavouriteAction.setToolTip("Show only favourite layers")
        self.filter_multilayers()

    def check_icon_clicked(self, item):
        """
        Checks if the mouse is pointing at an icon and handles the event accordingly
        """
        icon_width = self.height - 2

        # Clicked on layer, check favourite
        if isinstance(item, Layer):
            starts_at = 40 * self.scale
            icon_start = starts_at + 3
            if self.cbMultilayering.isChecked():
                checkbox_width = round(self.height * 0.75)
                icon_start += checkbox_width + 6
            position = self.listLayers.viewport().mapFromGlobal(QtGui.QCursor().pos())
            if icon_start <= position.x() <= icon_start + icon_width:
                self.threads += 1
                item.favourite_triggered()
                if self.filter_favourite:
                    self.filter_multilayers()
                self.threads -= 1

        # Clicked on server, check garbage bin
        elif isinstance(item, QtWidgets.QTreeWidgetItem):
            starts_at = 20 * self.scale
            icon_start = starts_at + 3
            position = self.listLayers.viewport().mapFromGlobal(QtGui.QCursor().pos())
            if icon_start <= position.x() <= icon_start + icon_width:
                self.threads += 1
                self.delete_server(item)
                self.threads -= 1

    def get_current_layer(self):
        """
        Return the current layer in the perspective of Multilayering or Singlelayering
        For Multilayering, it is the first priority syncable layer, or first priority layer if none are syncable
        For Singlelayering, it is the current selected layer
        """
        if self.cbMultilayering.isChecked():
            active_layers = self.get_active_layers()
            synced_layers = [layer for layer in active_layers if layer.is_synced]
            return synced_layers[0] if synced_layers else active_layers[0] if active_layers else None
        else:
            return self.current_layer

    def reload_sync(self):
        """
        Updates the self.synced_reference layer to contain the common options of all synced layers
        """
        levels, itimes, vtimes, crs = self.get_multilayer_common_options()
        self.synced_reference.levels = levels
        self.synced_reference.itimes = itimes
        self.synced_reference.vtimes = vtimes
        self.synced_reference.allowed_crs = crs

        if self.current_layer:
            if not self.synced_reference.level:
                self.synced_reference.level = self.current_layer.level
            if not self.synced_reference.itime:
                self.synced_reference.itime = self.current_layer.itime
            if not self.synced_reference.vtime:
                self.synced_reference.vtime = self.current_layer.vtime

        if self.synced_reference.level not in self.synced_reference.levels:
            self.synced_reference.level = levels[0] if levels else None

        if self.synced_reference.itime not in self.synced_reference.itimes:
            self.synced_reference.itime = itimes[-1] if itimes else None

        if self.synced_reference.vtime not in self.synced_reference.vtimes or \
                self.synced_reference.vtime < self.synced_reference.itime:
            self.synced_reference.vtime = next((vtime for vtime in vtimes if
                                                vtime >= self.synced_reference.itime), None) if vtimes else None

    def filter_multilayers(self, filter_string=None):
        """
        Hides all multilayers that don't contain the filter_string
        Shows all multilayers that do
        """
        if filter_string is None:
            filter_string = self.leMultiFilter.text()

        for wms_name in self.layers:
            header = self.layers[wms_name]["header"]
            wms_hits = 0
            for child_index in range(header.childCount()):
                widget = header.child(child_index)
                if filter_string.lower() in widget.text(0).lower() and (
                        not self.filter_favourite or widget.is_favourite):
                    widget.setHidden(False)
                    wms_hits += 1
                else:
                    widget.setHidden(True)
            if wms_hits == 0 and (len(filter_string) > 0 or self.filter_favourite):
                header.setHidden(True)
            else:
                header.setHidden(False)

        self.filterRemoveAction.setVisible(self.filter_favourite or len(filter_string) > 0)

    def get_multilayer_common_options(self, additional_layer=None):
        """
        Return the common option for levels, init_times, valid_times and CRS
        for all synchronised layers and the additional provided one
        """
        layers = self.get_active_layers(only_synced=True)
        if additional_layer:
            layers.append(additional_layer)

        elevation_values = []
        init_time_values = []
        valid_time_values = []
        crs_values = []

        for layer in layers:
            if len(layer.levels) > 0:
                elevation_values.append(layer.levels)
            init_time_values.append(layer.itimes)
            valid_time_values.append(layer.vtimes)
            crs_values.append(layer.allowed_crs)

        for values in elevation_values:
            elevation_values[0] = list(set(elevation_values[0]).intersection(values))
        for values in init_time_values:
            init_time_values[0] = list(set(init_time_values[0]).intersection(values))
        for values in valid_time_values:
            valid_time_values[0] = list(set(valid_time_values[0]).intersection(values))
        for values in crs_values:
            crs_values[0] = list(set(crs_values[0]).intersection(values))

        return sorted(elevation_values[0], key=lambda x: float(x.split()[0])) if len(elevation_values) > 0 else [], \
            sorted(init_time_values[0]) if len(init_time_values) > 0 else [], \
            sorted(valid_time_values[0]) if len(valid_time_values) > 0 else [], \
            sorted(crs_values[0]) if len(crs_values) > 0 else []

    def get_multilayer_priority(self, layer_widget):
        """
        Returns the priority of a layer, with a default of 999 if it wasn't explicitly set
        """
        priority = self.listLayers.itemWidget(layer_widget, 2)
        return int(priority.currentText()) if priority else 999

    def get_active_layers(self, only_synced=False):
        """
        Returns a list of every layer that has been checked
        """
        active_layers = []
        for wms_name in self.layers:
            header = self.layers[wms_name]["header"]
            for child_index in range(header.childCount()):
                widget = header.child(child_index)
                if widget.checkState(0) > 0 if not only_synced else widget.is_synced:
                    active_layers.append(widget)
        return sorted(active_layers, key=lambda layer: self.get_multilayer_priority(layer))

    def update_priority_selection(self):
        """
        Updates the priority numbers for the selected layers to the sorted self.layers_priority list
        """
        active_layers = self.get_active_layers()
        possible_values = [str(x) for x in range(1, len(active_layers) + 1)]
        for layer in active_layers:
            priority = self.listLayers.itemWidget(layer, 2)
            if priority is not None:
                # Update available numbers
                priority.currentIndexChanged.disconnect(self.priority_changed)
                priority.clear()
                priority.addItems(possible_values)
                # Update selected number
                priority.setCurrentIndex(self.layers_priority.index(layer))
                priority.currentIndexChanged.connect(self.priority_changed)

    def add_wms(self, wms):
        """
        Adds a wms to the multilayer list
        """
        if wms.url not in self.layers:
            header = QtWidgets.QTreeWidgetItem(self.listLayers)
            header.setText(0, wms.url)
            header.wms_name = wms.url
            self.layers[wms.url] = {}
            self.layers[wms.url]["header"] = header
            self.layers[wms.url]["wms"] = wms
            header.setExpanded(True)
            if not self.height:
                self.height = self.listLayers.visualItemRect(header).height()
            icon = QtGui.QIcon(icons("64x64", "bin.png"))
            header.setIcon(0, icon)

    def add_multilayer(self, name, wms, auto_select=False):
        """
        Adds a layer to the multilayer list, with the wms url as a parent
        """
        if name not in self.layers[wms.url]:
            layerobj = self.dock_widget.get_layer_object(wms, name.split(" | ")[-1])
            widget = Layer(self.layers[wms.url]["header"], self, layerobj, name=name)

            widget.wms_name = wms.url
            if layerobj.abstract:
                widget.setToolTip(0, layerobj.abstract)
            if self.cbMultilayering.isChecked():
                widget.setCheckState(0, QtCore.Qt.Unchecked)

            if self.is_linear:
                color = QtWidgets.QPushButton()
                color.setFixedHeight(15)
                color.setStyleSheet(f"background-color: {widget.color}")
                self.listLayers.setItemWidget(widget, 3, color)

                def color_changed(layer):
                    self.multilayer_clicked(layer)
                    new_color = QtWidgets.QColorDialog.getColor().name()
                    color.setStyleSheet(f"background-color: {new_color}")
                    layer.color_changed(new_color)
                    self.multilayer_clicked(layer)
                    self.dock_widget.auto_update()

                color.clicked.connect(lambda: color_changed(widget))

            if widget.style:
                style = QtWidgets.QComboBox()
                style.setFixedHeight(self.height)
                style.setFixedWidth(200)
                style.addItems(widget.styles)
                style.setCurrentIndex(style.findText(widget.style))

                def style_changed(layer):
                    layer.style = self.listLayers.itemWidget(layer, 1).currentText()
                    layer.style_changed()
                    self.multilayer_clicked(layer)
                    self.dock_widget.auto_update()

                style.currentIndexChanged.connect(lambda: style_changed(widget))
                self.listLayers.setItemWidget(widget, 1, style)

            size = QtCore.QSize()
            size.setHeight(self.height)
            widget.setSizeHint(0, size)

            self.layers[wms.url][name] = widget
            if widget.is_invalid:
                widget.setDisabled(True)
                return

            if not self.current_layer or auto_select:
                self.current_layer = widget
                self.listLayers.setCurrentItem(widget)

    def multilayer_clicked(self, item):
        """
        Gets called whenever the user clicks on a layer in the multilayer list
        Makes sure the dock widget updates its data depending on the users selection
        """
        if not isinstance(item, Layer):
            index = self.cbWMS_URL.findText(item.text(0))
            if index != -1 and index != self.cbWMS_URL.currentIndex():
                self.cbWMS_URL.setCurrentIndex(index)
            return
        if item.is_invalid:
            return

        self.threads += 1

        if self.carry_parameters["level"] in item.get_levels():
            item.set_level(self.carry_parameters["level"])
        if self.carry_parameters["itime"] in item.get_itimes():
            item.set_itime(self.carry_parameters["itime"])
        if self.carry_parameters["vtime"] in item.get_vtimes():
            item.set_vtime(self.carry_parameters["vtime"])

        if self.current_layer != item:
            self.current_layer = item
            self.listLayers.setCurrentItem(item)
            index = self.cbWMS_URL.findText(item.get_wms().url)
            if index != -1 and index != self.cbWMS_URL.currentIndex():
                self.cbWMS_URL.setCurrentIndex(index)
            self.needs_repopulate.emit()
            if not self.cbMultilayering.isChecked():
                QtCore.QTimer.singleShot(QtWidgets.QApplication.doubleClickInterval(), self.dock_widget.auto_update)
        self.threads -= 1

    def multilayer_doubleclicked(self, item, column):
        if isinstance(item, Layer):
            self.hide()

    def multilayer_changed(self, item):
        """
        Gets called whenever the checkmark for a layer is activate or deactivated
        Creates a priority combobox or removes it depending on the situation
        """
        if self.threads > 0:
            return

        if item.checkState(0) > 0 and not self.listLayers.itemWidget(item, 2):
            priority = QtWidgets.QComboBox()
            priority.setFixedHeight(self.height)
            priority.currentIndexChanged.connect(self.priority_changed)
            self.listLayers.setItemWidget(item, 2, priority)
            self.layers_priority.append(item)
            self.update_priority_selection()
            if (item.itimes or item.vtimes or item.levels) and self.is_sync_possible(item):
                item.is_synced = True
                self.reload_sync()
            elif not (item.itimes or item.vtimes or item.levels):
                item.is_active_unsynced = True
            self.update_checkboxes()
            self.needs_repopulate.emit()
            self.dock_widget.auto_update()
        elif item.checkState(0) == 0 and self.listLayers.itemWidget(item, 2):
            if item in self.layers_priority:
                self.listLayers.removeItemWidget(item, 2)
                self.layers_priority.remove(item)
                self.update_priority_selection()
            item.is_synced = False
            item.is_active_unsynced = False
            self.reload_sync()
            self.update_checkboxes()
            self.needs_repopulate.emit()
            self.dock_widget.auto_update()

    def priority_changed(self, new_index):
        """
        Get called whenever the user changes a priority for a layer
        Finds out the previous index and switches the layer position in self.layers_priority
        """
        active_layers = self.get_active_layers()
        old_index = [i for i in range(1, len(active_layers) + 1)]
        for layer in active_layers:
            value = self.get_multilayer_priority(layer)
            if value in old_index:
                old_index.remove(value)
        old_index = old_index[0] - 1

        to_move = self.layers_priority.pop(old_index)
        self.layers_priority.insert(new_index, to_move)
        self.update_priority_selection()
        self.multilayer_clicked(self.layers_priority[new_index])
        self.needs_repopulate.emit()
        self.dock_widget.auto_update()

    def update_checkboxes(self):
        """
        Activates or deactivates the checkboxes for every layer depending on whether they
        can be synchronised or not
        """
        self.threads += 1
        for wms_name in self.layers:
            header = self.layers[wms_name]["header"]
            for child_index in range(header.childCount()):
                layer = header.child(child_index)
                is_active = self.is_sync_possible(layer) or not (layer.itimes or layer.vtimes or layer.levels)
                layer.setDisabled(not is_active or layer.is_invalid)
        self.threads -= 1

    def is_sync_possible(self, layer):
        """
        Returns whether the passed layer can be synchronised with all other synchronised layers
        """
        if len(self.get_active_layers()) == 0:
            return True

        levels, itimes, vtimes, crs = self.get_multilayer_common_options(layer)
        levels_before, itimes_before, vtimes_before, crs_before = self.get_multilayer_common_options()

        return (len(levels) > 0 or (len(levels_before) == 0 and len(layer.levels) == 0)) and \
               (len(itimes) > 0 or (len(itimes_before) == 0 and len(layer.itimes) == 0)) and \
               (len(vtimes) > 0 or (len(vtimes_before) == 0 and len(layer.vtimes) == 0))

    def toggle_multilayering(self):
        """
        Toggle between checkable layers (multilayering) and single layer mode
        """
        self.threads += 1
        for wms_name in self.layers:
            header = self.layers[wms_name]["header"]
            for child_index in range(header.childCount()):
                layer = header.child(child_index)
                if self.cbMultilayering.isChecked():
                    layer.setCheckState(0, 2 if layer.is_synced or layer.is_active_unsynced else 0)
                else:
                    layer.setData(0, QtCore.Qt.CheckStateRole, QtCore.QVariant())
                    layer.setDisabled(layer.is_invalid)

        if self.cbMultilayering.isChecked():
            self.update_checkboxes()
            self.listLayers.setColumnHidden(2, False)
        else:
            self.listLayers.setColumnHidden(2, True)

        self.needs_repopulate.emit()
        self.threads -= 1


class Layer(QtWidgets.QTreeWidgetItem):
    def __init__(self, header, parent, layerobj, name=None, is_empty=False):
        super().__init__(header)
        self.parent = parent
        self.header = header
        self.layerobj = layerobj
        self.dimensions = {}
        self.extents = {}
        self.setText(0, name if name else "")

        self.levels = []
        self.level = None
        self.itimes = []
        self.itime = None
        self.itime_name = None
        self.allowed_init_times = []
        self.vtimes = []
        self.vtime = None
        self.vtime_name = None
        self.allowed_valid_times = []
        self.styles = []
        self.style = None
        self.is_synced = False
        self.is_active_unsynced = False
        self.is_favourite = False
        self.is_invalid = False

        if not is_empty:
            self._parse_layerobj()
            self._parse_levels()
            self._parse_itimes()
            self._parse_vtimes()
            self._parse_styles()
            self.is_favourite = str(self) in self.parent.settings["favourites"]
            self.show_favourite()
            if str(self) in self.parent.settings["saved_colors"]:
                self.color = self.parent.settings["saved_colors"][str(self)]
            else:
                self.color = "#00aaff"

    def _parse_layerobj(self):
        """
        Parses the dimensions and extents out of the self.layerobj
        """
        self.allowed_crs = []
        lobj = self.layerobj
        while lobj is not None:
            self.dimensions.update(lobj.dimensions)
            for key in lobj.extents:
                if key not in self.extents:
                    self.extents[key] = lobj.extents[key]
            if len(self.allowed_crs) == 0:
                self.allowed_crs = getattr(lobj, "crsOptions", None)
            lobj = lobj.parent

    def _parse_levels(self):
        """
        Extracts and saves the possible levels for the layer
        """
        if "elevation" in self.extents:
            units = self.dimensions["elevation"]["units"]
            values = self.extents["elevation"]["values"]
            self.levels = [f"{e.strip()} ({units})" for e in values]
            self.level = self.levels[0]

    def _parse_itimes(self):
        """
        Extracts and saves all init_time values for the layer
        """
        init_time_names = [x for x in ["init_time", "reference_time", "run"] if x in self.extents]

        # Both time dimension and time extent tags were found. Try to determine the
        # format of the date/time strings.
        if len(init_time_names) > 0:
            self.itime_name = init_time_names[0]
            values = self.extents[self.itime_name]["values"]
            self.allowed_init_times = sorted(self.parent.dock_widget.parse_time_extent(values))
            self.itimes = [_time.isoformat() + "Z" for _time in self.allowed_init_times]
            if len(self.allowed_init_times) == 0:
                logging.error(f"Cannot determine init time format of {self.header.text(0)} for {self.text(0)}")
                self.is_invalid = True
            else:
                self.itime = self.itimes[-1]

    def _parse_vtimes(self):
        """
        Extracts and saves all valid_time values for the layer
        """
        valid_time_names = [x for x in ["time", "forecast"] if x in self.extents]

        # Both time dimension and time extent tags were found. Try to determine the
        # format of the date/time strings.
        if len(valid_time_names) > 0:
            self.vtime_name = valid_time_names[0]
            values = self.extents[self.vtime_name]["values"]
            self.allowed_valid_times = sorted(self.parent.dock_widget.parse_time_extent(values))
            self.vtimes = [_time.isoformat() + "Z" for _time in self.allowed_valid_times]
            if len(self.allowed_valid_times) == 0:
                logging.error(f"Cannot determine valid time format of {self.header.text(0)} for {self.text(0)}")
                self.is_invalid = True
            else:
                if self.itime:
                    self.vtime = next((vtime for vtime in self.vtimes if vtime >= self.itime), self.vtimes[0])
                else:
                    self.vtime = self.vtimes[0]

    def _parse_styles(self):
        """
        Extracts and saves all styles for the layer.
        Sets the layers style to the first one, or the saved one if possible.
        """
        self.styles = [f"{style} | {self.layerobj.styles[style]['title']}" for style in self.layerobj.styles]
        if self.parent.is_linear:
            self.styles.extend(["linear | linear scaled y-axis", "log | log scaled y-axis"])
        if len(self.styles) > 0:
            self.style = self.styles[0]
            if str(self) in self.parent.settings["saved_styles"] and \
               self.parent.settings["saved_styles"][str(self)] in self.styles:
                self.style = self.parent.settings["saved_styles"][str(self)]

    def get_level(self):
        if not self.parent.cbMultilayering.isChecked() or not self.is_synced:
            return self.level
        else:
            return self.parent.synced_reference.level

    def get_levels(self):
        if not self.parent.cbMultilayering.isChecked() or not self.is_synced:
            return self.levels
        else:
            return self.parent.synced_reference.levels

    def get_itimes(self):
        if not self.parent.cbMultilayering.isChecked() or not self.is_synced:
            return self.itimes
        else:
            return self.parent.synced_reference.itimes

    def get_itime(self):
        if not self.parent.cbMultilayering.isChecked() or not self.is_synced:
            return self.itime
        else:
            return self.parent.synced_reference.itime

    def get_vtimes(self):
        if not self.parent.cbMultilayering.isChecked() or not self.is_synced:
            return self.vtimes
        else:
            return self.parent.synced_reference.vtimes

    def get_vtime(self):
        if not self.parent.cbMultilayering.isChecked() or not self.is_synced:
            return self.vtime
        else:
            return self.parent.synced_reference.vtime

    def set_level(self, level):
        if (not self.parent.cbMultilayering.isChecked() or not self.is_synced) and level in self.levels:
            self.level = level
        elif self.is_synced and level in self.parent.synced_reference.levels:
            self.parent.synced_reference.level = level

    def set_itime(self, itime):
        if (not self.parent.cbMultilayering.isChecked() or not self.is_synced) and itime in self.itimes:
            self.itime = itime
        elif self.is_synced and itime in self.parent.synced_reference.itimes:
            self.parent.synced_reference.itime = itime

        if self.get_vtime():
            if self.get_vtime() < itime:
                valid_vtime = next((vtime for vtime in self.get_vtimes() if vtime >= itime), None)
                if valid_vtime:
                    self.set_vtime(valid_vtime)
                    self.parent.carry_parameters["vtime"] = self.get_vtime()
            self.parent.needs_repopulate.emit()

    def set_vtime(self, vtime):
        if (not self.parent.cbMultilayering.isChecked() or not self.is_synced) and vtime in self.vtimes:
            self.vtime = vtime
        elif self.is_synced and vtime in self.parent.synced_reference.vtimes:
            self.parent.synced_reference.vtime = vtime

        if self.get_itime() and self.get_itime() > vtime:
            valid_itimes = [itime for itime in self.get_itimes() if itime <= vtime]
            if valid_itimes:
                self.set_itime(valid_itimes[-1])
                self.parent.needs_repopulate.emit()

    def get_layer(self):
        """
        Returns the layer name used internally by the WMS
        """
        return self.text(0).split(" | ")[-1].split(" (synced)")[0]

    def get_style(self):
        """
        Returns the style name used internally by the WMS
        """
        if self.style:
            return self.style.split(" |")[0]
        return ""

    def get_level_name(self):
        """
        Returns the level used internally by the WMS
        """
        if self.level:
            return self.get_level().split(" (")[0]

    def get_legend_url(self):
        if not self.parent.is_linear:
            style = self.get_style()
            urlstr = None
            if style and "legend" in self.layerobj.styles[style]:
                urlstr = self.layerobj.styles[style]["legend"]
            return urlstr

    def get_allowed_crs(self):
        if self.is_synced:
            return self.parent.synced_reference.allowed_crs
        else:
            return self.allowed_crs

    def draw(self):
        """
        Triggers the layer to be drawn by the WMSControlWidget
        """
        if isinstance(self.parent.dock_widget, mslib.msui.wms_control.HSecWMSControlWidget):
            self.parent.dock_widget.get_map([self])
        elif isinstance(self.parent.dock_widget, mslib.msui.wms_control.VSecWMSControlWidget):
            self.parent.dock_widget.get_vsec([self])
        else:
            self.parent.dock_widget.get_lsec([self])

    def get_wms(self):
        return self.parent.layers[self.header.text(0)]["wms"]

    def show_favourite(self):
        """
        Shows a filled star icon if this layer is a favourite layer or an unfilled one if not
        """
        if self.is_favourite:
            icon = QtGui.QIcon(icons("64x64", "star_filled.png"))
        else:
            icon = QtGui.QIcon(icons("64x64", "star_unfilled.png"))
        self.setIcon(0, icon)

    def style_changed(self):
        """
        Persistently saves the currently selected style of the layer, if it is not the first one
        """
        if self.style != self.styles[0]:
            self.parent.settings["saved_styles"][str(self)] = self.style
        else:
            self.parent.settings["saved_styles"].pop(str(self))
        save_settings_qsettings("multilayers", self.parent.settings)

    def color_changed(self, color):
        """
        Persistently saves the currently selected color of the layer, if it isn't black
        """
        self.color = color
        if self.color != 0:
            self.parent.settings["saved_colors"][str(self)] = self.color
        else:
            self.parent.settings["saved_colors"].pop(str(self))
        save_settings_qsettings("multilayers", self.parent.settings)

    def favourite_triggered(self):
        """
        Toggles whether a layer is or is not a favourite
        """
        self.is_favourite = not self.is_favourite
        self.show_favourite()
        if not self.is_favourite and str(self) in self.parent.settings["favourites"]:
            self.parent.settings["favourites"].remove(str(self))
        elif self.is_favourite and str(self) not in self.parent.settings["favourites"]:
            self.parent.settings["favourites"].append(str(self))
        save_settings_qsettings("multilayers", self.parent.settings)

    def __str__(self):
        return f"{self.header.text(0) if self.header else ''}: {self.text(0)}"
