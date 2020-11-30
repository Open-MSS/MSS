# -*- coding: utf-8 -*-
"""

    mslib.msui.wms_capabilities
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Widget to display a WMS (Web Map Service) capabilities document.

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2020 by the mss team, see AUTHORS.
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

from mslib.msui.mss_qt import QtWidgets
from mslib.msui.mss_qt import ui_wms_capabilities as ui


class WMSCapabilitiesBrowser(QtWidgets.QDialog, ui.Ui_WMSCapabilitiesBrowser):
    """Dialog presenting an XML document to the user.
    """

    def __init__(self, parent=None, url=None, capabilities=None):
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

        self.capabilities = capabilities

        self.update_text()
        self.cbFullView.stateChanged.connect(self.update_text)

    def update_text(self):
        if self.cbFullView.isChecked():
            self.txtCapabilities.setPlainText(self.capabilities.capabilities_document.decode("utf-8"))
        else:
            provider = self.capabilities.provider
            identification = self.capabilities.identification
            if provider.contact is None:
                contact = collections.defaultdict(lambda: None)
            else:
                contact = vars(provider.contact)
            text = ("<b>Title:</b> {title}<p>"
                    "<b>Service type:</b> {type} {version}<br>"
                    "<b>Abstract:</b><br>{abstract}<br>"
                    "<b>Contact:</b><br>"
                    "    {name}<br>"
                    "    {organization}<br>"
                    "    {email}<br>"
                    "    {address}<br>"
                    "    {postcode} {city}<br>\n"
                    "<b>Keywords:</b> {keywords}<br>\n"
                    "<b>Access constraints:</b> {accessconstraints}<br>\n"
                    "<b>Fees:</b> {fees}").format(
                type=identification.type,
                version=identification.version,
                title=identification.title,
                abstract=identification.abstract,
                name=contact["name"],
                organization=contact["organization"],
                email=contact["email"],
                address=contact["address"],
                postcode=contact["postcode"],
                city=contact["city"],
                keywords=identification.keywords,
                accessconstraints=identification.accessconstraints,
                fees=identification.fees)
            self.txtCapabilities.setHtml(text)
