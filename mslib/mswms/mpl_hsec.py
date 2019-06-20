# -*- coding: utf-8 -*-
"""

    mslib.mswms.mpl_hsec
    ~~~~~~~~~~~~~~~~~~~~

    Horizontal section style super classes for use with the
    HorizontalSectionDriver class.

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2019 by the mss team, see AUTHORS.
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
# style definitions should be put in mpl_hsec_styles.py

from __future__ import division


from future import standard_library
standard_library.install_aliases()


import io
import logging
from abc import abstractmethod
import mss_wms_settings

import matplotlib as mpl
import numpy as np
import PIL.Image
import cartopy
import cartopy.crs as ccrs
import matplotlib.pyplot as plt

from mslib.mswms import mss_2D_sections
from mslib.utils import get_projection_params


class AbstractHorizontalSectionStyle(mss_2D_sections.Abstract2DSectionStyle):
    """Abstract horizontal section super class. Use this class as a parent
       to classes implementing different plotting backends. For example,
       to derive a Matplotlib-based style class, or a Magics++-based
       style class.
    """

    @abstractmethod
    def plot_hsection(self):
        """Re-implement this function to perform the actual plotting.
        """
        pass


class MPLBasemapHorizontalSectionStyle(AbstractHorizontalSectionStyle):
    """Matplotlib-based super class for all horizontal section styles.
       Sets up and draws the map projection.
    """
    name = "BASEMAP"
    title = "Matplotlib Basemap"

    def _plot_style(self):
        """Overwrite this method to plot style-specific data on the map.
        """
        pass

    def supported_epsg_codes(self):
        return list(mss_wms_settings.epsg_to_mpl_basemap_table.keys())

    def support_epsg_code(self, crs):
        """Returns a list of supported EPSG codes.
        """
        try:
            get_projection_params(crs)
        except ValueError:
            return False
        return True

    def supported_crs(self):
        """Returns a list of the coordinate reference systems supported by
           this style.
        """
        crs_list = set([
            "EPSG:3031",  # WGS 84 / Antarctic Polar Stereographic
            "EPSG:3995",  # WGS 84 / Arctic Polar Stereographic
            "EPSG:3857",  # WGS 84 / Spherical Mercator
            "EPSG:4326",  # WGS 84 / cylindric
            "MSS:stere"])
        for code in self.supported_epsg_codes():
            crs_list.add("EPSG:{:d}".format(code))
        return sorted(crs_list)

    def plot_hsection(self, data, lats, lons, bbox=(-180, -90, 180, 90),
                      level=None, figsize=(960, 640), crs=None,
                      proj_params=None,
                      valid_time=None, init_time=None, style=None,
                      resolution=-1, noframe=False, show=False,
                      transparent=False):
        """
        EPSG overrides proj_params!
        """
        # if proj_params is None:
        proj_params = {"projection": ccrs.PlateCarree()}
        bbox_units = "latlon"
        # Projection parameters from EPSG code.
        if crs is not None:
            proj_params, bbox_units = [get_projection_params(crs)[_x] for _x in ("basemap", "bbox")]

        logging.debug("plotting data..")

        # Check if required data is available.
        for datatype, dataitem in self.required_datafields:
            if dataitem not in data:
                raise KeyError(u"required data field '{}' not found".format(dataitem))

        # Copy parameters to properties.
        self.data = data
        self.data_units = self.driver.data_units.copy()
        self.lats = lats
        self.lons = lons
        self.level = level
        self.valid_time = valid_time
        self.init_time = init_time
        self.style = style
        self.resolution = resolution
        self.noframe = noframe
        self.crs = crs

        # Derive additional data fields and make the plot.
        logging.debug("preparing additional data fields..")
        self._prepare_datafields()

        logging.debug("creating figure..")
        dpi = 80
        figsize = (figsize[0] / dpi), (figsize[1] / dpi)
        facecolor = "white"
        fig = plt.figure(figsize=figsize, dpi=dpi, facecolor=facecolor)
        logging.debug("\twith frame and legends" if not noframe else
                      "\twithout frame")
        user_proj = proj_params.get('projection')

        if noframe:
            ax = plt.axes([0.0, 0.0, 1.0, 1.0], projection=user_proj)
        else:
            ax = plt.axes([0.05, 0.05, 0.9, 0.88], projection=user_proj)

        if bbox_units == "degree":
            ax.set_extent([bbox[0], bbox[2], bbox[1], bbox[3]], crs=ccrs.PlateCarree())
        elif bbox_units.startswith("meter"):
            # convert meters to degrees
            ct_center = [float(_x) for _x in bbox_units[6:-1].split(",")]
            center_x, center_y = user_proj.transform_point(ct_center[0], ct_center[1], src_crs=ccrs.PlateCarree())
            bbox_0, bbox_2 = ccrs.PlateCarree().transform_point(
                bbox[0] + center_x, bbox[2] + center_y, src_crs=user_proj)
            bbox_1, bbox_3 = ccrs.PlateCarree().transform_point(
                bbox[1] + center_x, bbox[3] + center_y, src_crs=user_proj)
            ax.set_extent([bbox_0, bbox_1, bbox_2, bbox_3], crs=ccrs.PlateCarree())
        elif bbox_units == "no":
            pass
        else:
            raise ValueError("bbox_units '{}' not known.".format(bbox_units))

        ax.set_extent([bbox[0], bbox[2], bbox[1], bbox[3]], crs=ccrs.PlateCarree())
        ax.coastlines(resolution='10m')
        ax.add_feature(cartopy.feature.BORDERS, linestyle='-', alpha=1)
        ax.outline_patch.set_edgecolor('white')
        self.fig = fig
        self.shift_data(ax)
        self.mask_data(ax)
        self._plot_style(ax)

        # Return the image as png embedded in a StringIO stream.
        # canvas = FigureCanvas(fig)
        output = io.BytesIO()
        plt.savefig(output, bbox_inches='tight', format='png')

        if show:
            logging.debug("saving figure to mpl_hsec.png ..")
            plt.savefig("mpl_hsec.png", bbox_inches='tight', format='png')

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
        palette_img = PIL.Image.open(output).convert(mode="RGB").convert("P", palette=PIL.Image.ADAPTIVE)
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

            logging.debug(u"saving figure as transparent PNG with transparency index %s.", facecolor_index)
            palette_img.save(output, format="PNG", transparency=facecolor_index)

        logging.debug("returning figure..")
        return output.getvalue()

    def shift_data(self, ax):
        """Shift the data fields such that the longitudes are in the range
        left_longitude .. left_longitude+360, where left_longitude is the
        leftmost longitude appearing in the plot.

        Necessary to prevent data cut-offs in situations where the requested
        map covers a domain that crosses the data longitude boundaries
        (e.g. data is stored on a -180..180 grid, but a map in the range
        -200..-100 is requested).
        """
        # Determine the leftmost longitude in the plot.
        left_longitude = ax.get_extent()[0]
        logging.debug(u"shifting data grid to leftmost longitude in map %2.f..", left_longitude)

        # Shift the longitude field such that the data is in the range
        # left_longitude .. left_longitude+360.
        self.lons = ((self.lons - left_longitude) % 360) + left_longitude
        lon_indices = self.lons.argsort()
        self.lons = self.lons[lon_indices]

        # Shift data fields correspondingly.
        for key in self.data:
            self.data[key] = self.data[key][:, lon_indices]

    def mask_data(self, ax):
        """Mask data arrays so that all values outside the map domain
           are masked. This is required for clabel to work correctly.

        See:
        http://www.mail-archive.com/matplotlib-users@lists.sourceforge.net/msg02892.html
        (Re: [Matplotlib-users] clabel and basemap).

        (mr, 2011-01-18)
        """
        # compute native map projection coordinates of lat/lon grid.
        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        out_xyz = ccrs.PlateCarree().transform_points(ccrs.Geodetic(), lonmesh_, latmesh_)

        x = out_xyz[:, :, 0]
        y = out_xyz[:, :, 1]

        # test which coordinates are outside the map domain.
        add_x = ((ax.get_extent()[1] - ax.get_extent()[0]) / 10.)
        add_y = ((ax.get_extent()[2] - ax.get_extent()[3]) / 10.)

        mask1 = x < ax.get_extent()[0] - add_x
        mask2 = x > ax.get_extent()[1] + add_x
        mask3 = y > ax.get_extent()[3] + add_y
        mask4 = y < ax.get_extent()[2] - add_y
        mask = mask1 + mask2 + mask3 + mask4
        # mask data arrays.
        for key in self.data:
            self.data[key] = np.ma.masked_array(
                self.data[key], mask=mask, keep_mask=False)
