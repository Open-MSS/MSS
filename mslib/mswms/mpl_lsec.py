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
# style definitions should be put in mpl_vsec_styles.py

import PIL.Image
import io
import logging
import numpy as np
from xml.dom.minidom import getDOMImplementation
import matplotlib as mpl
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

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

    # TODO: the general setup should be a separate class as well
    def _latlon_setup(self, orography=105000., ax=None):
        """
        General setup for lat/lon x axis
        """
        if not ax:
            ax = self.ax

        # Set xticks so that they display lat/lon. Plot "numlabels" labels.
        tick_index_step = max(1, len(self.lat_inds) // int(self.numlabels))
        ax.set_xticks(self.lat_inds[::tick_index_step])
        ax.set_xticklabels([f"{d[0]:2.1f}, {d[1]:2.1f}"
                            for d in zip(self.lats[::tick_index_step],
                                         self.lons[::tick_index_step])],
                           rotation=25, fontsize=10, horizontalalignment='right')

        # Add lines to highlight points if any are given.
        ipoint = 0
        for i, (lat, lon) in enumerate(zip(self.lats, self.lons)):
            if (ipoint < len(self.highlight) and
                np.hypot(lat - self.highlight[ipoint][0],
                         lon - self.highlight[ipoint][1]) < 2E-10):
                ax.axvline(i, color='k', linewidth=2, linestyle='--', alpha=0.5)
                ipoint += 1

        # Set axis limits and draw grid for major ticks.
        ax.set_xlim(self.lat_inds[0], self.lat_inds[-1])
        ax.grid(b=True)

    def _plot_style(self, color):
        ax = self.ax

        numpoints = len(self.lats)
        ax.set_ylabel(self.unit)
        ax.plot(range(numpoints), self.y_values, color.replace("0x", "#"))
        self._latlon_setup()

    def plot_lsection(self, data, lats, lons, valid_time, init_time,
                      resolution=(-1, -1), style=None, show=False,
                      highlight=None, noframe=False, figsize=(960, 480),
                      numlabels=10, orography_color='k', transparent=False, color="0x00AAFF",
                      return_format="image/png"):
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
        self.lat_inds = np.arange(len(lats))
        self.lons = lons
        self.valid_time = valid_time
        self.init_time = init_time
        self.resolution = resolution
        self.style = style
        self.highlight = highlight
        self.noframe = noframe
        self.numlabels = numlabels
        self.orography_color = orography_color

        # Derive additional data fields and make the plot.
        self._prepare_datafields()

        # Code for producing a png image with Matplotlib.
        # ===============================================
        if return_format == "image/png":

            logging.debug("creating figure..")
            dpi = 80
            figsize = (figsize[0] / dpi), (figsize[1] / dpi)
            facecolor = "white"
            self.fig = mpl.figure.Figure(figsize=figsize, dpi=dpi, facecolor=facecolor)
            logging.debug("\twith frame and legends" if not noframe else
                          "\twithout frame")
            if noframe:
                self.ax = self.fig.add_axes([0.0, 0.0, 1.0, 1.0])
            else:
                self.ax = self.fig.add_axes([0.07, 0.17, 0.9, 0.72])

            # Set transparency for the output image.
            if transparent:
                self.fig.patch.set_alpha(0.)

            self._plot_style(color)

            # Return the image as png embedded in a StringIO stream.
            canvas = FigureCanvas(self.fig)
            output = io.BytesIO()
            canvas.print_png(output)

            if show:
                logging.debug("saving figure to mpl_lsec.png ..")
                canvas.print_png("mpl_lsec.png")

            # Convert the image to an 8bit palette image with a significantly
            # smaller file size (~factor 4, from RGBA to one 8bit value, plus the
            # space to store the palette colours).
            # NOTE: PIL at the current time can only create an adaptive palette for
            # RGB images, hence alpha values are lost here. If transparency is
            # requested, the figure face colour is stored as the "transparent"
            # colour in the image. This works in most cases, but might lead to
            # visible artefacts in some cases.
            logging.debug("converting image to indexed palette.")
            # Read the above stored png into a PIL image and create an adaptive
            # colour palette.
            output.seek(0)  # necessary for PIL.Image.open()
            palette_img = PIL.Image.open(output).convert(mode="RGB"
                                                         ).convert("P", palette=PIL.Image.ADAPTIVE)
            output = io.BytesIO()
            if not transparent:
                logging.debug("saving figure as non-transparent PNG.")
                palette_img.save(output, format="PNG")  # using optimize=True doesn't change much
            else:
                # If the image has a transparent background, we need to find the
                # index of the background colour in the palette. See the
                # documentation for PIL's ImagePalette module
                # (http://www.pythonware.com/library/pil/handbook/imagepalette.htm). The
                # idea is to create a 256 pixel image with the same colour palette
                # as the original image and use it as a lookup-table. Converting the
                # lut image back to RGB gives us a list of all colours in the
                # palette. (Why doesn't PIL provide a method to directly access the
                # colours in a palette??)
                lut = palette_img.resize((256, 1))
                lut.putdata(list(range(256)))
                lut = [c[1] for c in lut.convert("RGB").getcolors()]
                facecolor_rgb = list(mpl.colors.hex2color(mpl.colors.cnames[facecolor]))
                for i in [0, 1, 2]:
                    facecolor_rgb[i] = int(facecolor_rgb[i] * 255)
                facecolor_index = lut.index(tuple(facecolor_rgb))

                logging.debug("saving figure as transparent PNG with transparency index %i.",
                              facecolor_index)
                palette_img.save(output, format="PNG", transparency=facecolor_index)

            logging.debug("returning figure..")
            return output.getvalue()

        # Code for generating an XML document with the data values in ASCII format.
        # =========================================================================
        elif return_format == "text/xml":

            impl = getDOMImplementation()
            xmldoc = impl.createDocument(None, "MSS_1DSection_Data", None)

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

            data_str = ""
            for value in self.lons:
                data_str += str(value) + ","
            data_str = data_str[:-1]

            node.appendChild(xmldoc.createTextNode(data_str))
            xmldoc.documentElement.appendChild(node)

            # Latitude data.
            node = xmldoc.createElement("Latitude")
            node.setAttribute("num_waypoints", f"{len(self.lats)}")

            data_str = ""
            for value in self.lats:
                data_str += str(value) + ","
            data_str = data_str[:-1]

            node.appendChild(xmldoc.createTextNode(data_str))
            xmldoc.documentElement.appendChild(node)

            # Variable data.
            node = xmldoc.createElement("Data")
            node.setAttribute("num_waypoints", f"{len(self.y_values)}")
            node.setAttribute("unit", self.unit)
            node.setAttribute("color", color)

            data_str = ""
            for value in self.y_values:
                data_str += str(value) + ","
            data_str = data_str[:-1]

            node.appendChild(xmldoc.createTextNode(data_str))
            xmldoc.documentElement.appendChild(node)

            # Return the XML document as formatted string.
            return xmldoc.toprettyxml(indent="  ")
