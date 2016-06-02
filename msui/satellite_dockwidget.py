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
from PyQt4 import QtGui, QtCore  # Qt4 bindings

# local application imports
from mslib import mss_util
import ui_satellite_dockwidget as ui


################################################################################
###                      CLASS SatelliteControlWidget                        ###
################################################################################

class SatelliteControlWidget(QtGui.QWidget, ui.Ui_SatelliteDockWidget):
    def __init__(self, parent=None, view=None):
        super(SatelliteControlWidget, self).__init__(parent)
        self.setupUi(self)
        self.view = view

        # Currently loaded satellite overpass segments.
        self.overpass_segments = None

        # Connect slots and signals.
        self.connect(self.btSelectFile, QtCore.SIGNAL("clicked()"),
                     self.selectFile)
        self.connect(self.btLoadFile, QtCore.SIGNAL("clicked()"),
                     self.loadFile)
        self.connect(self.cbSatelliteOverpasses,
                     QtCore.SIGNAL("currentIndexChanged(int)"),
                     self.plotOverpassTrack)

    def selectFile(self):
        """Slot that opens a file dialog to choose a file with satellite
           overpass predictions.
        """
        fname = QtGui.QFileDialog.getOpenFileName(self,
                                                  "Open NASA satellite overpass prediction",
                                                  "", "(*.*)");
        if fname.isEmpty():
            return
        self.leFile.setText(fname)

    def loadFile(self):
        """Load the file specified in leFile and fill the combobox with the
           available track segments.
        """
        fname = str(self.leFile.text())
        logging.debug("loading satellite overpasses in file %s" % fname)

        overpass_segments = mss_util.read_nasa_satellite_prediction(fname)
        logging.debug("read %i segments" % len(overpass_segments))

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
        logging.debug("plotting satellite overpass #%i" % index)
        if index == -1:
            segment = None
        else:
            segment = self.overpass_segments[index]
        if self.view:
            self.view.plotSatelliteOverpass(segment)


################################################################################

if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    win = SatelliteControlWidget()
    win.show()
    sys.exit(app.exec_())
