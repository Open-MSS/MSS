from PyQt5 import QtWidgets, QtCore, QtGui
import traceback
import logging
import mslib.msui.wms_control


class Multilayers(QtCore.QObject):
    needs_repopulate = QtCore.pyqtSignal()

    def __init__(self, docker_widget):
        super().__init__()
        self.parent = docker_widget
        self.layers = {}
        self.layers_priority = []
        self.current_layer: Layer = None
        self.save_data = True
        self.synced_reference = Layer(None, None, None, is_empty=True)
        self.parent.listLayers.itemChanged.connect(self.multilayer_changed)
        self.parent.listLayers.itemClicked.connect(self.multilayer_clicked)
        self.parent.listLayers.itemDoubleClicked.connect(self.multilayer_doubleclicked)
        self.parent.listLayers.setVisible(True)
        self.parent.leMultiFilter.setVisible(True)
        self.parent.lFilter.setVisible(True)
        self.parent.leMultiFilter.textChanged.connect(self.filter_multilayers)
        self.parent.listLayers.setColumnWidth(1, 50)
        self.parent.listLayers.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.parent.listLayers.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.parent.listLayers.customContextMenuRequested.connect(self.right_clicked)

    def get_current_wms(self):
        if self.current_layer:
            return self.layers[self.current_layer.wms_name]["wms"]
        return None

    def reload_sync(self):
        levels, itimes, vtimes = self.get_multilayer_common_options()
        self.synced_reference.levels = levels
        self.synced_reference.itimes = itimes
        self.synced_reference.vtimes = vtimes

        if self.synced_reference.level not in self.synced_reference.levels:
            self.synced_reference.level = self.synced_reference.levels[0] if self.synced_reference.levels else None

        if self.synced_reference.itime not in self.synced_reference.itimes:
            self.synced_reference.itime = self.synced_reference.itimes[0] if self.synced_reference.itimes else None

        if self.synced_reference.vtime not in self.synced_reference.vtimes:
            self.synced_reference.vtime = self.synced_reference.vtimes[0] if self.synced_reference.vtimes else None

    def filter_multilayers(self, filter_string=None):
        """
        Hides all multilayers that don't contain the filter_string
        Shows all multilayers that do
        """
        if filter_string is None:
            filter_string = self.parent.leMultiFilter.text()

        for wms_name in self.layers:
            header = self.layers[wms_name]["header"]
            wms_hits = 0
            for child_index in range(header.childCount()):
                widget = header.child(child_index)
                if filter_string.lower() in widget.text(0).lower():
                    widget.setHidden(False)
                    wms_hits += 1
                else:
                    widget.setHidden(True)
            if wms_hits == 0:
                header.setHidden(True)
            else:
                header.setHidden(False)

    def get_multilayer_common_options(self, additional_layer=None):
        """
        Return the common option for levels, init_times and valid_times
        for all active, synchronised layers and the additional provided one
        """
        layers = self.get_active_layers(only_synced=True)
        if additional_layer:
            layers.append(additional_layer)

        elevation_values = []
        init_time_values = []
        valid_time_values = []

        wms_before = self.parent.wms

        for layer in layers:
            elevation_values.append(layer.levels)
            init_time_values.append(layer.itimes)
            valid_time_values.append(layer.vtimes)

        for values in elevation_values:
            elevation_values[0] = list(set(elevation_values[0]).intersection(values))
        for values in init_time_values:
            init_time_values[0] = list(set(init_time_values[0]).intersection(values))
        for values in valid_time_values:
            valid_time_values[0] = list(set(valid_time_values[0]).intersection(values))

        self.parent.wms = wms_before

        return sorted(elevation_values[0], key=lambda x: float(x.split()[0])) if len(elevation_values) > 0 else [], \
               sorted(init_time_values[0]) if len(init_time_values) > 0 else [], \
               sorted(valid_time_values[0]) if len(valid_time_values) > 0 else []

    def get_multilayer_priority(self, layer_widget):
        """
        Returns the priority of a layer, or None if it isn't checked
        """
        priority = self.parent.listLayers.itemWidget(layer_widget, 1)
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
        return active_layers

    def update_priority_selection(self):
        """
        Updates the priority numbers for the selected layers to the sorted self.layers_priority list
        """
        active_layers = self.get_active_layers()
        possible_values = [str(x) for x in range(1, len(active_layers) + 1)]
        for layer in active_layers:
            priority = self.parent.listLayers.itemWidget(layer, 1)
            if priority is not None:
                # Update available numbers
                priority.currentIndexChanged.disconnect(self.priority_changed)
                priority.clear()
                priority.addItems(possible_values)
                # Update selected number
                priority.setCurrentIndex(self.layers_priority.index(layer))
                priority.currentIndexChanged.connect(self.priority_changed)

    def add_multilayer(self, name, wms):
        """
        Adds a layer to the multilayer list, with the wms url as a parent
        """
        if wms.url not in self.layers:
            header = QtWidgets.QTreeWidgetItem(self.parent.listLayers)
            header.setText(0, wms.url)
            header.wms_name = wms.url
            self.layers[wms.url] = {}
            self.layers[wms.url]["header"] = header
            self.layers[wms.url]["wms"] = wms
        if name not in self.layers[wms.url]:
            layerobj = self.parent.get_layer_object(name.split(" | ")[-1])
            widget = Layer(self.layers[wms.url]["header"], self, layerobj)
            widget.setText(0, name)
            widget.setToolTip(0, "Right click a layer to sync it!" +
                              ("\n\nAbstract: " + layerobj.abstract if layerobj.abstract else ""))
            widget.wms_name = wms.url
            widget.setCheckState(0, QtCore.Qt.Unchecked)
            self.layers[wms.url][name] = widget
            self.current_layer = widget

    def multilayer_clicked(self, item):
        """
        Gets called whenever the user clicks on a layer in the multilayer list
        Makes sure the dock widget updates its data depending on the users selection
        """
        if item.childCount() > 0:
            return

        self.save_data = False
        self.current_layer = item
        if self.parent.wms is not self.layers[item.wms_name]["wms"]:
            index = self.parent.cbWMS_URL.findText(item.wms_name)
            if index != -1 and index != self.parent.cbWMS_URL.currentIndex():
                self.parent.cbWMS_URL.setCurrentIndex(index)
        self.save_data = True
        self.needs_repopulate.emit()

    def multilayer_changed(self, item):
        """
        Gets called whenever the checkmark for a layer is activate or deactivated
        Creates a priority combobox or removes it depending on the situation
        """
        if item.checkState(0) > 0 and not self.parent.listLayers.itemWidget(item, 1):
            priority = QtWidgets.QComboBox()
            priority.setFixedHeight(15)
            priority.currentIndexChanged.connect(self.priority_changed)
            self.parent.listLayers.setItemWidget(item, 1, priority)
            self.layers_priority.append(item)
            self.update_priority_selection()
        elif item.checkState(0) == 0 and self.parent.listLayers.itemWidget(item, 1):
            if item in self.layers_priority:
                self.parent.listLayers.removeItemWidget(item, 1)
                self.layers_priority.remove(item)
                self.update_priority_selection()

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

    def multilayer_doubleclicked(self, item, column):
        if item.childCount() == 0:
            item.draw()

    def right_clicked(self, pointer):
        """
        Gets called whenever the user right clicks somewhere in the multilayer list
        For now this is used to enable syncing
        """
        widget = self.parent.listLayers.itemAt(pointer)
        if not widget or widget.childCount() > 0:
            return

        if not widget.is_synced:
            levels, itimes, vtimes = self.get_multilayer_common_options(widget)
            levels_before, itimes_before, vtimes_before = self.get_multilayer_common_options()
            if (not levels and levels_before) or \
               (not itimes and itimes_before) or \
               (not vtimes and vtimes_before):
                self.multilayer_clicked(widget)
                return

        widget.is_synced = not widget.is_synced
        if widget.is_synced:
            widget.setText(0, widget.text(0) + " (synced)")
        else:
            widget.setText(0, widget.text(0).split(" (synced)")[0])

        self.reload_sync()
        self.multilayer_clicked(widget)


