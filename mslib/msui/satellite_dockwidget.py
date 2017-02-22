"""Control to load satellite track predictions into the top view.

********************************************************************************

   Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

********************************************************************************

This file is part of the Mission Support System User Interface (MSUI).

AUTHORS:
========

* Marc Rautenhaus (mr)

"""

# standard library imports
import logging

# related third party imports
from mslib.msui.mss_qt import QtGui, QtWidgets, USE_PYQT5

# local application imports
from mslib import mss_util
from mslib.msui.mss_qt import ui_satellite_dockwidget as ui

#
# CLASS SatelliteControlWidgeT
#


class SatelliteControlWidget(QtWidgets.QWidget, ui.Ui_SatelliteDockWidget):
    def __init__(self, parent=None, view=None):
        super(SatelliteControlWidget, self).__init__(parent)
        self.setupUi(self)
        self.view = view

        # Currently loaded satellite overpass segments.
        self.overpass_segments = None

        # Connect slots and signals.
        self.btSelectFile.clicked.connect(self.selectFile)
        self.btLoadFile.clicked.connect(self.loadFile)
        self.cbSatelliteOverpasses.currentIndexChanged.connect(self.plotOverpassTrack)

    def selectFile(self):
        """Slot that opens a file dialog to choose a file with satellite
           overpass predictions.
        """
        filename = QtGui.QFileDialog.getOpenFileName(
            self, "Open NASA satellite overpass prediction", "", "(*.*)")
        filename = filename[0] if USE_PYQT5 else unicode(filename)
        if not filename:
            return
        self.leFile.setText(filename)

    def loadFile(self):
        """Load the file specified in leFile and fill the combobox with the
           available track segments.
        """
        fname = unicode(self.leFile.text())
        logging.debug("loading satellite overpasses in file %s", fname)

        try:
            overpass_segments = mss_util.read_nasa_satellite_prediction(fname)
        except (IOError, OSError, ValueError), ex:
            logging.error("Problem accessing '%s' file", fname)
            QtWidgets.QMessageBox.critical(self, self.tr("Satellite Overpass Tool"),
                                           self.tr("ERROR:\n%s\n%s" % (type(ex), ex)))
        else:
            logging.debug("read %i segments", len(overpass_segments))

            self.cbSatelliteOverpasses.clear()
            items = ["%s to %s" % (str(seg["utc"][0]), str(seg["utc"][-1]))
                     for seg in overpass_segments]
            items.insert(0, "None (select item to plot)")
            self.cbSatelliteOverpasses.addItems(items)

            self.overpass_segments = overpass_segments

    def plotOverpassTrack(self, index):
        """
        """
        index -= 1
        logging.debug("plotting satellite overpass #%i", index)
        if index == -1:
            segment = None
        else:
            segment = self.overpass_segments[index]
        if self.view is not None:
            self.view.plotSatelliteOverpass(segment)


def _main():
    import sys

    application = QtWidgets.QApplication(sys.argv)
    window = SatelliteControlWidget()
    window.show()
    sys.exit(application.exec_())

if __name__ == "__main__":
    _main()
