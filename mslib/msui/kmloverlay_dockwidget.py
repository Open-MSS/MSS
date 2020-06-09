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
from fastkml import kml
# from lxml import etree, objectify
import os
from matplotlib import patheffects

from mslib.msui.mss_qt import QtGui, QtWidgets, get_open_filename
from mslib.msui.mss_qt import ui_kmloverlay_dockwidget as ui
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

    def compute_xy(self, coordinates):
        #coords = str(coordinates).split()
        # lons, lats = [[float(_x.split(" ")[_i]) for _x in coords] for _i in range(2)]
        lons , lats = (coordinates.x, coordinates.y)
        return self.map(lons, lats)

    def add_polygon(self, polygon, style, _):
        """
        Plot KML polygons

        :param polygon: pykml object specifying a polygon
        """
        kwargs = style.get("LineStyle", {"linewidth": self.linewidth, "color": self.color})
        for boundary in ["outerBoundaryIs", "innerBoundaryIs"]:
            if hasattr(polygon, boundary):
                x, y = self.compute_xy(getattr(polygon, boundary).LinearRing.coordinates)
                self.patches.append(self.map.plot(x, y, "-", zorder=10, **kwargs))

    def add_point(self, point, style, name):
        """
        Plot KML point

        :param point: pykml object specifying point
        :param name: name of placemark for annotation
        """
        x, y = self.compute_xy(point.geometry)
        self.patches.append(self.map.plot(x, y, "o", zorder=10, color=self.color))
        if name is not None:
            self.patches.append([self.map.ax.annotate(
                name, xy=(x, y), xycoords="data", xytext=(5, 5), textcoords='offset points', zorder=10,
                path_effects=[patheffects.withStroke(linewidth=2, foreground='w')])])

    def add_line(self, line, style, _):
        """
        Plot KML line

        :param line: pykml LineString object
        """
        kwargs = style.get("LineStyle", {"linewidth": self.linewidth, "color": self.color})
        x, y = self.compute_xy(line.coordinates)
        self.patches.append(self.map.plot(x, y, "-", zorder=10, **kwargs))

    def parse_geometries(self, placemark):
        name = placemark.name
        print(name)
        styleurl = placemark.styleUrl
        # print(styleurl)
        # styleurl = str(getattr(placemark, "styleUrl", ""))
        if styleurl and len(styleurl) > 0 and styleurl[0] == "#":
            # Remove # at beginning of style marking a locally defined style.
            # general urls for styles are not supported
            styleurl = styleurl[1:]
        style = self.parse_local_styles(
            placemark, self.styles.get(styleurl, {}))
        self.add_point(placemark, style, placemark.name)
        # for attr_name, method in (
        #         ("Point", self.add_point),
        #         ("Polygon", self.add_polygon),
        #         ("LineString", self.add_line),
        #         ("MultiGeometry", self.parse_geometries)
        #         ):
        #     for attr in getattr(placemark, attr_name, []):
        #         logging.debug("Found %s", attr_name)
        #         print(attr_name)
        #         method(attr, style, name)

    def parse_placemarks(self, level): 
        
        #only works if folder exists & only if 1 folder exists.
        # k_doc = level[0]
        # doc_child = list(k_doc.features())[0]
        # for feature in doc_child.features():
        #     # if isinstance(feature, kml.Placemark):
        #         placemark = getattr(feature, "name", None)
        #         print(placemark)
        #         self.parse_geometries(placemark)

        # this works for 1 folder and only if 1 exists too. 
        # but currently supports the way code has been rewritten
        innerFeature = list(level[0].features())
        placemarks = list(innerFeature[0].features())
        for placemark in range(len(placemarks)): 
            # print(placemarks[placemark]) 
            self.parse_geometries(placemarks[placemark])
                
    # example to help

    # def read_kml(kml_text):
    #     k = kml.KML()

    #     # Reading the kml from a text string
    #     k.from_string(kml_text)

    #     k_doc = list(k.features())[0]

    #     # Getting the first document child that must be a folder or a placemark
    #     # but you can iterate over it to get multiple folders or placemarks
    #     doc_child = list(k_doc.features())[0] --> Folder

    #     lst_geoms = list()
    #     if isinstance(doc_child, kml.Folder):
    #         for feature in doc_child.features():
    #             lst_geoms.append(feature.geometry)
    #     elif isinstance(doc_child, kml.Placemark):
    #         lst_geoms.append(doc_child.geometry)

    #     # Returning the geometries found list  
    #     return lst_geoms

    
        #original

        # for placemark in getattr(level[0].features(), "Placemark", []):
        #     name = getattr(placemark, "name", None)
        #     logging.debug("Placemark: %s", name)
        #     print(placemark.name)
        #     # self.parse_geometries(placemark)
        # for folder in getattr(level, "Folder", []):
        #     name = getattr(folder, "name", None)
        #     logging.debug("Folder: %s", name)
        #     self.parse_placemarks(folder)
        

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

    def parse_styles(self, level):
        Style1 = list(level[0].styles())[0]  
        AllStyle = list(Style1.styles())[0]
        for style in getattr(AllStyle, "Style", []): 
            name = style.getattr(style, "id")
            # print(name)
            if name is None:
                continue
            self.styles[name] = {
                "LineStyle": self.get_style_params(getattr(style, "LineStyle", None)),
                "PolyStyle": self.get_style_params(getattr(style, "PolyStyle", None)),
            }

    def parse_local_styles(self, placemark, default_styles):
        logging.debug("styles before %s", default_styles)
        local_styles = copy.deepcopy(default_styles)
        for style in getattr(placemark, "Style", []):
            logging.debug("style %s", style)
            # print(style)
            for supported in ["LineStyle", "PolyStyle"]:
                if supported in local_styles and hasattr(style, supported):
                    local_styles["LineStyle"] = self.get_style_params(
                        getattr(style, supported),
                        color=local_styles[supported]["color"], linewidth=local_styles[supported]["linewidth"])
                elif hasattr(style, supported):
                    local_styles["LineStyle"] = self.get_style_params(getattr(style, supported))
        logging.debug("styles after %s", local_styles)
        # print(local_styles)
        return local_styles

    def draw(self):
        """Do the actual plotting of the patch.
        """
        # Plot satellite track.
        self.styles = {}
        # if not self.overwrite:
        #     self.parse_styles(self.kml)
        self.parse_placemarks(self.kml)

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
        self.view = view
        self.kml = None
        self.patch = None

        # Connect slots and signals.
        self.btSelectFile.clicked.connect(self.select_file)
        self.btLoadFile.clicked.connect(self.load_file)
        self.pbSelectColour.clicked.connect(self.select_colour)
        self.cbOverlay.stateChanged.connect(self.update_settings)
        self.dsbLineWidth.valueChanged.connect(self.update_settings)
        self.cbManualStyle.stateChanged.connect(self.update_settings)

        self.cbOverlay.setChecked(True)
        self.cbOverlay.setEnabled(False)
        self.cbManualStyle.setChecked(False)

        self.settings_tag = "kmldock"
        settings = load_settings_qsettings(
            self.settings_tag, {"filename": "", "linewidth": 1, "colour": (0, 0, 0, 1)})

        self.leFile.setText(settings["filename"])
        self.dsbLineWidth.setValue(settings["linewidth"])

        palette = QtGui.QPalette(self.pbSelectColour.palette())
        colour = QtGui.QColor()
        colour.setRgbF(*settings["colour"])
        palette.setColor(QtGui.QPalette.Button, colour)
        self.pbSelectColour.setPalette(palette)

    def __del__(self):
        settings = {
            "filename": str(self.leFile.text()),
            "linewidth": self.dsbLineWidth.value(),
            "colour": self.get_color()
        }
        save_settings_qsettings(self.settings_tag, settings)

    def get_color(self):
        button = self.pbSelectColour
        return QtGui.QPalette(button.palette()).color(QtGui.QPalette.Button).getRgbF()

    def update_settings(self):
        """
        Called when the visibility checkbox is toggled and hides/shows
        the overlay if loaded.
        """
        if self.view is not None and self.cbOverlay.isChecked() and self.patch is not None:
            self.view.plot_kml(self.patch)
            self.patch.update(self.cbManualStyle.isChecked(), self.get_color(), self.dsbLineWidth.value())
        elif self.patch is not None:
            self.view.plot_kml(None)

    def select_colour(self):
        button = self.pbSelectColour

        palette = QtGui.QPalette(button.palette())
        colour = palette.color(QtGui.QPalette.Button)
        colour = QtWidgets.QColorDialog.getColor(colour)
        if colour.isValid():
            palette.setColor(QtGui.QPalette.Button, colour)
            button.setPalette(palette)
        self.update_settings()

    def select_file(self):
        """Slot that opens a file dialog to choose a kml file
        """
        filename = get_open_filename(
            self, "Open KML Polygonal File", os.path.dirname(str(self.leFile.text())), "KML Files (*.kml)")
        if not filename:
            return
        self.leFile.setText(filename)
    
    def load_file(self):
        """
        Loads a KML file selected by the leFile box and constructs the
        corresponding patch.
        """
        _dirname, _name = os.path.split(self.leFile.text())
        _fs = open_fs(_dirname)
        if self.patch is not None:
            self.patch.remove()
            self.view.plot_kml(None)
            self.patch = None
            self.cbOverlay.setEnabled(False)
        try:
            with _fs.open(_name, 'r') as kmlf:

                k = kml.KML()
                k.from_string(kmlf.read().encode('utf-8'))
                 # print(k.to_string(prettyprint=True))
                self.kml = list(k.features()) # <Document>
                self.patch = KMLPatch(self.view.map, self.kml,
                                      self.cbManualStyle.isChecked(), self.get_color(), self.dsbLineWidth.value())
            self.cbOverlay.setEnabled(True)
            if self.view is not None and self.cbOverlay.isChecked():
                self.view.plot_kml(self.patch)
        except IOError as ex:
            logging.error("KML Overlay - %s: %s", type(ex), ex)
            QtWidgets.QMessageBox.critical(
                self, self.tr("KML Overlay"), self.tr("ERROR:\n{}\n{}".format(type(ex), ex)))
# except (IOError, etree.XMLSyntaxError) as ex:
