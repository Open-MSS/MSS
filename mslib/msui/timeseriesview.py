"""Window for the display of trajectory time series.

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
from mslib.msui.mss_qt import QtGui  # Qt4 bindings

# local application imports
from mslib.msui import ui_timeseriesview_window as ui
from mslib.msui.viewwindows import MSSMplViewWindow

#
# CLASS TimeSeriesView
#


class MSSTimeSeriesViewWindow(MSSMplViewWindow, ui.Ui_TimeSeriesViewWindow):
    """PyQt4 window implementing a time series view.
    """
    name = "Time Series View"

    def __init__(self, parent=None):
        """Set up user interface, connect signal/slots.
        """
        super(MSSTimeSeriesViewWindow, self).__init__(parent)
        self.setupUi(self)

    def setIdentifier(self, identifier):
        super(MSSTimeSeriesViewWindow, self).setIdentifier(identifier)
        self.mpl.canvas.setIdentifier(identifier)


# Main program to test the window during development. The following code
# will not be executed if the view is opened from the Mission Support
# System user interface.

def _main():
    # Log everything, and send it to stderr.
    # See http://docs.python.org/library/logging.html for more information
    # on the Python logging module.
    # NOTE: http://docs.python.org/library/logging.html#formatter-objects
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s (%(module)s.%(funcName)s): %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")

    import sys

    application = QtGui.QApplication(sys.argv)
    window = MSSTimeSeriesViewWindow()
    window.show()
    sys.exit(application.exec_())

if __name__ == "__main__":
    _main()
