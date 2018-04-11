# -*- coding: utf-8 -*-
"""

    mslib.msui.kmloverlay_dockwidget
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Control widget to configure remote sensing overlays.

    This file is part of mss.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017 by the mss team, see AUTHORS.
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

from builtins import str

from fs import open_fs
import logging
from lxml import etree, objectify
import os

# local application imports
from mslib.msui.mss_qt import QtGui, QtWidgets, get_open_filename
from mslib.msui.mss_qt import ui_kmloverlay_dockwidget as ui
from mslib.msui.mpl_map import KMLPatch
from mslib.utils import save_settings_pickle, load_settings_pickle


KMLPARSER = objectify.makeparser(strip_cdata=False)


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
        settings = load_settings_pickle(
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
        save_settings_pickle(self.settings_tag, settings)

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
        Loads an KML file selected by the leFile box and constructs the
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
                self.kml = objectify.parse(kmlf, parser=KMLPARSER).getroot()
                self.patch = KMLPatch(self.view.map, self.kml,
                                      self.cbManualStyle.isChecked(), self.get_color(), self.dsbLineWidth.value())
            self.cbOverlay.setEnabled(True)
            if self.view is not None and self.cbOverlay.isChecked():
                self.view.plot_kml(self.patch)
        except (IOError, etree.XMLSyntaxError) as ex:
            logging.error("KML Overlay - %s: %s", type(ex), ex)
            QtWidgets.QMessageBox.critical(
                self, self.tr("KML Overlay"), self.tr(u"ERROR:\n{}\n{}".format(type(ex), ex)))
