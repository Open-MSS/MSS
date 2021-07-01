# -*- coding: utf-8 -*-
"""

    mslib.mswms.mpl_lsec
    ~~~~~~~~~~~~~~~~~~~~

    Linear section style super class.

    This file is part of mss.

    :copyright: Copyright 2021 May Baer
    :copyright: Copyright 2021 by the mss team, see AUTHORS.
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
# style definitions should be put in mpl_lsec_styles.py

import logging
from xml.dom.minidom import getDOMImplementation
import matplotlib as mpl
from pint import Quantity

from mslib.mswms import mss_2D_sections
from mslib.utils import convert_to

mpl.rcParams['xtick.direction'] = 'out'
mpl.rcParams['ytick.direction'] = 'out'


class AbstractLinearSectionStyle(mss_2D_sections.Abstract2DSectionStyle):
    """
    Abstract Linear Section Style
    Superclass for all Matplotlib-based linear section styles.
    """

    def __init__(self, driver=None):
        """
        Constructor.
        """
        super(AbstractLinearSectionStyle, self).__init__(driver=driver)
        self.variable = ""
        self.unit = ""
        self.y_values = []

    def _prepare_datafields(self):
        self.y_values = self.data[self.variable]
        if self.variable in self.driver.data_units:
            self.unit = self.driver.data_units[self.variable]

    def supported_crs(self):
        """
        Returns a list of the coordinate reference systems supported by
        this style.
        """
        return ["LINE:1"]

    def plot_lsection(self, data, lats, lons, valid_time, init_time):
        """
        """
        # Check if required data is available.
        self.data_units = self.driver.data_units.copy()
        for datatype, dataitem, dataunit in self.required_datafields:
            if dataitem not in data:
                raise KeyError(f"required data field '{dataitem}' not found")
            origunit = self.driver.data_units[dataitem]
            if dataunit is not None:
                data[dataitem] = convert_to(data[dataitem], origunit, dataunit)
                self.data_units[dataitem] = dataunit
            else:
                logging.debug("Please add units to plot variables")

        # Copy parameters to properties.
        self.data = data
        self.lats = lats
        self.lons = lons
        self.valid_time = valid_time
        self.init_time = init_time

        # Derive additional data fields and make the plot.
        self._prepare_datafields()

        impl = getDOMImplementation()
        xmldoc = impl.createDocument(None, "MSS_LinearSection_Data", None)

        # Title of this section.
        node = xmldoc.createElement("Title")
        node.appendChild(xmldoc.createTextNode(self.title))
        xmldoc.documentElement.appendChild(node)

        # Time information of this section.
        node = xmldoc.createElement("ValidTime")
        node.appendChild(xmldoc.createTextNode(self.valid_time.strftime("%Y-%m-%dT%H:%M:%SZ")))
        xmldoc.documentElement.appendChild(node)

        node = xmldoc.createElement("InitTime")
        node.appendChild(xmldoc.createTextNode(self.init_time.strftime("%Y-%m-%dT%H:%M:%SZ")))
        xmldoc.documentElement.appendChild(node)

        # Longitude data.
        node = xmldoc.createElement("Longitude")
        node.setAttribute("num_waypoints", f"{len(self.lons)}")
        data_str = ",".join([str(lon) for lon in self.lons])

        node.appendChild(xmldoc.createTextNode(data_str))
        xmldoc.documentElement.appendChild(node)

        # Latitude data.
        node = xmldoc.createElement("Latitude")
        node.setAttribute("num_waypoints", f"{len(self.lats)}")
        data_str = ",".join([str(lat) for lat in self.lats])

        node.appendChild(xmldoc.createTextNode(data_str))
        xmldoc.documentElement.appendChild(node)

        # Variable data.
        node = xmldoc.createElement("Data")
        node.setAttribute("num_waypoints", f"{len(self.y_values)}")
        node.setAttribute("unit", self.unit)
        if isinstance(self.y_values[0], Quantity):
            data_str = ",".join([str(val.magnitude) for val in self.y_values])
        else:
            data_str = ",".join([str(val) for val in self.y_values])

        node.appendChild(xmldoc.createTextNode(data_str))
        xmldoc.documentElement.appendChild(node)

        # Return the XML document as formatted string.
        return xmldoc.toprettyxml(indent="  ")
