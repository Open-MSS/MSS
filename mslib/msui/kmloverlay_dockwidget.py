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
        self.kml = None
        self.patch = None

        # # Currently loaded satellite overpass segments.
        # self.overpass_segments = None

        # # Connect slots and signals.
        self.connect(self.btSelectFile, QtCore.SIGNAL("clicked()"),
                     self.select_file)
        self.connect(self.btLoadFile, QtCore.SIGNAL("clicked()"),
                     self.load_file)
        self.cbOverlay.stateChanged.connect(self.update_settings)
        self.cbOverlay.setChecked(True)
        self.cbOverlay.setEnabled(False)

    def update_settings(self):
        if self.view and self.cbOverlay.isChecked() and self.patch:
            self.view.kmloverlay = self.patch
            self.patch.update()
        else:
            if self.patch:
                self.patch.remove()
            self.view.kmloverlay = None

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
        if self.patch:
            self.patch.remove()
            self.view.kmloverlay = None
            self.patch = None
            self.cbOverlay.setEnabled(False)
        try:
            with open(self.leFile.text()) as kmlf:
                self.kml = pykml.parser.parse(kmlf).getroot()
                self.patch = KMLPatch(self.view.map, self.kml)
            self.cbOverlay.setEnabled(True)
            if self.view and self.cbOverlay.isChecked():
                self.view.kmloverlay = self.patch
        except IOError, ex:
            QtGui.QMessageBox.critical(self, self.tr("KML Overlay"),
                                       self.tr("ERROR:\n%s\n%s" % (type(ex), ex)),
                                       QtGui.QMessageBox.Ok)
