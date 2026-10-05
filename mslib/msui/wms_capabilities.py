# -*- coding: utf-8 -*-
"""

    mslib.msui.wms_capabilities
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Widget to display a WMS (Web Map Service) capabilities document.

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2026 by the MSS team, see AUTHORS.
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

import collections
import html

from PyQt5 import QtCore, QtWidgets
from mslib.msui.qt5 import ui_wms_capabilities as ui


class WMSCapabilitiesBrowser(QtWidgets.QDialog, ui.Ui_WMSCapabilitiesBrowser):
    """Dialog presenting an XML document to the user.
    """

    def __init__(self, parent=None, url=None, capabilities=None):
        """
        Arguments:
        parent -- Qt widget that is parent to this widget.
        capabilities_xml -- .
        """
        super().__init__(parent)
        self.setupUi(self)

        if url is None:
            url = ""
        self.lblURL.setTextFormat(QtCore.Qt.PlainText)
        self.lblURL.setText(url)

        self.capabilities = capabilities

        self.update_text()
        self.cbFullView.stateChanged.connect(self.update_text)

    def update_text(self):
        def esc(value):
            # the texts come from the WMS server, markup in them, e.g. <img src="file://host/s/x.png">, is shown as text
            return html.escape(str(value))

        if self.cbFullView.isChecked():
            self.txtCapabilities.setPlainText(self.capabilities.capabilities_document.decode("utf-8"))
        else:
            provider = self.capabilities.provider
            identification = self.capabilities.identification
            if provider.contact is None:
                contact = collections.defaultdict(lambda: None)
            else:
                contact = {key: esc(value) for key, value in vars(provider.contact).items()}
            text = (f"<b>Title:</b> {esc(identification.title)}<p>"
                    f"<b>Service type:</b> {esc(identification.type)} {esc(identification.version)}<br>"
                    f"<b>Abstract:</b><br>{esc(identification.abstract)}<br>"
                    f"<b>Contact:</b><br>"
                    f"    {contact['name']}<br>"
                    f"    {contact['organization']}<br>"
                    f"    {contact['email']}<br>"
                    f"    {contact['address']}<br>"
                    f"    {contact['postcode']} {contact['city']}<br>\n"
                    f"<b>Keywords:</b> {esc(identification.keywords)}<br>\n"
                    f"<b>Access constraints:</b> {esc(identification.accessconstraints)}<br>\n"
                    f"<b>Fees:</b> {esc(identification.fees)}")
            self.txtCapabilities.setHtml(text)
