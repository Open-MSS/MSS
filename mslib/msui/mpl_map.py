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

from __future__ import division

from builtins import str

import logging
import numpy as np
import matplotlib
import matplotlib.path as mpath
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib import patheffects
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.geodesic as gd
from mslib.msui import mpl_pathinteractor as mpl_pi
from mslib.msui import trajectory_item_tree as titree
from mslib.utils import npts_cartopy, get_projection_params


class MapCanvas():
    """Derivative of mpl_toolkits.basemap, providing additional methods to
       automatically draw a graticule and to redraw specific map elements.
    """

    def __init__(self, identifier=None, CRS=None, BBOX_UNITS=None,
                 traj_item_tree=None, appearance=None, fig=None, **kwargs):
        """New constructor automatically adds coastlines, continents, and
           a graticule to the map.

        Keyword arguments are the same as for mpl_toolkits.basemap.

        Additional arguments:
        CRS -- string describing the coordinate reference system of the map.
        BBOX_UNITS -- string describing the units of the map coordinates.

        """
        # Coordinate reference system identifier and coordinate system units.
        self.appearance = appearance
        self.fig = fig
        self.map_grid = False
        self.crs = CRS if CRS is not None else self.crs if hasattr(self, "crs") else None
        if BBOX_UNITS is not None:
            self.bbox_units = BBOX_UNITS
        else:
            self.bbox_units = getattr(self, "bbox_units", None)

        # BBOX = [kwargs['llcrnrlon'], kwargs['urcrnrlon'], kwargs['llcrnrlat'], kwargs['urcrnrlat']]

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
        user_proj = get_projection_params(self.crs)["basemap"]
        if kwargs["fixed"] is True:
            ax = self.fig.add_subplot(1, 1, 1, projection=user_proj['projection'])
        else:
            BBOX = [kwargs['llcrnrlon'], kwargs['urcrnrlon'], kwargs['llcrnrlat'], kwargs['urcrnrlat']]
            ax = self.fig.add_subplot(1, 1, 1, projection=user_proj['projection'])
            ax.set_extent(BBOX)
        self.fig.canvas.draw()
        self.ax = ax
        self.kwargs = kwargs
        self.init_features(appearance)

        # Print CRS identifier into the figure.
        if self.crs is not None:
            if hasattr(self, "crs_text"):
                self.crs_text.set_text(self.crs)
            else:
                self.crs_text = self.ax.projection

        # Connect to the trajectory item tree, if defined.
        self.traj_item_tree = traj_item_tree if traj_item_tree is not None else self.traj_item_tree if hasattr(
            self, "traj_item_tree") else None
        if traj_item_tree is not None:
            self.set_trajectory_tree(traj_item_tree)

        # The View may be destroyed and then this class is left dangling due to the connected
        # trajectories unless we disconnect it.
        self.ax.figure.canvas.destroyed.connect(self.disconnectTrajectories)

    def init_features(self, appearance):
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

        # Set up the map appearance.
        self.map_coastlines = self.ax.coastlines(zorder=3)
        self.map_countries = self.ax.add_feature(cfeature.BORDERS, linestyle='-', alpha=0.5)
        if self.appearance["draw_coastlines"]:
            self.map_coastlines.set_visible(True)
            self.map_countries.set_visible(True)
        else:
            self.map_coastlines.set_visible(False)
            self.map_countries.set_visible(False)
        if self.appearance["fill_waterbodies"]:
            self.map_boundary = self.ax.add_feature(cfeature.OCEAN, facecolor=self.appearance["colour_water"])
        else:
            self.map_boundary = None

        # zorder = 0 is necessary to paint over the filled continents with
        # scatter() for drawing the flight tracks and trajectories.
        # Curiously, plot() works fine without this setting, but scatter()
        # doesn't.
        if self.appearance["fill_continents"]:
            self.map_continents = (self.ax.add_feature(cfeature.LAND, facecolor=self.appearance["colour_land"]),
                                   self.ax.add_feature(cfeature.OCEAN, facecolor=self.appearance["colour_water"]))
        else:
            self.map_continents = None

        self.image = None

        self.gl = self.ax.gridlines()
        self.gl.xlabels_top = False
        self.gl.xlines = False
        self.gl.ylines = False

        if self.appearance["draw_graticule"]:
            try:
                if self.ax.projection == ccrs.PlateCarree():
                    self.gl.xlabels_bottom = True
                    self.gl.ylabels_left = True
                    self.gl.ylabels_right = True
                self.gl.xlines = True
                self.gl.ylines = True
                self.map_grid = True
            except Exception as ex:
                logging.error(u"ERROR: cannot plot graticule (message: {} - '{}')".format(type(ex), ex))
        else:
            self.map_grid = False
        # self.warpimage() # disable fillcontinents when loading bluemarble
        self.ax.set_autoscale_on(False)

    def set_identifier(self, identifier):
        self.identifier = identifier

    def set_axes_limits(self, ax=None):
        """See Basemap.set_axes_limits() for documentation.

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

    def set_graticule_visible(self, visible=True):
        """Set the visibily of the graticule.

        Removes a currently visible graticule by deleting internally stored
        line and text objects representing graticule lines and labels, then
        redrawing the map canvas.

        See http://www.mail-archive.com/matplotlib-users@lists.sourceforge.net/msg09349.html
        """
        self.appearance["draw_graticule"] = visible
        if visible and self.map_grid is False:
            # Draw new graticule if visible is True and no current graticule
            # exists.
            self.gl = self.ax.gridlines()
            if self.ax.projection == ccrs.PlateCarree():
                self.gl.xlabels_bottom = True
                self.gl.ylabels_left = True
                self.gl.ylabels_right = True
            self.gl.xlines = True
            self.gl.ylines = True
            self.map_grid = True
            self.fig.canvas.draw()
        elif not visible and self.map_grid is True:
            # If visible if False, remove current graticule if one exists.
            # Every item in self.map_parallels and self.map_meridians is
            # a tuple of a list of lines and a list of text labels.
            self.gl = self.ax.gridlines()
            self.gl.xlines = False
            self.gl.ylines = False
            self.map_grid = False
            self.update_with_coordinate_change(self.kwargs, True)
            self.fig.canvas.draw()

    def set_fillcontinents_visible(self, visible=True, land_color=None,
                                   lake_color=None):
        """Set the visibility of continent fillings.
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
            self.map_continents = (self.ax.add_feature(cfeature.LAND, facecolor=self.appearance["colour_land"]),
                                   self.ax.add_feature(cfeature.OCEAN, facecolor=self.appearance["colour_water"]))
            self.fig.canvas.draw()
        elif not visible and self.map_continents is not None:
            # Remove current fills. They are stored as a list of polygon patches
            # in self.map_continents.
            # for patch in self.map_continents:
            #     patch.remove()
            self.map_continents = None
            self.fig.canvas.draw()
        elif visible and self.map_continents is not None:
            # Colours have changed: Remove the old fill and redraw.
            # for patch in self.map_continents:
            #     patch.remove()
            self.map_continents = (self.ax.add_feature(cfeature.LAND, facecolor=self.appearance["colour_land"]),
                                   self.ax.add_feature(cfeature.OCEAN, facecolor=self.appearance["colour_water"]))
            self.fig.canvas.draw()

    def set_coastlines_visible(self, visible=True):
        """Set the visibility of coastlines and country borders.
        """
        self.appearance["draw_coastlines"] = visible
        if visible:
            self.map_coastlines.set_visible(True)
            self.map_countries.set_visible(True)
            # self.map_countries = self.ax.add_feature(cfeature.BORDERS, linestyle='--', alpha=0.5)
            self.fig.canvas.draw()
        elif not visible:
            self.map_coastlines.set_visible(False)
            self.map_countries.set_visible(False)
            self.fig.canvas.draw()

    def set_mapboundary_visible(self, visible=True, bg_color='#99ffff'):
        """
        """
        # TODO: This doesn't work. Removing the map background only makes sense
        #      if there's a second image underneath this map. Maybe we should work
        #      with alpha values instead.
        self.appearance["fill_waterbodies"] = visible
        self.appearance["colour_water"] = bg_color

        if not visible and self.map_boundary is not None:
            self.map_boundary.remove()
            self.map_boundary = None
            self.fig.canvas.draw()
        elif visible:
            self.fig.canvas.draw()

    def update_with_coordinate_change(self, kwargs_update=None, unchanged=False):
        """Redraws the entire map. This is necessary after zoom/pan operations.

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
        # Convert the current axis corners to lat/lon coordinates.kwargs.get('projection')
        cont_vis = self.appearance["fill_continents"]
        self.set_fillcontinents_visible(False)
        self.appearance["fill_continents"] = cont_vis

        # POSSIBILITY A): Call self.__init__ again with stored keywords.
        # Update kwargs if new parameters such as the map region have been
        # given.
        user_proj = self.ax.projection
        curr_extent = self.ax.get_extent(ccrs.PlateCarree())
        require_new_axis = False
        if kwargs_update:
            proj_keys = ["epsg", "projection"]
            if any(_x in kwargs_update for _x in proj_keys):
                for key in (_x for _x in proj_keys if _x in self.kwargs):
                    del self.kwargs[key]
            require_new_axis = True
            map_keys = ('llcrnrlon', 'llcrnrlat', 'urcrnrlon', 'urcrnrlat')
            for key in map_keys:
                if key in self.kwargs:
                    del self.kwargs[key]
            self.kwargs.update(kwargs_update)

        kwargs = self.kwargs

        if require_new_axis:
            self.crs = kwargs['CRS'] if kwargs.get('CRS') is not None else self.crs if hasattr(self, "crs") else None
            if kwargs.get('BBOX_UNITS') is not None:
                self.bbox_units = kwargs['BBOX_UNITS']
            else:
                self.bbox_units = getattr(self, "bbox_units", None)

            self.fig.clf()
            if unchanged:
                ax = self.fig.add_subplot(1, 1, 1, projection=user_proj)
                ax.set_extent(curr_extent)
            else:
                if kwargs["fixed"] is True:
                    ax = self.fig.add_subplot(1, 1, 1, projection=self.kwargs['projection'])
                else:
                    try:
                        BBOX = [kwargs['llcrnrlon'], kwargs['urcrnrlon'], kwargs['llcrnrlat'], kwargs['urcrnrlat']]
                        ax = self.fig.add_subplot(1, 1, 1, projection=self.kwargs['projection'])
                        ax.set_extent(BBOX)
                    except KeyError:
                        ax = self.fig.add_subplot(1, 1, 1, projection=self.kwargs['projection'])
                        pass
            self.ax = ax
        self.fig.canvas.draw()
        self.init_features(self.appearance)
        self.update_trajectory_items()

    def imshow(self, X, **kwargs):
        """Overloads basemap.imshow(). Deletes any existing image and
           redraws the figure after the new image has been plotted.
        """
        ax = self.ax
        if self.image is not None:
            self.image.remove()
        self.image = self.ax.imshow(X, transform=ax.projection, extent=ax.get_extent(), zorder=2, **kwargs)
        self.fig.canvas.draw()
        return self.image

    def set_trajectory_tree(self, tree):
        """Set a reference to the tree data structure containing the information
           about the elements plotted on the map (e.g. flight tracks,
           trajectories).
        """
        logging.debug("registering trajectory tree model")
        # Disconnect old tree, if defined.
        if self.traj_item_tree is not None:
            self.traj_item_tree.dataChanged.disconnect(self.update_from_trajectory_tree)
        # Set and connect new tree.
        self.traj_item_tree = tree
        self.traj_item_tree.dataChanged.connect(self.update_from_trajectory_tree)
        # Draw tree items.
        self.update_trajectory_items()

    def disconnectTrajectories(self):
        if self.traj_item_tree is not None:
            self.traj_item_tree.dataChanged.disconnect(self.update_from_trajectory_tree)

    def update_from_trajectory_tree(self, index1, index2):
        """This method should be connected to the 'dataChanged()' signal
           of the MapItemsTree.

        NOTE: If index1 != index2, the entire tree will be updated (I haven't
              found out so far how to get all the items between the two
              indices).
        """
        if self.traj_item_tree is None:
            return
        # Update the map elements if the change that occured in traj_item_tree
        # affected a LagrantoMapItem.
        item = index1.internalPointer()
        item2 = index2.internalPointer()
        if isinstance(item, titree.LagrantoMapItem):
            last_change = self.traj_item_tree.getLastChange()
            # Update the given item or the entire tree if the two given
            # items are different.
            self.update_trajectory_items(item=item if item == item2 else None,
                                         mode=last_change)

    def update_trajectory_items(self, item=None, mode="DRAW_EVERYTHING"):
        """Draw or update map elements.

        The map items tree is traversed downward starting at the item
        given as the argument 'item' (i.e. the given item and all its
        children will be processed). Also, the path from the given
        item to the root of the tree will be followed to check if any
        property (visibility, colour) is inherited from a higher level.

        If no item is given, the traverse will start at the root, i.e.
        all items on the map will be drawn or updated.

        Keyword arguments:
        item -- LagrantoMapItem instance from which the traversal should
                be started.
        mode -- string with information on what should be done (draw vs.
                update):

                DRAW_EVERYTHING -- draw or redraw all elements on the map.
                FLIGHT_TRACK_ADDED -- draw the flight track represented
                    by 'item' (including markers).
                TRAJECTORY_DIR_ADDED -- draw the trajectory represented
                    by 'item' (including markers).
                MARKER_CHANGE -- markers for the current item (and all items in
                    its subtree) have been changed. Delete the old graphics
                    instances and draw new markers.
                GXPROPERTY_CHANGE -- a graphics property has been changed (e.g.
                    colour). Perform a pylab.setp() call to change the property.
                VISIBILITY_CHANGE -- same action as for GXPROPERTY_CHANGE
        """
        # If no trajectory item tree is defined exit the method.
        if self.traj_item_tree is None:
            return

        logging.debug("updating trajectory items on map <%s>, mode %s",
                      self.identifier, mode)

        # If no item is given start at the root of the 'traj_item_tree'.
        if item is None:
            item = self.traj_item_tree.getRootItem()
            logging.debug("processing all trajectory items")

        # This method can only operate on LagrantoMapItems -- raise an exception
        # if the argument is not of this type.
        elif not isinstance(item, titree.LagrantoMapItem):
            raise TypeError("This method can only process 'LagrantoMapItem's.")

        # Traverse the tree upward from the current item to the tree root,
        # to check if there are any properties that are inherited from an
        # item node at a higher level to the current item (e.g. an item
        # inherits visibility, colour and timeMarkerInterval from its
        # ancestors).
        #
        # Default values: The item is visible and inherits no other properties.
        parent_properties = {"visible": True,
                             "colour": None,
                             "linestyle": None,
                             "linewidth": None,
                             "timeMarkerInterval": None}
        parent = item.parent()  # this would be None if item == rootItem
        while parent is not None:  # loop until root has been reached
            # Set visible to False if one item along the path to the root is
            # found to be set to invisible.
            parent_properties["visible"] = parent.isVisible(self.identifier) and parent_properties["visible"]

            # Inherit colour and time marker interval of the highest tree level
            # on which they are set (set the current property to the value
            # encountered on the current level if the property is not None,
            # otherwise keep the old value -- since we're moving upward,
            # the property will eventually have the value of the highest
            # level on which is was not None).
            for propName in ["colour", "linestyle", "linewidth",
                             "timeMarkerInterval"]:
                prop = parent.getGxElementProperty("general", propName)
                parent_properties[propName] = prop if prop \
                    else parent_properties[propName]

            # Move up one level.
            parent = parent.parent()

        # Iterative tree traversal: Put the item and its attributes on a
        # stack.
        item_stack = [(item, parent_properties)]

        # Operate on the items in the stack until the stack is empty.
        while len(item_stack) > 0:

            # Get a new item from the stack.
            item, parent_properties = item_stack.pop()

            # Its visibility is determined by its own visibility status
            # and that of its parent (i.e. the subtree it is part of).
            item_properties = {}
            item_properties["visible"] = item.isVisible(self.identifier) and parent_properties["visible"]
            #
            for propName in ["colour", "linestyle", "linewidth",
                             "timeMarkerInterval"]:
                item_properties[propName] = parent_properties[propName] \
                    if parent_properties[propName] \
                    else item.getGxElementProperty("general",
                                                   propName)

            # Push all children of the current item onto the stack that are
            # instances of LagrantoMapItem (VariableItems are not plotted on
            # the map).
            item_stack.extend([(child, item_properties) for child in item.childItems
                               if isinstance(child, titree.LagrantoMapItem)])

            # Plotting and graphics property update operations can only be
            # performed for flight tracks and trajectories.
            if not (isinstance(item, titree.FlightTrackItem) or isinstance(item, titree.TrajectoryItem)):
                continue

            if mode in ["GXPROPERTY_CHANGE", "VISIBILITY_CHANGE"]:
                # Set the visibility of all graphics elements of the current item
                # to 'itemVisible'.
                # NOTE: We do not have to test if the item is of type
                #   FlightTrackItem or TrajectoryItem, since only these
                #   two classes contain fields other that 'general' in
                #   gxElements.
                for element in item.getGxElements():
                    if element == "general":
                        continue
                    elif element == "lineplot":
                        plt.setp(
                            item.getGxElementProperty(element,
                                                      u"instance::{}".format(self.identifier)),
                            visible=item_properties["visible"],
                            color=item_properties["colour"],
                            linestyle=item_properties["linestyle"],
                            linewidth=item_properties["linewidth"])
                    elif element == "timemarker":
                        plt.setp(
                            item.getGxElementProperty(element,
                                                      u"instance::{}".format(self.identifier)),
                            visible=item_properties["visible"],
                            color=item_properties["colour"])

            elif mode in ["FLIGHT_TRACK_ADDED", "TRAJECTORY_DIR_ADDED",
                          "MARKER_CHANGE", "DRAW_EVERYTHING"]:

                # Convert lat/lon data into map coordinates, plot the item path
                # and set the visibility flag. A handle on the plot is stored
                # via the setplotInstance() method, this allows to later switch
                # on/off the visibility.
                xy = ccrs.PlateCarree().transform_points(item.getLonVariable().getVariableData(),
                                                         item.getLatVariable().getVariableData(),
                                                         src_crs=self.ax.projection)
                x, y = xy[:, 0], xy[:, 1]
                if mode != "MARKER_CHANGE":
                    # Remove old plot instances.
                    try:
                        instances = item.getGxElementProperty("lineplot",
                                                              u"instance::{}".format(self.identifier))
                        for instance in instances:
                            instance.remove()
                    except (KeyError, ValueError) as error:
                        logging.debug("KeyError, ValueError Exception %s", error)
                    # Plot new instances.
                    plot_instance = self.plot(x, y,
                                              color=item_properties["colour"],
                                              visible=item_properties["visible"],
                                              linestyle=item_properties["linestyle"],
                                              linewidth=item_properties["linewidth"])
                    item.setGxElementProperty("lineplot",
                                              u"instance::{}".format(self.identifier),
                                              plot_instance)

                # Get the indexes for the time markers. If no time markers should
                # be drawn, 'None' is returned.
                try:
                    # Try to remove an existing time marker instance from
                    # the plot.
                    old_scatter_instance = item.getGxElementProperty("timemarker",
                                                                     u"instance::{}".format(self.identifier))
                    plt.setp(old_scatter_instance, visible=False)
                    old_scatter_instance.remove()
                except (KeyError, ValueError) as error:
                    logging.debug("KeyError, ValueError Exception %s", error)
                imarker = item.getTimeMarkerIndexes()
                if imarker is not None:
                    scatter_instance = self.scatter(x[imarker], y[imarker],
                                                    s=20, c=item_properties["colour"],
                                                    visible=item_properties["visible"], linewidth=0)
                    item.setGxElementProperty("timemarker",
                                              u"instance::{}".format(self.identifier),
                                              scatter_instance)

        # Update the figure canvas.
        self.fig.canvas.draw()

    def gcpoints2(self, lon1, lat1, lon2, lat2, del_s=100., map_coords=True):
        """
        The same as basemap.gcpoints(), but takes a distance interval del_s
        to space the points instead of a number of points.
        """
        # use great circle formula for a perfect sphere.
        gc = gd.Geodesic()
        dist = gc.inverse((lon1, lat1), (lon2, lat2)).base[0, 0]
        npoints = int((dist + 0.5 * 1000. * del_s) / (1000. * del_s))
        lonlats = npts_cartopy((lon1, lat1), (lon2, lat2), npoints)
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
        """Same as gcpoints2, but for an entire path, i.e. multiple
           line segments. lons and lats are lists of waypoint coordinates.
        """
        # use great circle formula for a perfect sphere.
        gc = gd.Geodesic()
        assert len(lons) == len(lats)
        assert len(lons) > 1
        gclons = [lons[0]]
        gclats = [lats[0]]
        for i in range(len(lons) - 1):
            dist = gc.inverse((lons[i], lats[i]), (lons[i + 1], lats[i + 1])).base[0, 0]
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
            lonlats = npts_cartopy((lons[i], lats[i]), (lons[i + 1], lats[i + 1]), npoints)
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
            if str(self.ax.projection)[13:-26] == "PlateCarree" and npoints > 0:
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
            new_coords = self.ax.projection.transform_points(ccrs.PlateCarree(), np.array(gclons), np.array(gclats))
            x, y = new_coords[:, 0], new_coords[:, 1]
        else:
            x, y = (gclons, gclats)
        return x, y

    def drawgreatcircle_path(self, lons, lats, del_s=100., **kwargs):
        """
        """
        x, y = self.gcpoints_path(lons, lats, del_s=del_s)
        return self.ax.plot(x, y, **kwargs)
        # return self.ax.plot(lons, lats, transform=ccrs.Geodetic(), **kwargs)


class SatelliteOverpassPatch(object):
    """Represents a satellite overpass on the top view map (satellite
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
        """Do the actual plotting of the patch.
        """
        # Plot satellite track.
        sat = np.copy(self.sat)
        sat_xy = self.map.ax.projection.transform_points(ccrs.PlateCarree(),
                                                         sat[:, 0], sat[:, 1])
        self.trackline = self.map.ax.plot(sat_xy[:, 0], sat_xy[:, 1],
                                          zorder=10, marker='+', markerfacecolor='g')

        # Plot polygon patch that represents the swath of the sensor.
        sw_l = self.sw_l
        sw_r = self.sw_r
        Path = mpath.Path
        pathdata = [(Path.MOVETO, self.map.ax.projection.transform_point(
            sw_l[0, 0], sw_l[0, 1], ccrs.PlateCarree()))]
        for point in sw_l[1:]:
            pathdata.append((Path.LINETO, self.map.ax.projection.transform_point(
                point[0], point[1], ccrs.PlateCarree())))
        for point in sw_r[::-1]:
            pathdata.append((Path.LINETO, self.map.ax.projection.transform_point(
                point[0], point[1], ccrs.PlateCarree())))
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
        """Removes the current plot of the patch and redraws the patch.
           This is necessary, for instance, when the map projection and/or
           extent has been changed.
        """
        self.remove()
        self.draw()

    def remove(self):
        """Remove this satellite patch from the map canvas.
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


class KMLPatch(object):
    """
    Represents a KML overlay.

    KML overlay implementation is currently very crude and basic and most features are not supported.
    """

    def __init__(self, canvas, mapcanvas, kml, overwrite=False, color="red", linewidth=1):
        self.canvas = canvas
        self.map = mapcanvas
        self.kml = kml
        self.patches = []
        self.color = color
        self.linewidth = linewidth
        self.overwrite = overwrite
        self.draw()

    def compute_xy(self, coordinates):
        coords = str(coordinates).split()
        lons, lats = [[float(_x.split(",")[_i]) for _x in coords] for _i in range(2)]
        return self.map.ax.projection.transform_points(
            ccrs.PlateCarree(), np.asarray(lons), np.asarray(lats))

    def add_polygon(self, polygon, style, _):
        """
        Plot KML polygons

        :param polygon: pykml object specifying a polygon
        """
        kwargs = self.styles.get(style, {}).get("PolyStyle", {"linewidth": self.linewidth, "color": self.color})
        for boundary in ["outerBoundaryIs", "innerBoundaryIs"]:
            if hasattr(polygon, boundary):
                result = self.compute_xy(getattr(polygon, boundary).LinearRing.coordinates)
                x, y = result[:, 0], result[:, 1]
                self.patches.append(self.map.ax.plot(x, y, "-", zorder=10, **kwargs))

    def add_point(self, point, style, name):
        """
        Plot KML point

        :param point: pykml object specifying point
        :param name: name of placemark for annotation
        """
        result = self.compute_xy(point.coordinates)
        x, y = result[:, 0], result[:, 1]
        self.patches.append(self.map.ax.plot(x[0], y[0], "o", zorder=10, color=self.color))
        if name is not None:
            self.patches.append([self.map.ax.annotate(
                name, xy=(x[0], y[0]), xycoords="data", xytext=(5, 5), textcoords='offset points', zorder=10,
                path_effects=[patheffects.withStroke(linewidth=2, foreground='w')])])

    def add_line(self, line, style, _):
        """
        Plot KML line

        :param line: pykml LineString object
        """
        kwargs = self.styles.get(style, {}).get("LineStyle", {"linewidth": self.linewidth, "color": self.color})
        result = self.compute_xy(line.coordinates)
        x, y = result[:, 0], result[:, 1]
        self.patches.append(self.map.ax.plot(x, y, "-", zorder=10, **kwargs))

    def parse_geometries(self, placemark, style=None, name=None):
        if style.startswith("#"):
            # Remove # at beginning of style marking a locally defined style.
            # general urls for styles are not supported
            style = style[1:]
        for attr_name, method in (
                ("Point", self.add_point),
                ("Polygon", self.add_polygon),
                ("LineString", self.add_line),
                ("MultiGeometry", self.parse_geometries)):
            for attr in getattr(placemark, attr_name, []):
                logging.debug("Found %s", attr_name)
                method(attr, style, name)

    def parse_placemarks(self, level):
        for placemark in getattr(level, "Placemark", []):
            name = getattr(placemark, "name", None)
            style = str(getattr(placemark, "styleUrl", ""))
            logging.debug("Placemark: %s %s", style, name)
            self.parse_geometries(placemark, style, name)
        for folder in getattr(level, "Folder", []):
            name = getattr(folder, "name", None)
            logging.debug("Folder: %s", name)
            self.parse_placemarks(folder)

    def get_style_params(self, style):
        result = {
            "color": str(getattr(style, "color", "")),
            "linewidth": float(getattr(style, "width", self.linewidth))
        }
        if not result["color"] or len(result["color"]) != 8:
            result["color"] = self.color
        else:
            result["color"] = [(int(result["color"][i:i + 2], 16) / 255.) for i in range(0, 8, 2)]
        return result

    def parse_styles(self, level):
        for style in getattr(level, "Style", []):
            name = style.attrib.get("id")
            if name is None:
                continue
            self.styles[name] = {
                "LineStyle": self.get_style_params(getattr(style, "LineStyle", None)),
                "PolyStyle": self.get_style_params(getattr(style, "PolyStyle", None))
            }
        for folder in getattr(level, "Folder", []):
            name = getattr(folder, "name", None)
            logging.debug("Folder: %s", name)
            self.parse_styles(folder)

    def draw(self):
        """Do the actual plotting of the patch.
        """
        # Plot satellite track.
        self.styles = {}
        if not self.overwrite:
            self.parse_styles(self.kml.Document)
        self.parse_placemarks(self.kml.Document)
        self.canvas.draw()

    def update(self, overwrite=None, color=None, linewidth=None):
        """Removes the current plot of the patch and redraws the patch.
           This is necessary, for instance, when the map projection and/or
           extent has been changed.
        """
        if overwrite is not None:
            self.overwrite = overwrite
        if color is not None:
            self.color = color
        if linewidth is not None:
            self.linewidth = linewidth
        self.remove()
        self.draw()

    def remove(self):
        """Remove this satellite patch from the map canvas.
        """
        for patch in self.patches:
            for element in patch:
                element.remove()
        self.patches = []
        self.canvas.draw()
