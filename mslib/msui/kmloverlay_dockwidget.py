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

        # # Currently loaded satellite overpass segments.
        # self.overpass_segments = None
        palette = QtGui.QPalette(self.pbSelectColour.palette())
        colour = QtGui.QColor()
        colour.setRgbF(0, 0, 0, 1)
        palette.setColor(QtGui.QPalette.Button, colour)
        self.pbSelectColour.setPalette(palette)

        # # Connect slots and signals.
        self.connect(self.btSelectFile, QtCore.SIGNAL("clicked()"),
                     self.select_file)
        self.connect(self.btLoadFile, QtCore.SIGNAL("clicked()"),
                     self.load_file)
        self.pbSelectColour.clicked.connect(self.select_colour)
        self.cbOverlay.stateChanged.connect(self.update_settings)
        self.cbOverlay.setChecked(True)
        self.cbOverlay.setEnabled(False)

    def get_color(self):
        button = self.pbSelectColour
        return QtGui.QPalette(button.palette()).color(QtGui.QPalette.Button).getRgbF()

    def update_settings(self):
        """
        Called when the visibility checkbox is toggled and hides/shows
        the overlay if loaded.
        """
        if self.view and self.cbOverlay.isChecked() and self.patch:
            self.view.plotKML(self.patch)
            self.patch.update(self.get_color())
        elif self.patch:
                self.view.plotKML(None)

    def select_colour(self):
        button = self.pbSelectColour

        palette = QtGui.QPalette(button.palette())
        colour = palette.color(QtGui.QPalette.Button)
        colour = QtGui.QColorDialog.getColor(colour)
        if colour.isValid():
            palette.setColor(QtGui.QPalette.Button, colour)
            button.setPalette(palette)
        self.update_settings()

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
        """
        Loads an KML file selected by the leFile box and constructs the
        corresponding patch.
        """
        if self.patch:
            self.patch.remove()
            self.view.plotKML(None)
            self.patch = None
            self.cbOverlay.setEnabled(False)
        try:
            with open(self.leFile.text()) as kmlf:
                self.kml = pykml.parser.parse(kmlf).getroot()
                self.patch = KMLPatch(self.view.map, self.kml, self.get_color())
            self.cbOverlay.setEnabled(True)
            if self.view and self.cbOverlay.isChecked():
                self.view.plotKML(self.patch)
        except IOError, ex:
            QtGui.QMessageBox.critical(self, self.tr("KML Overlay"),
                                       self.tr("ERROR:\n%s\n%s" % (type(ex), ex)),
                                       QtGui.QMessageBox.Ok)
