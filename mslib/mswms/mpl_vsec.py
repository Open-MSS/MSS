# -*- coding: utf-8 -*-
"""

    mslib.mswms.mpl_vsec
    ~~~~~~~~~~~~~~~~~~~~

    Vertical section style super classes for use with the
    VerticalSectionDriver class.

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2017 by the mss team, see AUTHORS.
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

from __future__ import division


from future import standard_library
standard_library.install_aliases()


import PIL.Image
import io
import logging
import numpy as np
from abc import abstractmethod
from xml.dom.minidom import getDOMImplementation

# related third party imports
import matplotlib as mpl
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# local application imports
from mslib.mswms import mss_2D_sections

mpl.rcParams['xtick.direction'] = 'out'
mpl.rcParams['ytick.direction'] = 'out'


class AbstractVerticalSectionStyle(mss_2D_sections.Abstract2DSectionStyle):
    """
    Abstract Vertical Section Style
    Superclass for all Matplotlib-based vertical section styles.
    """

    def __init__(self, driver=None):
        """Constructor.
        """
        super(AbstractVerticalSectionStyle, self).__init__(driver=driver)

    def supported_crs(self):
        """Returns a list of the coordinate reference systems supported by
           this style.
        """
        return ["VERT:LOGP"]

    # TODO: the general setup should be a separate class as well
    def _latlon_logp_setup(self, orography=105000., titlestring=u""):
        """General setup for lat/lon vs. log p vertical cross-sections.
        """
        ax = self.ax

        # Set xticks so that they display lat/lon. Plot "numlabels" labels.
        tick_index_step = max(1, len(self.lat_inds) // int(self.numlabels))
        ax.set_xticks(self.lat_inds[::tick_index_step])
        ax.set_xticklabels(["{:2.1f}, {:2.1f}".format(d[0], d[1])
                            for d in zip(self.lats[::tick_index_step],
                                         self.lons[::tick_index_step])],
                           rotation=25, fontsize=10, horizontalalignment='right')

        # Add lines to highlight points if any are given.
        ipoint = 0
        for i, (lat, lon) in enumerate(zip(self.lats, self.lons)):
            if (abs(lat - self.highlight[ipoint][0]) < 1E-10 and
                    abs(lon - self.highlight[ipoint][1]) < 1E-10):
                ax.axvline(i, color='k', linewidth=2, linestyle='--', alpha=0.5)
                ipoint += 1

        # Add lower limit of pressure curtain to indicate orography.
        ax.fill_between(self.lat_inds, orography, y2=self.p_bot,
                        color=self.orography_color)

        # Set pressure axis scale to log.
        ax.set_yscale("log")

        # Compute the position of major and minor ticks. Major ticks are labelled.
        # By default, major ticks are drawn every 100hPa. If p_top < 100hPa,
        # the distance is reduced to every 10hPa above 100hPa.
        label_distance = 10000
        label_bot = self.p_bot - (self.p_bot % label_distance)
        major_ticks = np.arange(label_bot, self.p_top - 1, -label_distance)

        # .. check step reduction to 10 hPa ..
        if self.p_top < 10000:
            major_ticks2 = np.arange(major_ticks[-1], self.p_top - 1,
                                     -label_distance // 10)
            len_major_ticks = len(major_ticks)
            major_ticks = np.resize(major_ticks,
                                    len_major_ticks + len(major_ticks2) - 1)
            major_ticks[len_major_ticks:] = major_ticks2[1:]

        labels = ["{:.0f}".format(l / 100.) for l in major_ticks]

        # .. the same for the minor ticks ..
        p_top_minor = max(label_distance, self.p_top)
        label_distance_minor = 1000
        label_bot_minor = self.p_bot - (self.p_bot % label_distance_minor)
        minor_ticks = np.arange(label_bot_minor, p_top_minor - 1,
                                -label_distance_minor)

        if self.p_top < 10000:
            minor_ticks2 = np.arange(minor_ticks[-1], self.p_top - 1,
                                     -label_distance_minor // 10)
            len_minor_ticks = len(minor_ticks)
            minor_ticks = np.resize(minor_ticks,
                                    len_minor_ticks + len(minor_ticks2) - 1)
            minor_ticks[len_minor_ticks:] = minor_ticks2[1:]

        # Draw ticks and tick labels.
        ax.set_yticks(minor_ticks, minor=True)
        ax.set_yticks(major_ticks, minor=False)
        ax.set_yticklabels(labels, minor=False, fontsize=10)

        # Set axis limits and draw grid for major ticks.
        ax.set_xlim(self.lat_inds[0], self.lat_inds[-1])
        ax.set_ylim(self.p_bot, self.p_top)
        ax.grid(b=True)

        # Plot title (either in image axes or above).
        time_step = self.valid_time - self.init_time
        time_step_hrs = (time_step.days * 86400 + time_step.seconds) // 3600
        titlestring = u"{} [{:.0f}..{:.0f} hPa]\nValid: {} (step {:d} hrs from {})".format(
            titlestring, self.p_bot / 100., self.p_top / 100.,
            self.valid_time.strftime("%a %Y-%m-%d %H:%M UTC"),
            time_step_hrs, self.init_time.strftime("%a %Y-%m-%d %H:%M UTC"))

    @abstractmethod
    def _plot_style(self):
        """Can call self._log_setup()
        """
        pass

    def plot_vsection(self, data, lats, lons, valid_time, init_time,
                      resolution=(-1, -1), bbox=(-1, 1050, -1, 200), style=None,
                      show=False,
                      highlight=None, noframe=False, figsize=(960, 480),
                      numlabels=10, orography_color='k', transparent=False,
                      return_format="image/png"):
        """
        """
        # Check if required data is available.
        for datatype, dataitem in self.required_datafields:
            if dataitem not in data:
                raise KeyError(u"required data field '{}' not found".format(dataitem))

        # Copy parameters to properties.
        self.data = data
        self.data_units = self.driver.data_units.copy()
        self.lats = lats
        self.lat_inds = np.arange(len(lats))
        self.lons = lons
        self.valid_time = valid_time
        self.init_time = init_time
        self.resolution = resolution
        self.style = style
        self.highlight = highlight
        self.noframe = noframe
        self.p_bot = bbox[1] * 100
        self.p_top = bbox[3] * 100
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

            self._plot_style()

            # Set transparency for the output image.
            if transparent:
                self.fig.patch.set_alpha(0.)

            # Return the image as png embedded in a StringIO stream.
            canvas = FigureCanvas(self.fig)
            output = io.BytesIO()
            canvas.print_png(output, bbox_inches='tight')

            if show:
                logging.debug("saving figure to mpl_vsec.png ..")
                canvas.print_png("mpl_vsec.png", bbox_inches='tight')

            # Convert the image to an 8bit palette image with a significantly
            # smaller file size (~factor 4, from RGBA to one 8bit value, plus the
            # space to store the palette colours).
            # NOTE: PIL at the current time can only create an adaptive palette for
            # RGB images, hence alpha values are lost here. If transpareny is
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
            xmldoc = impl.createDocument(None, "MSS_VerticalSection_Data", None)

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
            node.setAttribute("num_waypoints", "{}".format(len(self.lons)))

            data_str = ""
            for value in self.lons:
                data_str += str(value) + ","
            data_str = data_str[:-1]

            node.appendChild(xmldoc.createTextNode(data_str))
            xmldoc.documentElement.appendChild(node)

            # Latitude data.
            node = xmldoc.createElement("Latitude")
            node.setAttribute("num_waypoints", "{}".format(len(self.lats)))

            data_str = ""
            for value in self.lats:
                data_str += str(value) + ","
            data_str = data_str[:-1]

            node.appendChild(xmldoc.createTextNode(data_str))
            xmldoc.documentElement.appendChild(node)

            # Variable data.
            data_node = xmldoc.createElement("Data")

            for var in self.data:
                node = xmldoc.createElement(var)
                data_shape = self.data[var].shape
                node.setAttribute("num_levels", u"{}".format(data_shape[0]))
                node.setAttribute("num_waypoints", u"{}".format(data_shape[1]))

                data_str = ""
                for data_row in self.data[var]:
                    for value in data_row:
                        data_str += str(value) + ","
                    data_str = data_str[:-1] + "\n"
                data_str = data_str[:-1]

                node.appendChild(xmldoc.createTextNode(data_str))
                data_node.appendChild(node)

            xmldoc.documentElement.appendChild(data_node)

            # Return the XML document as formatted string.
            return xmldoc.toprettyxml(indent="  ")
