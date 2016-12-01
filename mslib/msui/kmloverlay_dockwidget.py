"""
AUTHORS:
========

* Joern Ungermann (ju)

"""

# standard library imports
import logging

# related third party imports
from PyQt4 import QtGui, QtCore  # Qt4 bindings

# local application imports
from mslib.msui import ui_kmloverlay_dockwidget as ui
from mslib.msui.mpl_map import KMLPatch
import pykml.parser


class KMLOverlayControlWidget(QtGui.QWidget, ui.Ui_KMLOverlayDockWidget):
    def __init__(self, parent=None, view=None):
        super(KMLOverlayControlWidget, self).__init__(parent)
        self.setupUi(self)
        self.view = view

        # # Currently loaded satellite overpass segments.
        # self.overpass_segments = None

        # # Connect slots and signals.
        self.connect(self.btSelectFile, QtCore.SIGNAL("clicked()"),
                     self.select_file)
        self.connect(self.btLoadFile, QtCore.SIGNAL("clicked()"),
                     self.load_file)
        self.cbOverlay.stateChanged.connect(self.update_settings)

        self.kml = None

    def update_settings(self):
        pass

    def select_file(self):
        """Slot that opens a file dialog to choose a file with satellite
           overpass predictions.
        """
        fname = QtGui.QFileDialog.getOpenFileName(self,
                                                  "Open KML Polygonal File",
                                                  "", "(*.kml)")
        if fname.isEmpty():
            return
        self.leFile.setText(fname)

    def load_file(self):
        with open(self.leFile.text()) as kmlf:
            self.kml = pykml.parser.parse(kmlf).getroot()

        if self.view:
            self.view.kmloverlay = KMLPatch(self.view.map, self.kml)
