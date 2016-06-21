"""Widget to display a WMS (Web Map Service) capabilities document.

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
from PyQt4 import QtGui  # Qt4 bindings

# local application imports
from mslib.msui import ui_wms_capabilities as ui

"""
CLASS WMSCapabilitiesBrowser
"""


class WMSCapabilitiesBrowser(QtGui.QDialog, ui.Ui_WMSCapabilitiesBrowser):
    """Dialog presenting an XML document to the user.
    """

    def __init__(self, parent=None, url=None, capabilities_xml=None):
        """
        Arguments:
        parent -- Qt widget that is parent to this widget.
        capabilities_xml -- .
        """
        super(WMSCapabilitiesBrowser, self).__init__(parent)
        self.setupUi(self)

        if url is None:
            url = ""
        self.lblURL.setText(url)

        if capabilities_xml is None:
            capabilities_xml = ""
        self.txtCapabilities.setPlainText(capabilities_xml)


if __name__ == "__main__":
    # Log everything, and send it to stderr.
    # See http://docs.python.org/library/logging.html for more information
    # on the Python logging module.
    # NOTE: http://docs.python.org/library/logging.html#formatter-objects
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s (%(module)s.%(funcName)s): %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")

    import sys

    app = QtGui.QApplication(sys.argv)
    win = WMSCapabilitiesBrowser(url="http://test.me",
                                 capabilities_xml="""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE WMT_MS_Capabilities SYSTEM "http://schemas.opengis.net/wms/1.1.1/capabilities_1_1_1.dtd">
<WMT_MS_Capabilities version="1.1.1" updateSequence="1295028115677" xmlns:xlink="http://www.w3.org/1999/xlink">""")
    win.show()
    sys.exit(app.exec_())
