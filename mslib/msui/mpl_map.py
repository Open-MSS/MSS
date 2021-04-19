# -*- coding: utf-8 -*-
"""

    mslib.msui.mpl_map
    ~~~~~~~~~~~~~~~~~~

    Map canvas for the top view.
    As Matplotlib's Basemap is primarily designed to produce static plots,
    we derived a class MapCanvas to allow for a certain degree of
    interactivity. MapCanvas extends Basemap by functionality to, for
    instance, automatically draw a graticule. It also keeps references to
    plotted map elements to allow the user to toggle their visibility, or
    to redraw when map section (zoom/pan) or projection have been changed.

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2021 by the mss team, see AUTHORS.
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

import logging
import numpy as np
import matplotlib
import matplotlib.path as mpath
import matplotlib.patches as mpatches
import mpl_toolkits.basemap as basemap
try:
    import mpl_toolkits.basemap.pyproj as pyproj
except ImportError:
    logging.debug("Failed to pyproj from mpl_toolkits.basemap")
    import pyproj

from mslib.msui import mpl_pathinteractor as mpl_pi


class MapCanvas(basemap.Basemap):
    """
    Derivative of mpl_toolkits.basemap, providing additional methods to
    automatically draw a graticule and to redraw specific map elements.
    """

    def __init__(self, identifier=None, CRS=None, BBOX_UNITS=None,
                 appearance=None, **kwargs):
        """
        New constructor automatically adds coastlines, continents, and
        a graticule to the map.

        Keyword arguments are the same as for mpl_toolkits.basemap.

        Additional arguments:
        CRS -- string describing the coordinate reference system of the map.
        BBOX_UNITS -- string describing the units of the map coordinates.

        """
        # Coordinate reference system identifier and coordinate system units.
        self.crs = CRS if CRS is not None else self.crs if hasattr(self, "crs") else None
        if BBOX_UNITS is not None:
            self.bbox_units = BBOX_UNITS
        else:
            self.bbox_units = getattr(self, "bbox_units", None)

        # Dictionary containing map appearance settings.
        if appearance is not None:
            param_appearance = appearance
        else:
            param_appearance = getattr(self, "appearance", {})

        default_appearance = {"draw_graticule": True,
                              "draw_coastlines": True,
                              "fill_waterbodies": True,
                              "fill_continents": True,
                              "colour_water": ((153 / 255.), (255 / 255.), (255 / 255.), (255 / 255.)),
                              "colour_land": ((204 / 255.), (153 / 255.), (102 / 255.), (255 / 255.))}
        default_appearance.update(param_appearance)
        self.appearance = default_appearance

        # Identifier of this map canvas (used to query data structures that
        # are observed by different views).
        if identifier is not None:
            self.identifier = identifier
        else:
            self.identifier = getattr(self, "identifier", None)

        # Call the Basemap constructor. If a cylindrical projection was used
        # before, Basemap stores an EPSG code that will not be changed if
        # the Basemap constructor is called a second time. Hence, we have to
        # delete the attribute (mr, 08Feb2013).
        if hasattr(self, "epsg"):
            del self.epsg
        super(MapCanvas, self).__init__(**kwargs)
        self.kwargs = kwargs

        # Set up the map appearance.
        if self.appearance["draw_coastlines"]:
            if len(self.coastsegs) > 0 and len(self.coastsegs[0]) > 0:
                self.map_coastlines = self.drawcoastlines(zorder=3)
            self.map_countries = self.drawcountries(zorder=3)
        else:
            self.map_coastlines = None
            self.map_countries = None
        if self.appearance["fill_waterbodies"]:
            self.map_boundary = self.drawmapboundary(fill_color=self.appearance["colour_water"])
        else:
            self.map_boundary = None

        # zorder = 0 is necessary to paint over the filled continents with
        # scatter() for drawing the flight tracks and trajectories.
        # Curiously, plot() works fine without this setting, but scatter()
        # doesn't.
        if self.appearance["fill_continents"]:
            self.map_continents = self.fillcontinents(
                color=self.appearance["colour_land"], lake_color=self.appearance["colour_water"], zorder=1)
        else:
            self.map_continents = None

        self.image = None

        # Print CRS identifier into the figure.
        if self.crs is not None:
            if hasattr(self, "crs_text"):
                self.crs_text.set_text(self.crs)
            else:
                self.crs_text = self.ax.figure.text(0, 0, self.crs)

        if self.appearance["draw_graticule"]:
            try:
                self._draw_auto_graticule()
            except Exception as ex:
                logging.error("ERROR: cannot plot graticule (message: %s - '%s')", type(ex), ex)
        else:
            self.map_parallels = None
            self.map_meridians = None

        # self.warpimage() # disable fillcontinents when loading bluemarble
        self.ax.set_autoscale_on(False)

    def set_identifier(self, identifier):
        self.identifier = identifier

    def set_axes_limits(self, ax=None):
        """
        See Basemap.set_axes_limits() for documentation.

        This function is overridden in MapCanvas as a workaround to a problem
        in Basemap.set_axes_limits() that occurs in interactive matplotlib
        mode. If matplotlib.is_interactive() is True, Basemap.set_axes_limits()
        tries to redraw the canvas by accessing the pylab figure manager.
        If the matplotlib object is embedded in a Qt application, this manager
        is not available and an exception is raised. Hence, the interactive
        mode is disabled here before the original Basemap.set_axes_limits()
        method is called. It is restored afterwards.
        """
        intact = matplotlib.is_interactive()
        matplotlib.interactive(False)
        super(MapCanvas, self).set_axes_limits(ax=ax)
        matplotlib.interactive(intact)

    def _draw_auto_graticule(self):
        """
        Draw an automatically spaced graticule on the map.
        """
        # Compute some map coordinates that are required below for the automatic
        # determination of which meridians and parallels to draw.
        axis = self.ax.axis()
        upperLeftCornerLon, upperLeftCornerLat = self.__call__(
            axis[0], axis[3], inverse=True)
        lowerRightCornerLon, lowerRightCornerLat = self.__call__(
            axis[1], axis[2], inverse=True)
        middleUpperBoundaryLon, middleUpperBoundaryLat = self.__call__(
            np.mean([axis[0], axis[1]]), axis[3], inverse=True)
        middleLowerBoundaryLon, middleLowerBoundaryLat = self.__call__(
            np.mean([axis[0], axis[1]]), axis[2], inverse=True)

        # Determine which parallels and meridians should be drawn.
        #   a) determine which are the minimum and maximum visible
        #      longitudes and latitudes, respectively. These
        #      values depend on the map projection.
        if self.projection in ['npstere', 'spstere', 'stere', 'lcc']:
            # For stereographic projections: Draw meridians from the minimum
            # longitude contained in the map at one of the four corners to the
            # maximum longitude at one of these corner points. If
            # the southern or norther pole  is contained in the map, draw all
            # meridians around the globe.
            # Draw parallels from the min latitude contained in the map at
            # one of the four corners OR the middle top or bottom to the
            # maximum latitude at one of these six points.
            # If the map centre in contained in the map, replace either
            # start or end latitude by the centre latitude (whichever is
            # smaller/larger).

            # check if centre point of projection is contained in the map,
            # use projection coordinates for this test
            centre_x = self.projparams["x_0"]
            centre_y = self.projparams["y_0"]
            centre_lon, centre_lat = self.__call__(centre_x, centre_y, inverse=True)
            if centre_lat > 0:
                pole_lon, pole_lat = 0, 90
            else:
                pole_lon, pole_lat = 0, -90
            pole_x, pole_y = self.__call__(pole_lon, pole_lat)
            if self.urcrnrx > self.llcrnrx:
                contains_pole = (self.llcrnrx <= pole_x <= self.urcrnrx)
            else:
                contains_pole = (self.llcrnrx >= pole_x >= self.urcrnrx)
            if self.urcrnry > self.llcrnry:
                contains_pole = contains_pole and (self.llcrnry <= pole_y <= self.urcrnry)
            else:
                contains_pole = contains_pole and (self.llcrnry >= pole_y >= self.urcrnry)

            # merdidians
            if contains_pole:
                mapLonStart = -180.
                mapLonStop = 180.
            else:
                mapLonStart = min(upperLeftCornerLon, self.llcrnrlon,
                                  self.urcrnrlon, lowerRightCornerLon)
                mapLonStop = max(upperLeftCornerLon, self.llcrnrlon,
                                 self.urcrnrlon, lowerRightCornerLon)
            # parallels
            mapLatStart = min(middleLowerBoundaryLat, lowerRightCornerLat,
                              self.llcrnrlat,
                              middleUpperBoundaryLat, upperLeftCornerLat,
                              self.urcrnrlat)
            mapLatStop = max(middleLowerBoundaryLat, lowerRightCornerLat,
                             self.llcrnrlat,
                             middleUpperBoundaryLat, upperLeftCornerLat,
                             self.urcrnrlat)
            if contains_pole:
                centre_lat = self.projparams["lat_0"]
                mapLatStart = min(mapLatStart, centre_lat)
                mapLatStop = max(mapLatStop, centre_lat)
        else:
            # for other projections (preliminary): difference between the
            # lower left and the upper right corner.
            mapLonStart = self.llcrnrlon
            mapLonStop = self.urcrnrlon
            mapLatStart = self.llcrnrlat
            mapLatStop = self.urcrnrlat

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
        spacingLon = [i for i in spacingValues if i > (deltaLon / 11.)][0]
        spacingLat = [i for i in spacingValues if i > (deltaLat / 11.)][0]

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
        self.map_parallels = self.drawparallels(np.arange(latStart, latStop,
                                                          spacingLat),
                                                labels=[1, 1, 0, 0], zorder=3)
        self.map_meridians = self.drawmeridians(np.arange(lonStart, lonStop,
                                                          spacingLon),
                                                labels=[0, 0, 0, 1], zorder=3)

    def set_graticule_visible(self, visible=True):
        """
        Set the visibily of the graticule.

        Removes a currently visible graticule by deleting internally stored
        line and text objects representing graticule lines and labels, then
        redrawing the map canvas.

        See http://www.mail-archive.com/matplotlib-users@lists.sourceforge.net/msg09349.html
        """
        self.appearance["draw_graticule"] = visible
        if visible and self.map_parallels is None and self.map_meridians is None:
            # Draw new graticule if visible is True and no current graticule
            # exists.
            self._draw_auto_graticule()
            # Update the figure canvas.
            self.ax.figure.canvas.draw()
        elif not visible and self.map_parallels is not None and self.map_meridians is not None:
            # If visible if False, remove current graticule if one exists.
            # Every item in self.map_parallels and self.map_meridians is
            # a tuple of a list of lines and a list of text labels.
            for item in self.map_parallels.values():
                for line in item[0]:
                    line.remove()
                for text in item[1]:
                    text.remove()
            for item in self.map_meridians.values():
                for line in item[0]:
                    line.remove()
                for text in item[1]:
                    text.remove()
            self.map_parallels = None
            self.map_meridians = None
            # Update the figure canvas.
            self.ax.figure.canvas.draw()

    def set_fillcontinents_visible(self, visible=True, land_color=None,
                                   lake_color=None):
        """
        Set the visibility of continent fillings.
        """
        if land_color is not None:
            self.appearance["colour_land"] = land_color
        if lake_color is not None:
            self.appearance["colour_water"] = lake_color
        self.appearance["fill_continents"] = visible

        if visible and self.map_continents is None:
            # zorder = 0 is necessary to paint over the filled continents with
            # scatter() for drawing the flight tracks and trajectories.
            # Curiously, plot() works fine without this setting, but scatter()
            # doesn't.
            self.map_continents = self.fillcontinents(color=self.appearance["colour_land"],
                                                      lake_color=self.appearance["colour_water"],
                                                      zorder=1)
            self.ax.figure.canvas.draw()
        elif not visible and self.map_continents is not None:
            # Remove current fills. They are stored as a list of polygon patches
            # in self.map_continents.
            for patch in self.map_continents:
                patch.remove()
            self.map_continents = None
            self.ax.figure.canvas.draw()
        elif visible and self.map_continents is not None:
            # Colours have changed: Remove the old fill and redraw.
            for patch in self.map_continents:
                patch.remove()
            self.map_continents = self.fillcontinents(color=self.appearance["colour_land"],
                                                      lake_color=self.appearance["colour_water"],
                                                      zorder=1)
            self.ax.figure.canvas.draw()

    def set_coastlines_visible(self, visible=True):
        """
        Set the visibility of coastlines and country borders.
        """
        self.appearance["draw_coastlines"] = visible
        if visible and self.map_coastlines is None and self.map_countries is None:
            self.map_coastlines = self.drawcoastlines(zorder=3)
            self.map_countries = self.drawcountries(zorder=3)
            self.ax.figure.canvas.draw()
        elif not visible and self.map_coastlines is not None and self.map_countries is not None:
            self.map_coastlines.remove()
            self.map_countries.remove()
            del self.cntrysegs
            self.map_coastlines = None
            self.map_countries = None
            self.ax.figure.canvas.draw()

    def set_mapboundary_visible(self, visible=True, bg_color='#99ffff'):
        """
        """
        # TODO: This doesn't work. Removing the map background only makes sense
        #      if there's a second image underneath this map. Maybe we should work
        #      with alpha values instead.
        self.appearance["fill_waterbodies"] = visible
        self.appearance["colour_water"] = bg_color

        if not visible and self.map_boundary is not None:
            try:
                self.map_boundary.remove()
            except NotImplementedError as ex:
                logging.debug("%s", ex)
            self.map_boundary = None
            self.ax.figure.canvas.draw()
        elif visible:
            self.map_boundary = self.drawmapboundary(fill_color=bg_color)
            self.ax.figure.canvas.draw()

    def update_with_coordinate_change(self, kwargs_update=None):
        """
        Redraws the entire map. This is necessary after zoom/pan operations.

        Determines corner coordinates of the current axes, removes all items
        belonging the the current map and draws a new one by calling
        self.__init__().

        DRAWBACK of this approach is that the map coordinate system changes, as
        basemap always takes the lower left axis corner as (0,0). This means
        that all other objects on the matplotlib canvas (flight track, markers,
        ..) will be incorrectly placed after a redraw. Their coordinates need
        to be adjusted by 1) transforming their coordinates to lat/lon BEFORE
        the map is redrawn, 2) redrawing the map, 3) transforming the stored
        lat/lon coordinates to the new map coordinates.
        """
        # Convert the current axis corners to lat/lon coordinates.
        axis = self.ax.axis()
        self.kwargs['llcrnrlon'], self.kwargs['llcrnrlat'] = \
            self.__call__(axis[0], axis[2], inverse=True)
        self.kwargs['urcrnrlon'], self.kwargs['urcrnrlat'] = \
            self.__call__(axis[1], axis[3], inverse=True)
        logging.debug("corner coordinates (lat/lon): ll(%.2f,%.2f), ur(%.2f,%.2f)",
                      self.kwargs['llcrnrlat'], self.kwargs['llcrnrlon'],
                      self.kwargs['urcrnrlat'], self.kwargs['urcrnrlon'])

        if (self.kwargs.get("projection") in ["cyl"] or
                self.kwargs.get("epsg") in ["4326"]):
            # Latitudes in cylindrical projection need to be within -90..90.
            self.kwargs['llcrnrlat'] = max(self.kwargs['llcrnrlat'], -90)
            self.kwargs['urcrnrlat'] = max(self.kwargs['urcrnrlat'], -89)
            self.kwargs['llcrnrlat'] = min(self.kwargs['llcrnrlat'], 89)
            self.kwargs['urcrnrlat'] = min(self.kwargs['urcrnrlat'], 90)
            # Longitudes in cylindrical projection need to be within -360..540.
            self.kwargs["llcrnrlon"] = max(self.kwargs["llcrnrlon"], -360)
            self.kwargs["urcrnrlon"] = max(self.kwargs["urcrnrlon"], -359)
            self.kwargs["llcrnrlon"] = min(self.kwargs["llcrnrlon"], 539)
            self.kwargs["urcrnrlon"] = min(self.kwargs["urcrnrlon"], 540)

        # Remove the current map artists.
        grat_vis = self.appearance["draw_graticule"]
        self.set_graticule_visible(False)
        self.appearance["draw_graticule"] = grat_vis
        if self.map_coastlines is not None and (len(self.coastsegs) > 0 and len(self.coastsegs[0]) > 0):
            self.map_coastlines.remove()

        if self.image is not None:
            self.image.remove()
            self.image = None

        # Refer to Basemap.drawcountries() on how to remove country borders.
        # In addition to the matplotlib lines, the loaded country segment data
        # needs to be loaded. THE SAME NEEDS TO BE DONE WITH RIVERS ETC.
        if self.map_countries is not None:
            self.map_countries.remove()
            del self.cntrysegs

        # map_boundary is None for rectangular projections (basemap simply sets
        # the background colour).
        if self.map_boundary is not None:
            try:
                self.map_boundary.remove()
            except NotImplementedError as ex:
                logging.debug("%s", ex)
            self.map_boundary = None

        cont_vis = self.appearance["fill_continents"]
        self.set_fillcontinents_visible(False)
        self.appearance["fill_continents"] = cont_vis

        # POSSIBILITY A): Call self.__init__ again with stored keywords.
        # Update kwargs if new parameters such as the map region have been
        # given.
        if kwargs_update:
            proj_keys = ["epsg", "projection"]
            if any(_x in kwargs_update for _x in proj_keys):
                for key in (_x for _x in proj_keys if _x in self.kwargs):
                    del self.kwargs[key]
            self.kwargs.update(kwargs_update)
        self.__init__(**self.kwargs)

        # TODO: HOW TO MAKE THIS MORE EFFICIENT.
        # POSSIBILITY B): Only set the Basemap parameters that influence the
        # plot (corner lat/lon, x/y, width/height, ..) and re-define the
        # polygons that represent the coastlines etc. In Basemap, they are
        # defined in __init__(), at the very bottom (the code that comes
        # with the comments
        #    >> read in coastline polygons, only keeping those that
        #    >> intersect map boundary polygon.
        # ). Basemap only loads the coastline data that is actually displayed.
        # If we only change llcrnrlon etc. here and replot coastlines etc.,
        # the polygons and the map extent will remain the same.
        # However, it should be possible to make a map change WITHOUT changing
        # coordinates.
        #

    # self.llcrnrlon = llcrnrlon
    # self.llcrnrlat = llcrnrlat
    # self.urcrnrlon = urcrnrlon
    # self.urcrnrlat = urcrnrlat
    # self.llcrnrx = axis[0]
    # self.llcrnry = axis[2]
    # self.urcrnrx = axis[1]
    # self.urcrnry = axis[3]

    def imshow(self, X, **kwargs):
        """
        Overloads basemap.imshow(). Deletes any existing image and
        redraws the figure after the new image has been plotted.
        """
        if self.image is not None:
            self.image.remove()
        self.image = super(MapCanvas, self).imshow(X, zorder=2, **kwargs)
        self.ax.figure.canvas.draw()
        return self.image

    def gcpoints2(self, lon1, lat1, lon2, lat2, del_s=100., map_coords=True):
        """
        The same as basemap.gcpoints(), but takes a distance interval del_s
        to space the points instead of a number of points.
        """
        # use great circle formula for a perfect sphere.
        gc = pyproj.Geod(a=self.rmajor, b=self.rminor)
        az12, az21, dist = gc.inv(lon1, lat1, lon2, lat2)
        npoints = int((dist + 0.5 * 1000. * del_s) / (1000. * del_s))
        lonlats = gc.npts(lon1, lat1, lon2, lat2, npoints)
        lons = [lon1]
        lats = [lat1]
        for lon, lat in lonlats:
            lons.append(lon)
            lats.append(lat)
        lons.append(lon2)
        lats.append(lat2)
        if map_coords:
            x, y = self(lons, lats)
        else:
            x, y = (lons, lats)
        return x, y

    def gcpoints_path(self, lons, lats, del_s=100., map_coords=True):
        """
        Same as gcpoints2, but for an entire path, i.e. multiple
        line segments. lons and lats are lists of waypoint coordinates.
        """
        # use great circle formula for a perfect sphere.
        gc = pyproj.Geod(a=self.rmajor, b=self.rminor)
        assert len(lons) == len(lats)
        assert len(lons) > 1
        gclons = [lons[0]]
        gclats = [lats[0]]
        for i in range(len(lons) - 1):
            az12, az21, dist = gc.inv(lons[i], lats[i], lons[i + 1], lats[i + 1])
            npoints = int((dist + 0.5 * 1000. * del_s) / (1000. * del_s))
            # BUG -- weird path in cyl projection on waypoint move
            # On some system configurations, the path is wrongly plotted when one
            # of the waypoints is moved by the user and the current projection is cylindric.
            # The weird thing is that when comparing cyl projection and stereo projection
            # (which works), the exact same arguments are passed to gc.npts(). Also, the
            # gc is initialised with the exact same a and b. Nevertheless, for the cyl
            # projection, gc.npts() returns lons that connect lon1 and lat2, not lon1 and
            # lon2 ... I cannot figure out why, maybe this is an issue in certain versions
            # of pyproj?? (mr, 16Oct2012)
            lonlats = gc.npts(lons[i], lats[i], lons[i + 1], lats[i + 1], npoints)
            # The cylindrical projection of matplotlib is not periodic, that means that
            # -170 longitude and 190 longitude are not identical. The gc projection however
            # assumes identity and maps all longitudes to -180 to 180. This is no issue for
            # most other projections.
            # The clean solution would be to have a periodic display, where the locations
            # and path are plotted periodically every 360 degree. As long as this is not
            # supported by matplotlib.basemap, we "hack" this to map the path to the
            # longitude range defined by the locations. This breaks potentially down in case
            # that the locations are too far apart (>180 degree), but this is not the typical
            # use case and will thus hopefully not pose a problem.
            if self.projection == "cyl" and npoints > 0:
                lonlats = np.asarray(lonlats)
                milon = min(lons[i], lons[i + 1])
                malon = max(lons[i], lons[i + 1])
                sel = lonlats[:, 0] < milon
                lonlats[sel, 0] += 360
                sel = lonlats[:, 0] > malon
                lonlats[sel, 0] -= 360

            for lon, lat in lonlats:
                gclons.append(lon)
                gclats.append(lat)
            gclons.append(lons[i + 1])
            gclats.append(lats[i + 1])
        if map_coords:
            x, y = self(gclons, gclats)
        else:
            x, y = (gclons, gclats)
        return x, y

    def drawgreatcircle_path(self, lons, lats, del_s=100., **kwargs):
        """
        """
        x, y = self.gcpoints_path(lons, lats, del_s=del_s)
        return self.plot(x, y, **kwargs)


class SatelliteOverpassPatch(object):
    """
    Represents a satellite overpass on the top view map (satellite
    track and, if available, swath).
    """

    # TODO: Derive this class from some Matplotlib actor class? Or create
    #       a new abstract base class for objects that can be drawn on the
    #       map -- they all should provide methods remove(), update(),
    #       etc. update() should automatically remap the object to new map
    #       coordinates.
    def __init__(self, mapcanvas, segment):
        """
        """
        self.map = mapcanvas
        self.segment = segment
        # Filter those time elements that correspond to masked positions -- this
        # way the indexes in self.utc correspond to those in self.sat.
        # np.ma.getmaskarray is necessary as ..mask only returns a scalar
        # "False" if the array contains no masked entries.
        self.utc = segment["utc"][~np.ma.getmaskarray(segment["satpos"])[:, 0]]
        self.sat = np.ma.compress_rows(segment["satpos"])
        self.sw_l = np.ma.compress_rows(segment["swath_left"])
        self.sw_r = np.ma.compress_rows(segment["swath_right"])
        self.trackline = None
        self.patch = None
        self.texts = []
        self.draw()

    def draw(self):
        """
        Do the actual plotting of the patch.
        """
        # Plot satellite track.
        sat = np.copy(self.sat)
        sat[:, 0], sat[:, 1] = self.map(sat[:, 0], sat[:, 1])
        self.trackline = self.map.plot(sat[:, 0], sat[:, 1], zorder=10,
                                       marker='+', markerfacecolor='g')

        # Plot polygon patch that represents the swath of the sensor.
        sw_l = self.sw_l
        sw_r = self.sw_r
        Path = mpath.Path
        pathdata = [(Path.MOVETO, self.map(sw_l[0, 0], sw_l[0, 1]))]
        for point in sw_l[1:]:
            pathdata.append((Path.LINETO, self.map(point[0], point[1])))
        for point in sw_r[::-1]:
            pathdata.append((Path.LINETO, self.map(point[0], point[1])))
        codes, verts = list(zip(*pathdata))
        path = mpl_pi.PathH(verts, codes, map=self.map)
        patch = mpatches.PathPatch(path, facecolor='yellow',
                                   edgecolor='yellow', alpha=0.4, zorder=10)
        self.patch = patch
        self.map.ax.add_patch(patch)

        # Draw text labels.
        self.texts.append(self.map.ax.text(sat[0, 0], sat[0, 1],
                                           self.utc[0].strftime("%H:%M:%S"),
                                           zorder=10,
                                           bbox=dict(facecolor='white',
                                                     alpha=0.5,
                                                     edgecolor='none')))
        self.texts.append(self.map.ax.text(sat[-1, 0], sat[-1, 1],
                                           self.utc[-1].strftime("%H:%M:%S"),
                                           zorder=10,
                                           bbox=dict(facecolor='white',
                                                     alpha=0.5,
                                                     edgecolor='none')))

        self.map.ax.figure.canvas.draw()

    def update(self):
        """
        Removes the current plot of the patch and redraws the patch.
        This is necessary, for instance, when the map projection and/or
        extent has been changed.
        """
        self.remove()
        self.draw()

    def remove(self):
        """
        Remove this satellite patch from the map canvas.
        """
        if self.trackline is not None:
            for element in self.trackline:
                element.remove()
            self.trackline = None
        if self.patch is not None:
            self.patch.remove()
            self.patch = None
        for element in self.texts:
            # Removal of text elements sometimes fails. I don't know why,
            # the plots look fine nevertheless.
            try:
                element.remove()
            except Exception as ex:
                logging.error("Wildcard exception caught: %s %s", type(ex), ex)