class Layer(QtWidgets.QTreeWidgetItem):
    def __init__(self, header, parent, layerobj, is_empty=False):
        if not is_empty:
            super().__init__(header)
            self.parent = parent
            self.layerobj = layerobj
            self.dimensions = {}
            self.extents = {}

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
        self.is_active = False

        if not is_empty:
            self._parse_layerobj()
            self._parse_levels()
            self._parse_itimes()
            self._parse_vtimes()
            self._parse_styles()

    def _parse_layerobj(self):
        """
        Parses the dimensions and extents out of the self.layerobj
        """
        self.allowed_crs = None
        lobj = self.layerobj
        while lobj is not None:
            self.dimensions.update(lobj.dimensions)
            for key in lobj.extents:
                if key not in self.extents:
                    self.extents[key] = lobj.extents[key]
            if self.allowed_crs is None:
                self.allowed_crs = getattr(lobj, "crsOptions", None)
            lobj = lobj.parent

    def _parse_levels(self):
        """
        Extracts and saves the possible levels for the layer
        """
        if "elevation" in self.extents:
            units = self.dimensions["elevation"]["units"]
            values = self.extents["elevation"]["values"]
            self.levels = ["{} ({})".format(e.strip(), units) for e in values]
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
            self.allowed_init_times = self.parent.parent.parse_time_extent(values)
            self.itimes = [_time.isoformat() + "Z" for _time in self.allowed_init_times]
            if len(self.allowed_init_times) == 0:
                msg = "cannot determine init time format"
                logging.error(msg)
                QtWidgets.QMessageBox.critical(
                    self.parent.parent, self.parent.parent.tr("Web Map Service"), self.parent.parent.tr("ERROR: {}".format(msg)))
            else:
                self.itime = self.itimes[0]

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
            self.allowed_valid_times = self.parent.parent.parse_time_extent(values)
            self.vtimes = [_time.isoformat() + "Z" for _time in self.allowed_valid_times]
            if len(self.allowed_valid_times) == 0:
                msg = "cannot determine init time format"
                logging.error(msg)
                QtWidgets.QMessageBox.critical(
                    self.parent.parent, self.parent.parent.tr("Web Map Service"), self.parent.parent.tr("ERROR: {}".format(msg)))
            else:
                self.vtime = self.vtimes[0]

    def _parse_styles(self):
        self.styles = [f"{style} | {self.layerobj.styles[style]['title']}" for style in self.layerobj.styles]
        if len(self.styles) > 0:
            self.style = self.styles[0]

    def get_level(self):
        if not self.is_synced:
            return self.level
        else:
            return self.parent.synced_reference.level

    def get_levels(self):
        if not self.is_synced:
            return self.levels
        else:
            return self.parent.synced_reference.levels

    def get_itimes(self):
        if not self.is_synced:
            return self.itimes
        else:
            return self.parent.synced_reference.itimes

    def get_itime(self):
        if not self.is_synced:
            return self.itime
        else:
            return self.parent.synced_reference.itime

    def get_vtimes(self):
        if not self.is_synced:
            return self.vtimes
        else:
            return self.parent.synced_reference.vtimes

    def get_vtime(self):
        if not self.is_synced:
            return self.vtime
        else:
            return self.parent.synced_reference.vtime

    def set_level(self, level):
        if not self.is_synced and level in self.levels:
            self.level = level
        elif self.is_synced and level in self.parent.synced_reference.levels:
            self.parent.synced_reference.level = level

    def set_itime(self, itime):
        if not self.is_synced and itime in self.itimes:
            self.itime = itime
        elif self.is_synced and itime in self.parent.synced_reference.itimes:
            self.parent.synced_reference.itime = itime

    def set_vtime(self, vtime):
        if not self.is_synced and vtime in self.vtimes:
            self.vtime = vtime
        elif self.is_synced and vtime in self.parent.synced_reference.vtimes:
            self.parent.synced_reference.vtime = vtime

    def get_layer(self):
        return self.text(0).split(" | ")[-1].split(" (synced)")[0]

    def get_style(self):
        if self.style:
            return self.style.split(" |")[0]
        return ""

    def get_level_name(self):
        if self.level:
            return self.get_level().split(" (")[0]
        return None

    def get_legend_url(self):
        style = self.get_style()
        urlstr = None
        if style and "legend" in self.layerobj.styles[style]:
            urlstr = self.layerobj.styles[style]["legend"]

        return urlstr

    def draw(self):
        if isinstance(self.parent.parent, mslib.msui.wms_control.HSecWMSControlWidget):
            self.parent.parent.get_map([self])
        else:
            self.parent.parent.get_vsec([self])

    def get_wms(self):
        return self.parent.layers[self.wms_name]["wms"]
