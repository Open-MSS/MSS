# -*- coding: utf-8 -*-
"""

    mslib.mswms.mpl_hsec
    ~~~~~~~~~~~~~~~~~~~~

    Horizontal section style super classes for use with the
    HorizontalSectionDriver class.

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
# style definitions should be put in mpl_hsec_styles.py


import io
import logging
from abc import abstractmethod
import mss_wms_settings

import matplotlib as mpl
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import mpl_toolkits.basemap as basemap
import numpy as np
import PIL.Image

from mslib.mswms import mss_2D_sections
from mslib.utils import get_projection_params, convert_to


BASEMAP_CACHE = {}
BASEMAP_REQUESTS = []


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
       Sets up the map projection and draws a basemap.
    """
    name = "BASEMAP"
    title = "Matplotlib basemap"

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

    def _draw_auto_graticule(self, bm):
        """
        """
        # Compute some map coordinates that are required below for the automatic
        # determination of which meridians and parallels to draw.
        axis = bm.ax.axis()
        upperLeftCornerLon, upperLeftCornerLat = bm(axis[0], axis[3], inverse=True)
        lowerRightCornerLon, lowerRightCornerLat = bm(axis[1], axis[2], inverse=True)
        middleUpperBoundaryLon, middleUpperBoundaryLat = bm(np.mean([axis[0], axis[1]]), axis[3], inverse=True)
        middleLowerBoundaryLon, middleLowerBoundaryLat = bm(np.mean([axis[0], axis[1]]), axis[2], inverse=True)

        # Determine which parallels and meridians should be drawn.
        #   a) determine which are the minimum and maximum visible
        #      longitudes and latitudes, respectively. These
        #      values depend on the map projection.
        if bm.projection in ['npstere', 'spstere', 'stere', 'lcc']:
            # For stereographic projections: Draw meridians from the minimum
            # longitude contained in the map at one of the four corners to the
            # maximum longitude at one of these corner points. If
            # the map centre is contained in the map, draw all meridians
            # around the globe.
            # FIXME? This is only correct for polar stereographic projections.
            # Draw parallels from the min latitude contained in the map at
            # one of the four corners OR the middle top or bottom to the
            # maximum latitude at one of these six points.
            # If the map centre in contained in the map, replace either
            # start or end latitude by the centre latitude (whichever is
            # smaller/larger).

            # check if centre point of projection is contained in the map,
            # use projection coordinates for this test
            centre_x = bm.projparams["x_0"]
            centre_y = bm.projparams["y_0"]
            contains_centre = (centre_x < bm.urcrnrx) and (centre_y < bm.urcrnry)
            # merdidians
            if contains_centre:
                mapLonStart = -180.
                mapLonStop = 180.
            else:
                mapLonStart = min(upperLeftCornerLon, bm.llcrnrlon,
                                  bm.urcrnrlon, lowerRightCornerLon)
                mapLonStop = max(upperLeftCornerLon, bm.llcrnrlon,
                                 bm.urcrnrlon, lowerRightCornerLon)
            # parallels
            mapLatStart = min(middleLowerBoundaryLat, lowerRightCornerLat,
                              bm.llcrnrlat,
                              middleUpperBoundaryLat, upperLeftCornerLat,
                              bm.urcrnrlat)
            mapLatStop = max(middleLowerBoundaryLat, lowerRightCornerLat,
                             bm.llcrnrlat,
                             middleUpperBoundaryLat, upperLeftCornerLat,
                             bm.urcrnrlat)
            if contains_centre:
                centre_lat = bm.projparams["lat_0"]
                mapLatStart = min(mapLatStart, centre_lat)
                mapLatStop = max(mapLatStop, centre_lat)
        else:
            # for other projections (preliminary): difference between the
            # lower left and the upper right corner.
            mapLonStart = bm.llcrnrlon
            mapLonStop = bm.urcrnrlon
            mapLatStart = bm.llcrnrlat
            mapLatStop = bm.urcrnrlat

        # b) parallels and meridians can be drawn with a spacing of
        #      >spacingValues< degrees. Determine the appropriate
        #      spacing for the lon/lat differences: about 10 lines
        #      should be drawn in each direction. (The following lines
        #      filter the spacingValues list for all spacing values
        #      that are larger than lat/lon difference / 10, then
        #      take the first value (first values that's larger)).
        spacingValues = [0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 30, 40]
        deltaLon = mapLonStop - mapLonStart
        deltaLat = mapLatStop - mapLatStart
        spacingLon = [i for i in spacingValues if i > (deltaLon / 10.)][0]
        spacingLat = [i for i in spacingValues if i > (deltaLat / 10.)][0]

        #   c) parallels and meridians start at the first value in the
        #      spacingLon/Lat grid that's smaller than the lon/lat of the
        #      lower left corner; they stop at the first values in the
        #      grid that's larger than the lon/lat of the upper right corner.
        lonStart = np.floor((mapLonStart / spacingLon)) * spacingLon
        lonStop = np.ceil((mapLonStop / spacingLon)) * spacingLon
        latStart = np.floor((mapLatStart / spacingLat)) * spacingLat
        latStop = np.ceil((mapLatStop / spacingLat)) * spacingLat

        #   d) call the basemap methods to draw the lines in the determined
        #      range.
        bm.map_parallels = bm.drawparallels(np.arange(latStart, latStop,
                                                      spacingLat),
                                            labels=[1, 1, 0, 0],
                                            color='0.5', dashes=[5, 5])
        bm.map_meridians = bm.drawmeridians(np.arange(lonStart, lonStop,
                                                      spacingLon),
                                            labels=[0, 0, 0, 1],
                                            color='0.5', dashes=[5, 5])

    def plot_hsection(self, data, lats, lons, bbox=(-180, -90, 180, 90),
                      level=None, figsize=(960, 640), crs=None,
                      proj_params=None,
                      valid_time=None, init_time=None, style=None,
                      resolution=-1, noframe=False, show=False,
                      transparent=False):
        """
        EPSG overrides proj_params!
        """
        if proj_params is None:
            proj_params = {"projection": "cyl"}
            bbox_units = "latlon"
        # Projection parameters from EPSG code.
        if crs is not None:
            proj_params, bbox_units = [get_projection_params(crs)[_x] for _x in ("basemap", "bbox")]

        logging.debug("plotting data..")

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
        fig = mpl.figure.Figure(figsize=figsize, dpi=dpi, facecolor=facecolor)
        logging.debug("\twith frame and legends" if not noframe else
                      "\twithout frame")
        if noframe:
            ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
        else:
            ax = fig.add_axes([0.05, 0.05, 0.9, 0.88])

        # The basemap instance is created with a fixed aspect ratio for framed
        # plots; the aspect ratio is not fixed for frameless plots (standard
        # WMS). This means that for WMS plots, the map will always fill the
        # entire image area, no matter of whether this stretches or shears the
        # map. This is the behaviour specified by the WMS standard (WMS Spec
        # 1.1.1, Section 7.2.3.8):
        # "The returned picture, regardless of its return format, shall have
        # exactly the specified width and height in pixels. In the case where
        # the aspect ratio of the BBOX and the ratio width/height are different,
        # the WMS shall stretch the returned map so that the resulting pixels
        # could themselves be rendered in the aspect ratio of the BBOX.  In
        # other words, it should be possible using this definition to request a
        # map for a device whose output pixels are themselves non-square, or to
        # stretch a map into an image area of a different aspect ratio."
        # NOTE: While the MSUI always requests image sizes that match the aspect
        # ratio, for instance the Metview 4 client does not (mr, 2011Dec16).

        # Some additional code to store the last 20 coastlines in memory for quicker
        # access.
        key = repr((proj_params, bbox, bbox_units))
        basemap_use_cache = getattr(mss_wms_settings, "basemap_use_cache", False)
        basemap_request_size = getattr(mss_wms_settings, "basemap_request_size ", 200)
        basemap_cache_size = getattr(mss_wms_settings, "basemap_cache_size", 20)
        bm_params = {"area_thresh": 1000., "ax": ax, "fix_aspect": (not noframe)}
        bm_params.update(proj_params)
        if bbox_units == "degree":
            bm_params.update({"llcrnrlon": bbox[0], "llcrnrlat": bbox[1],
                              "urcrnrlon": bbox[2], "urcrnrlat": bbox[3]})
        elif bbox_units.startswith("meter"):
            # convert meters to degrees
            try:
                bm_p = basemap.Basemap(resolution=None, **bm_params)
            except ValueError:  # projection requires some extent
                bm_p = basemap.Basemap(resolution=None, width=1e7, height=1e7, **bm_params)
            bm_center = [float(_x) for _x in bbox_units[6:-1].split(",")]
            center_x, center_y = bm_p(*bm_center)
            bbox_0, bbox_1 = bm_p(bbox[0] + center_x, bbox[1] + center_y, inverse=True)
            bbox_2, bbox_3 = bm_p(bbox[2] + center_x, bbox[3] + center_y, inverse=True)
            bm_params.update({"llcrnrlon": bbox_0, "llcrnrlat": bbox_1,
                              "urcrnrlon": bbox_2, "urcrnrlat": bbox_3})
        elif bbox_units == "no":
            pass
        else:
            raise ValueError(f"bbox_units '{bbox_units}' not known.")
        if basemap_use_cache and key in BASEMAP_CACHE:
            bm = basemap.Basemap(resolution=None, **bm_params)
            (bm.resolution, bm.coastsegs, bm.coastpolygontypes, bm.coastpolygons,
             bm.coastsegs, bm.landpolygons, bm.lakepolygons, bm.cntrysegs) = BASEMAP_CACHE[key]
            logging.debug("Loaded '%s' from basemap cache", key)
        else:
            bm = basemap.Basemap(resolution='l', **bm_params)
            # read in countries manually, as those are laoded only on demand
            bm.cntrysegs, _ = bm._readboundarydata("countries")
            if basemap_use_cache:
                BASEMAP_CACHE[key] = (bm.resolution, bm.coastsegs, bm.coastpolygontypes, bm.coastpolygons,
                                      bm.coastsegs, bm.landpolygons, bm.lakepolygons, bm.cntrysegs)
        if basemap_use_cache:
            BASEMAP_REQUESTS.append(key)
            BASEMAP_REQUESTS[:] = BASEMAP_REQUESTS[-basemap_request_size:]

            if len(BASEMAP_CACHE) > basemap_cache_size:
                useful = {}
                for idx, key in enumerate(BASEMAP_REQUESTS):
                    useful[key] = useful.get(key, 0) + idx
                least_useful = sorted([(value, key) for key, value in useful.items()])[:-basemap_cache_size]
                for _, key in least_useful:
                    del BASEMAP_CACHE[key]
                    BASEMAP_REQUESTS[:] = [_x for _x in BASEMAP_REQUESTS if key != _x]

        # Set up the map appearance.
        bm.drawcoastlines(color='0.25')
        bm.drawcountries(color='0.5')
        bm.drawmapboundary(fill_color='white')

        # zorder = 0 is necessary to paint over the filled continents with
        # scatter() for drawing the flight tracks and trajectories.
        # Curiously, plot() works fine without this setting, but scatter()
        # doesn't.
        bm.fillcontinents(color='0.98', lake_color='white', zorder=0)
        self._draw_auto_graticule(bm)

        if noframe:
            ax.axis('off')

        self.bm = bm  # !! BETTER PASS EVERYTHING AS PARAMETERS?
        self.fig = fig
        self.shift_data()
        self.mask_data()
        self._plot_style()

        # Set transparency for the output image.
        if transparent:
            fig.patch.set_alpha(0.)

        # Return the image as png embedded in a StringIO stream.
        canvas = FigureCanvas(fig)
        output = io.BytesIO()
        canvas.print_png(output)

        if show:
            logging.debug("saving figure to mpl_hsec.png ..")
            canvas.print_png("mpl_hsec.png")

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

            logging.debug("saving figure as transparent PNG with transparency index %s.", facecolor_index)
            palette_img.save(output, format="PNG", transparency=facecolor_index)

        logging.debug("returning figure..")
        return output.getvalue()

    def shift_data(self):
        """Shift the data fields such that the longitudes are in the range
        left_longitude .. left_longitude+360, where left_longitude is the
        leftmost longitude appearing in the plot.

        Necessary to prevent data cut-offs in situations where the requested
        map covers a domain that crosses the data longitude boundaries
        (e.g. data is stored on a -180..180 grid, but a map in the range
        -200..-100 is requested).
        """
        # Determine the leftmost longitude in the plot.
        axis = self.bm.ax.axis()
        ulcrnrlon, ulcrnrlat = self.bm(axis[0], axis[3], inverse=True)
        left_longitude = min(self.bm.llcrnrlon, ulcrnrlon)
        logging.debug("shifting data grid to leftmost longitude in map %2.f..", left_longitude)

        # Shift the longitude field such that the data is in the range
        # left_longitude .. left_longitude+360.
        self.lons = ((self.lons - left_longitude) % 360) + left_longitude
        self.lon_indices = self.lons.argsort()
        self.lons = self.lons[self.lon_indices]

        # Shift data fields correspondingly.
        for key in self.data:
            self.data[key] = self.data[key][:, self.lon_indices]

    def mask_data(self):
        """Mask data arrays so that all values outside the map domain
           are masked. This is required for clabel to work correctly.

        See:
        http://www.mail-archive.com/matplotlib-users@lists.sourceforge.net/msg02892.html
        (Re: [Matplotlib-users] clabel and basemap).

        (mr, 2011-01-18)
        """
        # compute native map projection coordinates of lat/lon grid.
        lonmesh_, latmesh_ = np.meshgrid(self.lons, self.lats)
        x, y = self.bm(lonmesh_, latmesh_)
        # test which coordinates are outside the map domain.

        add_x = ((self.bm.xmax - self.bm.xmin) / 10.)
        add_y = ((self.bm.ymax - self.bm.ymin) / 10.)

        mask1 = x < self.bm.xmin - add_x
        mask2 = x > self.bm.xmax + add_x
        mask3 = y > self.bm.ymax + add_y
        mask4 = y < self.bm.ymin - add_y
        mask = mask1 + mask2 + mask3 + mask4
        # mask data arrays.
        for key in self.data:
            self.data[key] = np.ma.masked_array(
                self.data[key], mask=mask, keep_mask=False)
