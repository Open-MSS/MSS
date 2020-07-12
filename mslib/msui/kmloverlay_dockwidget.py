# -*- coding: utf-8 -*-
"""

    mslib.msui.kmloverlay_dockwidget
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Control widget to configure kml overlays.

    This file is part of mss.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017-2020 by the mss team, see AUTHORS.
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

import copy
from fs import open_fs
import logging
from fastkml import kml, geometry, styles
import os
from matplotlib import patheffects

from mslib.msui.mss_qt import QtGui, QtWidgets, QtCore, get_open_filename
from mslib.msui.mss_qt import ui_kmloverlay_dockwidget as ui
from mslib.msui.mss_qt import ui_customize_kml
from mslib.utils import save_settings_qsettings, load_settings_qsettings


class KMLPatch(object):
    """
    Represents a KML overlay.

    KML overlay implementation is currently very crude and basic and most features are not supported.
    """

    def __init__(self, mapcanvas, kml, overwrite=False, color="red", linewidth=1):
        self.map = mapcanvas
        self.kml = kml
        self.patches = []
        self.color = color
        self.linewidth = linewidth
        self.overwrite = overwrite
        self.draw()

    def compute_xy(self, geometry):
        lons = []
        lats = []
        for coordinates in geometry.coords:
            lons.append(coordinates[0])
            lats.append(coordinates[1])
        return self.map(lons, lats)

    def add_point(self, point, style, name):
        """
        Plot KML point

        :param point: fastkml object specifying point
        :param name: name of placemark for annotation
        """
        x, y = (point.geometry.x, point.geometry.y)
        self.patches.append(self.map.plot(x, y, "o", zorder=10, color=self.color))
        if name is not None:
            self.patches.append([self.map.ax.annotate(
                name, xy=(x, y), xycoords="data", xytext=(5, 5), textcoords='offset points', zorder=10,
                path_effects=[patheffects.withStroke(linewidth=2, foreground='w')])])

    def add_line(self, line, style, name):
        """
        Plot KML line

        :param line: fastkml LineString object
        """
        kwargs = style.get("LineStyle", {"linewidth": self.linewidth, "color": self.color})
        x, y = self.compute_xy(line.geometry)
        self.patches.append(self.map.plot(x, y, "-", zorder=10, **kwargs))

    def add_polygon(self, polygon, style, _):
        """
        Plot KML polygons

        :param polygon: fastkml object specifying a polygon
        """

        kwargs = style.get("LineStyle", {"linewidth": self.linewidth, "color": self.color})
        x, y = self.compute_xy(polygon.geometry.exterior)
        self.patches.append(self.map.plot(x, y, "-", zorder=10, **kwargs))

    def parse_geometries(self, placemark):
        name = placemark.name
        styleurl = placemark.styleUrl
        if styleurl and len(styleurl) > 0 and styleurl[0] == "#":
            # Remove # at beginning of style marking a locally defined style.
            # general urls for styles are not supported
            styleurl = styleurl[1:]
        style = self.parse_local_styles(placemark, self.styles.get(styleurl, {}))
        if hasattr(placemark, "geometry"):
            if isinstance(placemark.geometry, geometry.Point):
                self.add_point(placemark, style, placemark.name)
            if isinstance(placemark.geometry, geometry.LineString):
                self.add_line(placemark, style, placemark.name)
            if isinstance(placemark.geometry, geometry.Polygon):
                self.add_polygon(placemark, style, placemark.name)

    def parse_placemarks(self, document):
        for feature in document:
            if isinstance(feature, kml.Placemark):  # when there is no folder
                placemark = feature
                self.parse_geometries(placemark)
        for feature in document:
            if isinstance(feature, kml.Folder):
                self.parse_placemarks(list(feature.features()))
            if isinstance(feature, kml.Document):  # Document inside another document
                self.parse_placemarks(list(feature.features()))

    def get_style_params(self, style, color=None, linewidth=None):
        if color is None:
            color = self.color
        if linewidth is None:
            linewidth = self.linewidth
        result = {
            "color": str(getattr(style, "color", "")),
            "linewidth": float(getattr(style, "width", linewidth))
        }
        logging.debug("color before %s", result["color"])
        if len(result["color"]) == 7 and result["color"][0] == "#":
            result["color"] = [(int(result["color"][i:i + 2], 16) / 255.) for i in range(1, 8, 2)]
        elif len(result["color"]) == 8:
            result["color"] = [(int(result["color"][i:i + 2], 16) / 255.) for i in range(0, 8, 2)][::-1]
        else:
            result["color"] = color
        logging.debug("color after %s", result["color"])
        return result

    def parse_styles(self, kml_doc):
        # exterior_style : <Style> OUTSIDE placemarks
        # interior style : within <Style>
        for exterior_style in kml_doc.styles():
            if isinstance(exterior_style, styles.Style):
                name = exterior_style.id
                if name is None:
                    continue
                self.styles[name] = {}
                interior_style = exterior_style.styles()
                for style in interior_style:
                    if isinstance(style, styles.LineStyle):
                        self.styles[name]["LineStyle"] = self.get_style_params(style)
                    elif isinstance(style, styles.PolyStyle):
                        self.styles[name]["PolyStyle"] = self.get_style_params(style)

    def parse_local_styles(self, placemark, default_styles):
        # exterior_style : <Style> INSIDE placemarks
        # interior_style : within <Style>
        logging.debug("styles before %s", default_styles)
        local_styles = copy.deepcopy(default_styles)
        for exterior_style in placemark.styles():
            interior_style = exterior_style.styles()
            for style in interior_style:
                for supported, supported_type in (('LineStyle', styles.LineStyle), ('PolyStyle', styles.PolyStyle)):
                    if isinstance(style, supported_type) and supported in local_styles:
                        local_styles[supported] = self.get_style_params(
                            style,
                            color=local_styles[supported]['color'],
                            linewidth=local_styles[supported]['linewidth'])
                    elif isinstance(style, supported_type):
                        local_styles[supported] = self.get_style_params(style)
        return local_styles

    def draw(self):
        """Do the actual plotting of the patch.
        """
        # Plot satellite track.
        self.styles = {}
        if not self.overwrite:
            kml_doc = list(self.kml.features())[0]  # All kml files start with the first <Document>
            self.parse_styles(kml_doc)
        kml_features = list(kml_doc.features())
        self.parse_placemarks(kml_features)

        self.map.ax.figure.canvas.draw()

    def update(self, overwrite=None, color=None, linewidth=None):
        """Removes the current plot of the patch and redraws the patch.
           This is necessary, for instance, when the map projection and/or
           extent has been changed.
        """
        if overwrite is not None:
            self.overwrite = overwrite
        if color is not None:
            self.color = color
        if linewidth is not None:
            self.linewidth = linewidth
        self.remove()
        self.draw()

    def remove(self):
        """Remove this satellite patch from the map canvas.
        """
        for patch in self.patches:
            for element in patch:
                element.remove()
        self.patches = []
        self.map.ax.figure.canvas.draw()


class KMLOverlayControlWidget(QtWidgets.QWidget, ui.Ui_KMLOverlayDockWidget):
    """
    This class provides the interface for accessing KML files and
    adding the appropriate patches to the TopView canvas.
    """

    def __init__(self, parent=None, view=None):
        super(KMLOverlayControlWidget, self).__init__(parent)
        self.setupUi(self)
        self.view = view  #  canvas
        self.kml = None
        self.patch = None
        self.list_items = {}  # creates dictionary of files being added
    
        # Connect slots and signals.
        self.btSelectFile.clicked.connect(self.select_file)
        self.pushButton_remove.clicked.connect(self.remove_file)
        self.pushButton_remove_all.clicked.connect(self.remove_all_files)

        self.dialog = CustomizeKMLWidget(self)
        self.listWidget.itemDoubleClicked.connect(self.open_customize_kml_dialog)
        self.dialog.pushButton_colour.clicked.connect(self.select_colour)

        self.listWidget.itemChanged.connect(self.load_file)

        self.cbManualStyle.setChecked(False)
        # self.cbManualStyle.stateChanged.connect(self.update_settings)

        self.settings_tag = "kmldock"
        settings = load_settings_qsettings(
            self.settings_tag, {"filename": "", "linewidth": 5, "colour": (0, 0, 0, 1)})

        self.directory_location = settings["filename"]
        self.dialog.dsb_linewidth.setValue(settings["linewidth"])

        palette = QtGui.QPalette(self.dialog.pushButton_colour.palette())
        colour = QtGui.QColor()
        colour.setRgbF(*settings["colour"])
        palette.setColor(QtGui.QPalette.Button, colour)
        self.dialog.pushButton_colour.setPalette(palette) # sets the last colour
        self.dialog.dsb_linewidth.valueChanged.connect(self.select_linewidth)

    def open_customize_kml_dialog(self):
        self.dialog.show()

    def __del__(self):  # destructor
        settings = {
            "filename": str(self.directory_location),
            "linewidth": self.dialog.dsb_linewidth.value(),
            "colour": self.get_color()
        }
        save_settings_qsettings(self.settings_tag, settings)

    def get_color(self):
        button = self.dialog.pushButton_colour
        return QtGui.QPalette(button.palette()).color(QtGui.QPalette.Button).getRgbF()

    def set_color(self, file):
        return self.list_items[file]["color"]
    
    def set_linewidth(self, file):
        return self.list_items[file]["linewidth"]

    def set_attribute_colour(self, file):
        if file in self.list_items:
            self.list_items[file]["color"] = self.get_color()
        self.update_settings()

    def set_attribute_linewidth(self, file):
        if file in self.list_items:
            self.list_items[file]["linewidth"] = self.dialog.dsb_linewidth.value()
        self.update_settings()

    def update_settings(self):
        """
        Called when the visibility checkbox is toggled and hides/shows
        the overlay if loaded.
        """
        if self.view is not None and self.patch is not None:
            for filename in self.list_items:
                if self.list_items[filename]["patch"] is not None:
                    self.list_items[filename]["patch"].update(self.cbManualStyle.isChecked(), self.list_items[filename]["color"], self.list_items[filename]["linewidth"])

    def select_colour(self):
        file = self.listWidget.currentItem().text()
        button = self.dialog.pushButton_colour

        palette = QtGui.QPalette(button.palette())
        colour = palette.color(QtGui.QPalette.Button)
        colour = QtWidgets.QColorDialog.getColor(colour)
        if colour.isValid():
            palette.setColor(QtGui.QPalette.Button, colour)
            button.setPalette(palette)
        self.set_attribute_colour(file)

    def select_linewidth(self):
        file = self.listWidget.currentItem().text()
        self.set_attribute_linewidth(file)

    def select_file(self):
        """Slot that opens a file dialog to choose a kml file or multiple files simultaneously
        """
        filenames = get_open_filename(
            self, "Open KML Polygonal File", os.path.dirname(str(self.directory_location)), "KML Files (*.kml)")
        for filename in filenames:
            if filename is None:
                return
            text = filename
            if text not in self.list_items:
                self.list_items[text] = {}
                self.list_items[text]["patch"] = None
                self.list_items[text]["color"] = self.get_color()
                self.list_items[text]["linewidth"] = self.dialog.dsb_linewidth.value()
                item = QtWidgets.QListWidgetItem(text)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.Checked)
                self.listWidget.addItem(item)
                self.directory_location = text
            else:
                logging.info("%s file already added", text)
        self.load_file()

    def remove_file(self):
        for index in range(self.listWidget.count()):
            if hasattr(self.listWidget.item(index), "checkState") and (
                self.listWidget.item(index).checkState() == QtCore.Qt.Checked):
                self.list_items[self.listWidget.item(index).text()]["patch"].remove() # remove object
                del self.list_items[self.listWidget.item(index).text()]
                self.listWidget.takeItem(index)
                self.remove_file()
        # self.load_file()

    def remove_all_files(self):
        self.listWidget.clear()
        for filename in self.list_items:
            self.list_items[filename]["patch"].remove()
        self.list_items = {}
        self.patch = None   

    def load_file(self):
        """
        Loads multiple KML Files simultaneously and constructs the
        corresponding patches.
        """
        if self.patch is not None:
            for filename in self.list_items:
                if self.list_items[filename]["patch"] is not None: #  None because newly initialised files will have patch : None
                    self.list_items[filename]["patch"].remove()
                
        for index in range(self.listWidget.count()):
            if hasattr(self.listWidget.item(index), "checkState") and (
                self.listWidget.item(index).checkState() == QtCore.Qt.Checked):
                _dirname, _name = os.path.split(self.listWidget.item(index).text())
                _fs = open_fs(_dirname)
                try:
                    with _fs.open(_name, 'r') as kmlf:
                        self.kml = kml.KML()
                        self.kml.from_string(kmlf.read().encode('utf-8'))
                        if self.listWidget.item(index).text() in self.list_items: #  if the file is ticked
                            if self.list_items[self.listWidget.item(index).text()]["patch"] is not None: # if file has already been added before
                                self.patch = KMLPatch(self.view.map, self.kml,
                                                      self.cbManualStyle.isChecked(),
                                                      self.set_color(self.listWidget.item(index).text()), self.set_linewidth(self.listWidget.item(index).text()))
                            else: # if new file is being added
                                self.patch = KMLPatch(self.view.map, self.kml,
                                                      self.cbManualStyle.isChecked(),
                                                      self.list_items[self.listWidget.item(index).text()]["color"], self.list_items[self.listWidget.item(index).text()]["linewidth"])
                            self.list_items[self.listWidget.item(index).text()]["patch"] = self.patch
                        
                except IOError as ex:
                    logging.error("KML Overlay - %s: %s", type(ex), ex)
                    QtWidgets.QMessageBox.critical(
                        self, self.tr("KML Overlay"), self.tr("ERROR:\n{}\n{}".format(type(ex), ex)))
        logging.info(self.list_items)
    

class CustomizeKMLWidget(QtWidgets.QDialog, ui_customize_kml.Ui_CustomizeKMLDialog):
    """
    This class provides the interface for accessing Multiple KML files simultaneously and
    adding the appropriate patches to the TopView canvas.
    """
    def __init__(self, parent=None):
        super(CustomizeKMLWidget, self).__init__(parent)
        self.setupUi(self)