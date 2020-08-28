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
import fs
import logging
from fastkml import kml, geometry, styles
from lxml import etree as et, objectify
import os
from matplotlib import patheffects

from mslib.msui.mss_qt import QtGui, QtWidgets, QtCore, get_open_filenames, get_save_filename
from mslib.msui.mss_qt import ui_kmloverlay_dockwidget as ui
from mslib.msui.mss_qt import ui_customize_kml
from mslib.utils import save_settings_qsettings, load_settings_qsettings


class KMLPatch(object):
    """
    Represents a KML overlay.
    """

    def __init__(self, mapcanvas, kml, color="red", linewidth=1):
        self.map = mapcanvas
        self.kml = kml
        self.patches = []
        self.color = color
        self.linewidth = linewidth
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
                bbox=dict(boxstyle="round, pad=0.15", fc="w"),
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
        # Exterior
        kwargs = style.get("LineStyle", {"linewidth": self.linewidth, "color": self.color})
        x, y = self.compute_xy(polygon.geometry.exterior)
        self.patches.append(self.map.plot(x, y, "-", zorder=10, **kwargs))

        # Interior Rings
        for interior in list(polygon.geometry.interiors):
            x1, y1 = self.compute_xy(interior)
            self.patches.append(self.map.plot(x1, y1, "-", zorder=10, **kwargs))

    def add_multipoint(self, point, style, name):
        """
        Plot KML points in a MultiGeometry

        :param point: fastkml object specifying point
        :param name: name of placemark for annotation
        """
        x, y = (point.x, point.y)
        self.patches.append(self.map.plot(x, y, "o", zorder=10, color=self.color))
        if name is not None:
            self.patches.append([self.map.ax.annotate(
                name, xy=(x, y), xycoords="data", xytext=(5, 5), textcoords='offset points', zorder=10,
                path_effects=[patheffects.withStroke(linewidth=2, foreground='w')])])

    def add_multiline(self, line, style, name):
        """
        Plot KML LineStrings in a MultiGeometry

        :param line: fastkml LineString object
        """
        kwargs = style.get("LineStyle", {"linewidth": self.linewidth, "color": self.color})
        x, y = self.compute_xy(line)
        self.patches.append(self.map.plot(x, y, "-", zorder=10, **kwargs))

    def add_multipolygon(self, polygon, style, _):
        """
        Plot KML polygons in a MultiGeometry

        :param polygon: fastkml object specifying a polygon
        """
        kwargs = style.get("LineStyle", {"linewidth": self.linewidth, "color": self.color})
        x, y = self.compute_xy(polygon.exterior)
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
                self.add_point(placemark, style, name)
            elif isinstance(placemark.geometry, geometry.LineString):
                self.add_line(placemark, style, name)
            elif isinstance(placemark.geometry, geometry.LinearRing):
                self.add_line(placemark, style, name)  # LinearRing can be plotted through LineString
            elif isinstance(placemark.geometry, geometry.Polygon):
                self.add_polygon(placemark, style, name)
            elif isinstance(placemark.geometry, geometry.MultiPoint):
                for geom in placemark.geometry.geoms:
                    self.add_multipoint(geom, style, name)
            elif isinstance(placemark.geometry, geometry.MultiLineString):
                for geom in placemark.geometry.geoms:
                    self.add_multiline(geom, style, name)
            elif isinstance(placemark.geometry, geometry.MultiPolygon):
                for geom in placemark.geometry.geoms:
                    self.add_multipolygon(geom, style, name)
            elif isinstance(placemark.geometry, geometry.GeometryCollection):
                for geom in placemark.geometry.geoms:
                    if geom.geom_type == "Point":
                        self.add_multipoint(geom, style, name)
                    elif geom.geom_type == "LineString":
                        self.add_multiline(geom, style, name)
                    elif geom.geom_type == "LinearRing":
                        self.add_multiline(geom, style, name)
                    elif geom.geom_type == "Polygon":
                        self.add_multipolygon(geom, style, name)

    def parse_placemarks(self, document):
        for feature in document:
            if isinstance(feature, kml.Placemark):  # when there is no folder
                placemark = feature
                self.parse_geometries(placemark)
        for feature in document:
            if isinstance(feature, kml.Folder):
                self.parse_placemarks(list(feature.features()))
            if isinstance(feature, kml.Document):  # Document present somewhere inside another doc, not consecutively
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
        kml_doc = list(self.kml.features())  # All kml files are enclosed in a single root < > and </ >
        kml_style = kml_doc[0]
        self.parse_styles(kml_style)
        self.parse_placemarks(kml_doc)

        self.map.ax.figure.canvas.draw()

    def update(self, color=None, linewidth=None):
        """Removes the current plot of the patch and redraws the patch.
           This is necessary, for instance, when the map projection and/or
           extent has been changed.
        """
        if color is not None:
            self.color = color
        if linewidth is not None:
            self.linewidth = linewidth
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
    This class provides the interface for accessing Multiple KML files and
    adding the appropriate patches to the TopView canvas.
    """

    def __init__(self, parent=None, view=None):
        super(KMLOverlayControlWidget, self).__init__(parent)
        self.setupUi(self)
        self.view = view  # canvas
        self.kml = None
        self.patch = None  # patch refers to plottings on the map
        self.dict_files = {}  # Dictionary of files added; key : patch , color , linewidth

        # Connect slots and signals.
        self.btSelectFile.clicked.connect(self.get_file)
        self.pushButton_remove.clicked.connect(self.remove_file)
        self.pushButton_select_all.clicked.connect(self.select_all)
        self.pushButton_unselect_all.clicked.connect(self.unselect_all)
        self.pushButton_merge.clicked.connect(self.merge_file)
        self.labelStatusBar.setText("Status: Click on Add KML Files to get started.")

        self.dialog = CustomizeKMLWidget(self)  # create object of dialog UI Box
        self.listWidget.itemDoubleClicked.connect(self.open_customize_kml_dialog)
        self.dialog.pushButton_colour.clicked.connect(self.select_color)

        self.listWidget.itemChanged.connect(self.load_file)  # list of files in ListWidget

        self.settings_tag = "kmldock"
        settings = load_settings_qsettings(
            self.settings_tag, {"filename": "", "linewidth": 5, "colour": (0, 0, 0, 1),
                                "saved_files": {}})  # initial settings

        self.directory_location = settings["filename"]
        self.dialog.dsb_linewidth.setValue(settings["linewidth"])

        # Restore previously opened files
        if settings["saved_files"] is not None:
            delete_files = []  # list to store non-existing files
            self.dict_files = settings["saved_files"]
            for file in self.dict_files:
                if os.path.isfile(file) is True:
                    self.create_list_item(file)
                else:
                    delete_files.append(file)  # add non-existent files to list
                    logging.info(file + " does not exist in the directory anymore")
            for file in delete_files:
                del self.dict_files[file]  # remove non-existent files from dictionary
            self.load_file()

        palette = QtGui.QPalette(self.dialog.pushButton_colour.palette())
        colour = QtGui.QColor()
        colour.setRgbF(*settings["colour"])
        palette.setColor(QtGui.QPalette.Button, colour)
        self.dialog.pushButton_colour.setPalette(palette)  # sets the last colour before closing KML Overlay
        self.dialog.dsb_linewidth.valueChanged.connect(self.select_linewidth)

    def open_customize_kml_dialog(self):
        file = self.listWidget.currentItem().text()
        # Set the colour of the Colour button to the colour of specific KML plot
        if self.dict_files[file]["color"] is not None:
            palette = QtGui.QPalette(self.dialog.pushButton_colour.palette())
            colour = QtGui.QColor()
            colour.setRgbF(*self.set_color(file))
            palette.setColor(QtGui.QPalette.Button, colour)
            self.dialog.pushButton_colour.setPalette(palette)
        # Set the linewidth value to the linewidth of specific KML plot
        if self.dict_files[file]["linewidth"] is not None:
            self.dialog.dsb_linewidth.setValue(self.set_linewidth(file))

        self.dialog.show()

    def __del__(self):  # destructor
        for x in self.dict_files:
            self.dict_files[x]["patch"] = None  # patch object has to be deleted
        settings = {
            "filename": str(self.directory_location),
            "linewidth": self.dialog.dsb_linewidth.value(),
            "colour": self.get_color(),
            "saved_files": self.dict_files
        }
        save_settings_qsettings(self.settings_tag, settings)

    def select_color(self):
        """
        Stores current selected file; select colour using Palette
        """
        file = self.listWidget.currentItem().text()
        button = self.dialog.pushButton_colour

        palette = QtGui.QPalette(button.palette())
        colour = palette.color(QtGui.QPalette.Button)
        colour = QtWidgets.QColorDialog.getColor(colour)  # opens select colour palette
        if colour.isValid():
            palette.setColor(QtGui.QPalette.Button, colour)
            button.setPalette(palette)  # finally sets the colour of the button
        self.set_attribute_color(file)

    def get_color(self):
        """
        Returns the colour of the 'pushButton_colour' Button
        """
        button = self.dialog.pushButton_colour
        return QtGui.QPalette(button.palette()).color(QtGui.QPalette.Button).getRgbF()

    def set_color(self, file):
        """
        Returns the respective colour of a given file
        """
        return self.dict_files[file]["color"]

    def set_attribute_color(self, file):
        """
        Assigns colour to given file; calls update_settings
        """
        if file in self.dict_files:
            self.dict_files[file]["color"] = self.get_color()
        self.update_settings()
        self.checklistitem(file)

    def select_linewidth(self):
        """
        Stores current selected file; calls set_attribute_linewidth
        """
        file = self.listWidget.currentItem().text()
        self.set_attribute_linewidth(file)

    def set_linewidth(self, file):
        """
        Returns the respective linewidth of a given file
        """
        return self.dict_files[file]["linewidth"]

    def set_attribute_linewidth(self, file):
        """
        Assigns linewidth to given file; calls update_settings
        """
        if file in self.dict_files:
            self.dict_files[file]["linewidth"] = self.dialog.dsb_linewidth.value()
        self.update_settings()
        self.checklistitem(file)

    def checklistitem(self, file):
        """
        Checks the file item in ListWidget
        """
        item_list = self.listWidget.findItems(file, QtCore.Qt.MatchExactly)
        for item in item_list:
            index = self.listWidget.row(item)
            self.listWidget.item(index).setCheckState(QtCore.Qt.Checked)

    def update_settings(self):
        """
        Updates the new values of linewidth and colour for individual files
        """
        if self.view is not None and self.patch is not None:
            for filename in self.dict_files:
                if self.dict_files[filename]["patch"] is not None:
                    self.dict_files[filename]["patch"].update(self.dict_files[filename]["color"],
                                                              self.dict_files[filename]["linewidth"])
        self.load_file()  # important since changes need to be refreshed

    def get_file(self):
        """Slot that opens a file dialog to choose a kml file or multiple files simultaneously
        """
        filenames = get_open_filenames(
            self, "Open KML File", os.path.dirname(str(self.directory_location)), "KML Files (*.kml)")
        if not filenames:
            return
        self.select_file(filenames)

    def select_file(self, filenames):
        """Initializes selected file/ files
        """
        for filename in filenames:
            if filename is None:
                return
            text = filename
            if text not in self.dict_files:  # prevents same file being added twice
                # initializing the nested dictionary dict_files
                self.dict_files[text] = {}
                self.dict_files[text]["patch"] = None
                self.dict_files[text]["color"] = self.get_color()
                self.dict_files[text]["linewidth"] = self.dialog.dsb_linewidth.value()
                self.directory_location = text  # Saves location of directory to open
                self.create_list_item(text)
            else:
                logging.info("%s file already added", text)
        self.labelStatusBar.setText("Status: KML Files added")
        self.load_file()

    def create_list_item(self, text):
        """
        PyQt5 method : Add items in list and add checkbox functionality
        """
        item = QtWidgets.QListWidgetItem(text)
        item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
        item.setCheckState(QtCore.Qt.Checked)
        self.listWidget.addItem(item)

    def select_all(self):  # selects all files
        if self.listWidget.count() == 0:
            self.labelStatusBar.setText("Status: No Files to select. Click on Add KML Files to get started.")
            return
        for index in range(self.listWidget.count()):
            self.listWidget.item(index).setCheckState(QtCore.Qt.Checked)
        self.labelStatusBar.setText("Status: All Files selected")

    def unselect_all(self):  # unselects all files
        if self.listWidget.count() == 0:
            self.labelStatusBar.setText("Status: No Files to unselect. Click on Add KML Files to get started.")
            return
        for index in range(self.listWidget.count()):
            self.listWidget.item(index).setCheckState(QtCore.Qt.Unchecked)
        self.labelStatusBar.setText("Status: All Files unselected")

    def remove_file(self):  # removes checked files
        for index in range(self.listWidget.count()):  # list of files in ListWidget
            if hasattr(self.listWidget.item(index), "checkState") and (
                self.listWidget.item(index).checkState() == QtCore.Qt.Checked):  # if file is checked
                if self.dict_files[self.listWidget.item(index).text()]["patch"] is not None:
                    self.dict_files[self.listWidget.item(index).text()]["patch"].remove()  # remove patch object
                del self.dict_files[self.listWidget.item(index).text()]  # del the checked files from dictionary
                self.listWidget.takeItem(index)  # remove file item from ListWidget
                self.remove_file()  # recursively since count of for loop changes every iteration due to del of items))
        self.labelStatusBar.setText("Status: KML Files removed")
        if self.listWidget.count() == 0:  # implies no files in ListWidget
            self.patch = None
        # self.load_file() # not sure to keep this or not, works either ways

    def load_file(self):
        """
        Loads multiple KML Files simultaneously and constructs the
        corresponding patches.
        """
        if self.patch is not None:  # --> self.patch has been initialized before
            for filename in self.dict_files:  # removes all patches from map, but not from dict_files
                if self.dict_files[filename]["patch"] is not None:  # since newly initialized files will have patch:None
                    self.dict_files[filename]["patch"].remove()

        for index in range(self.listWidget.count()):
            if hasattr(self.listWidget.item(index), "checkState") and (
                self.listWidget.item(index).checkState() == QtCore.Qt.Checked):
                _dirname, _name = os.path.split(self.listWidget.item(index).text())
                _fs = fs.open_fs(_dirname)
                try:
                    with _fs.open(_name, 'r') as kmlf:
                        self.kml = kml.KML()  # creates fastkml object
                        self.kml.from_string(kmlf.read().encode('utf-8'))
                        if self.listWidget.item(index).text() in self.dict_files:  # just a precautionary check
                            if self.dict_files[self.listWidget.item(index).text()]["patch"] is not None:  # if added before
                                self.patch = KMLPatch(self.view.map, self.kml,
                                                      self.set_color(self.listWidget.item(index).text()),
                                                      self.set_linewidth(self.listWidget.item(index).text()))
                            else:  # if new file is being added
                                self.patch = KMLPatch(self.view.map, self.kml,
                                                      self.dict_files[self.listWidget.item(index).text()]["color"],
                                                      self.dict_files[self.listWidget.item(index).text()]["linewidth"])
                            self.dict_files[self.listWidget.item(index).text()]["patch"] = self.patch

                except (IOError, TypeError, et.XMLSyntaxError, et.XMLSchemaError, et.XMLSchemaParseError,
                        et.XMLSchemaValidateError) as ex:  # catches KML Syntax Errors
                    logging.error("KML Overlay - %s: %s", type(ex), ex)
                    self.labelStatusBar.setText(str(self.listWidget.item(index).text()) +
                                                " is either an invalid KML File or has an error.")
                    del self.dict_files[self.listWidget.item(index).text()]  # del the checked files from dictionary
                    self.listWidget.takeItem(index)  # remove file item from ListWidget
                    QtWidgets.QMessageBox.critical(
                        self, self.tr("KML Overlay"), self.tr("ERROR:\n{}\n{}".format(type(ex), ex)))
        logging.debug(self.dict_files)

    def merge_file(self):
        checked_files = []  # list of indices of checked files
        counter = 0
        for count in range(self.listWidget.count()):
            if hasattr(self.listWidget.item(count), "checkState") and (
                self.listWidget.item(count).checkState() == QtCore.Qt.Checked):
                checked_files.append(count)
                counter = counter + 1
        if counter == 0:
            self.labelStatusBar.setText("Status: No KML File Found or Selected. Add or Select Files to Merge.")
            return

        default_filename = fs.path.join(self.directory_location, "merged_file" + ".kml")
        filename = get_save_filename(self, "Merge KML Files", default_filename, "KML Files (*.kml)")
        if filename:
            _dir_name, file_name = fs.path.split(filename)
            if filename.endswith('.kml'):
                try:
                    element = []
                    count = 0  # used to count elements in order; see usage below
                    for index in checked_files:  # index is the indices of checked files
                        _dirname, _name = os.path.split(self.listWidget.item(index).text())
                        _fs = fs.open_fs(_dirname)
                        with _fs.open(_name, 'r') as kmlf:
                            tree = et.parse(kmlf)  # parse kml file
                            root = tree.getroot()  # get the root of the file
                            self.remove_ns(root)  # removes <kml> and </kml>
                            element.append(copy.deepcopy(root[0]))
                            if index == checked_files[0]:  # first checked file becomes the top kml file, everything happens on this base
                                super_root = et.Element("Folder")
                                super_root.insert(0, element[0])  # adds <Folder> at the top of stripped KML File
                                count = count + 1
                                continue  # since the super root cannot be its own sub root
                            sub_root = et.Element("Folder")
                            sub_root.insert(0, element[count])  # count used since its consecutive, not index
                            element[0].append(sub_root)
                            count = count + 1

                    logging.debug(et.tostring(super_root, encoding='utf-8').decode('UTF-8'))
                    newkml = et.Element("kml")  # create new <kml> element
                    newkml.attrib['xmlns'] = 'http://earth.google.com/kml/2.0'  # add xmlns attribute
                    newkml.insert(0, super_root)
                    logging.debug(et.tostring(newkml, encoding='utf-8').decode('UTF-8'))
                    with _fs.open(file_name, 'w') as output:  # write file
                        output.write(et.tostring(newkml, encoding='utf-8').decode('UTF-8'))
                    path = fs.path.join(self.directory_location, "..")
                    self.labelStatusBar.setText("Status: Merged File " + file_name + " stored at " + path)
                except (OSError, IOError) as ex:
                    QtWidgets.QMessageBox.critical(
                        self, self.tr("Problem while merging KML Files:"),
                        self.tr("ERROR: {} {}".format(type(ex), ex)))
            else:
                QtWidgets.QMessageBox.warning(self, "Merge KML Files",
                                              "File extension is not '.kml'!\n{:}".format(filename))

    def remove_ns(self, root):
        """
        Removes namespace prefixes, passed on during deepcopy
        """
        try:
            for elem in root.getiterator():
                elem.tag = et.QName(elem).localname
            et.cleanup_namespaces(root)
        except Exception as e:
            for elem in root.getiterator():
                if not hasattr(elem.tag, 'find'):
                    continue
                i = elem.tag.find('}')
                if i >= 0:
                    elem.tag = elem.tag[i + 1:]
            objectify.deannotate(root, cleanup_namespaces=True)


class CustomizeKMLWidget(QtWidgets.QDialog, ui_customize_kml.Ui_CustomizeKMLDialog):
    """
    This class provides the interface for customizing individual KML Files with respect to
    linewidth and colour.
    """
    def __init__(self, parent=None):
        super(CustomizeKMLWidget, self).__init__(parent)
        self.setupUi(self)
    