from distutils.command.config import config
import sys
import argparse
import datetime
import io
import os
import xml
from fs import open_fs
import PIL.Image
import matplotlib

import mslib
import mslib.utils
import mslib.msui
import mslib.msui.mpl_map
import mslib.utils.qt
import mslib.utils.thermolib
from mslib.utils.config import config_loader, read_config_file
from mslib.utils.units import units
from mslib.msui.wms_control import MSUIWebMapService
from mslib.msui.wms_control import WMSMapFetcher
import matplotlib.pyplot as plt
import numpy as np
from mslib.utils import thermolib
import defusedxml.ElementTree as etree
import hashlib
from mslib.msui import wms_control
from mslib.msui import mpl_qtwidget as qt
from mslib.msui import mpl_pathinteractor as mpath
from mslib.msui import flighttrack as ft
import datetime


TEXT_CONFIG = {
    "bbox": dict(boxstyle="round", facecolor="white", alpha=0.5, edgecolor="none"),
    "fontweight": "bold", "zorder": 4, "fontsize": 6, "clip_on": True}


def load_from_ftml(filename):
    """Load a flight track from an XML file at <filename>.
    """
    _dirname, _name = os.path.split(filename)
    _fs = open_fs(_dirname)
    datasource = _fs.open(_name)
    wp_list = load_from_xml_data(datasource)
    return wp_list


def load_from_xml_data(datasource):
    try:
        doc = xml.dom.minidom.parse(datasource)
    except xml.parsers.expat.ExpatError as ex:
        raise SyntaxError(str(ex))

    ft_el = doc.getElementsByTagName("FlightTrack")[0]

    waypoints_list1 = []
    waypoints_list2 = []
    for wp_el in ft_el.getElementsByTagName("Waypoint"):

        location = wp_el.getAttribute("location")
        lat = float(wp_el.getAttribute("lat"))
        lon = float(wp_el.getAttribute("lon"))
        flightlevel = float(wp_el.getAttribute("flightlevel"))
        comments = wp_el.getElementsByTagName("Comments")[0]
        # If num of comments is 0(null comment), then return ''
        if len(comments.childNodes):
            comments = comments.childNodes[0].data.strip()
        else:
            comments = ''

        waypoints_list1.append((lat, lon, flightlevel, location, comments))
        waypoints_list2.append(ft.Waypoint(lat, lon, flightlevel, location, comments))
        waypoints_list2[-1].utc_time = datetime.datetime.now()
    return waypoints_list1, waypoints_list2


class Plotting():
    def __init__(self):
        read_config_file()
        self.config = config_loader()
        self.num_interpolation_points = self.config["num_interpolation_points"]
        self.num_labels = self.config["num_labels"]
        self.tick_index_step = self.num_interpolation_points // self.num_labels
        self.wps = None
        self.bbox = None
        self.wms_cache = config_loader(dataset="wms_cache")
        self.fig = plt.figure()
        section = self.config["automated_plotting_flights"][0][1]
        filename = self.config["automated_plotting_flights"][0][3]
        self.params = mslib.utils.coordinate.get_projection_params(
            self.config["predefined_map_sections"][section]["CRS"].lower())
        self.params["basemap"].update(self.config["predefined_map_sections"][section]["map"])
        print(self.params)
        self.bbox_units = self.params["bbox"]
        self.wpslist = []
        self.wpslist = load_from_ftml(filename)
        self.wps = self.wpslist[0]
        self.wp_model_data = self.wpslist[1]
        self.wp_lats, self.wp_lons, self.wp_locs = [[x[i] for x in self.wps] for i in [0, 1, 3]]
        self.wp_press = [mslib.utils.thermolib.flightlevel2pressure(wp[2] * units.hft).to("Pa").m for wp in self.wps]
        self.fig.clear()
        self.ax = self.fig.add_subplot(111, zorder=99)
        self.path = [(wp[0], wp[1], datetime.datetime.now()) for wp in self.wps]
        self.vertices = [list(a) for a in (zip(self.wp_lons, self.wp_lats))]
        self.lats, self.lons = mslib.utils.coordinate.path_points([_x[0] for _x in self.path], [_x[1] for _x in self.path],
                                                                  numpoints=self.num_interpolation_points + 1,
                                                                  connection="greatcircle"
                                                                  )


class TopViewPlotting(Plotting):
    def __init__(self, itime=None, vtime=None, no_of_plots=1):
        super(TopViewPlotting, self).__init__()
        self.itime = itime
        self.vtime = vtime
        self.no_of_plots = no_of_plots
        self.myfig = qt.MyTopViewFigure()
        self.myfig.fig.canvas.draw()
        self.line = None
        matplotlib.backends.backend_agg.FigureCanvasAgg(self.myfig.fig)
        self.ax = self.myfig.ax
        self.fig = self.myfig.fig
        self.myfig.init_map(**(self.params["basemap"]))
        self.myfig.set_map()
        self.plotter = mpath.PathH_GCPlotter(self.myfig.map)

    def TopViewPath(self):
        # plot path and label
        self.fig.canvas.draw()
        wp_lats, wp_lons, wp_locs = [[x[i] for x in self.wps] for i in [0, 1, 3]]
        self.plotter.update_from_waypoints(self.wp_model_data)
        self.plotter.redraw_path(waypoints_model_data=self.wp_model_data)

    def TopViewDraw(self):
        for flight, section, vertical, filename, init_time, time in \
            self.config["automated_plotting_flights"]:
            for url, layer, style, elevation in self.config["automated_plotting_hsecs"]:
                width, height = self.myfig.get_plot_size_in_px()
                self.bbox = self.params['basemap']
                if self.itime is not None:
                    init_time = self.itime
                if self.vtime is not None:
                    time = self.vtime
                if not init_time:
                    init_time = None

                kwargs = {"layers": [layer],
                          "styles": [style],
                          "time": time,
                          "init_time": init_time,
                          "exceptions": 'application/vnd.ogc.se_xml',
                          "level": elevation,
                          "srs": self.config["predefined_map_sections"][section]["CRS"],
                          "bbox": (self.bbox['llcrnrlon'], self.bbox['llcrnrlat'],
                                   self.bbox['urcrnrlon'], self.bbox['urcrnrlat']
                                  ),
                          "format": "image/png",
                          "size": (width, height)
                        }

                wms = wms_control.MSUIWebMapService(url,
                                                    username=self.config["WMS_login"][url][0],
                                                    password=self.config["WMS_login"][url][1],
                                                    version='1.3.0'
                                                    )

                img = wms.getmap(**kwargs)
                image_io = io.BytesIO(img.read())
                img = PIL.Image.open(image_io)
                self.myfig.draw_image(img)
                self.myfig.fig.savefig(f"{flight}_{layer}_{self.no_of_plots}.png")


class SideViewPlotting(Plotting):
    def __init__(self):
        super(SideViewPlotting, self).__init__()
        self.myfig = qt.MySideViewFigure()
        self.ax = self.myfig.ax
        self.fig = self.myfig.fig
        self.tick_index_step = self.num_interpolation_points // self.num_labels
        self.fig.canvas.draw()
        matplotlib.backends.backend_agg.FigureCanvasAgg(self.myfig.fig)

    def setup(self):
        self.intermediate_indexes = []
        ipoint = 0
        for i, (lat, lon) in enumerate(zip(self.lats, self.lons)):
            if abs(lat - self.wps[ipoint][0]) < 1E-10 and abs(lon - self.wps[ipoint][1]) < 1E-10:
                self.intermediate_indexes.append(i)
                ipoint += 1
            if ipoint >= len(self.wps):
                break
        self.myfig.setup_side_view()
        times = None
        times_visible = False
        self.myfig.redraw_xaxis(self.lats, self.lons, times, times_visible)

    def SideViewPath(self):
        self.fig.canvas.draw()
        self.plotter = mpath.PathV_Plotter(self.myfig.ax)
        self.plotter.update_from_waypoints(self.wp_model_data)
        indices = list(zip(self.intermediate_indexes, self.wp_press))
        self.plotter.redraw_path(vertices=indices,
                                 waypoints_model_data=self.wp_model_data)
        highlight = [[wp[0], wp[1]] for wp in self.wps]
        self.myfig.draw_vertical_lines(highlight, self.lats, self.lons)

    def SideViewDraw(self):
        for flight, section, vertical, filename, init_time, time in \
            self.config["automated_plotting_flights"]:
            for url, layer, style, vsec_type in self.config["automated_plotting_vsecs"]:
                width, height = self.myfig.get_plot_size_in_px()
                p_bot, p_top = [float(x) * 100 for x in vertical.split(",")]
                self.bbox = tuple([x for x in (self.num_interpolation_points,
                                  p_bot / 100, self.num_labels, p_top / 100)]
                                 )

                if not init_time:
                    init_time = None

                kwargs = {"layers": [layer],
                          "styles": [style],
                          "time": time,
                          "init_time": init_time,
                          "exceptions": 'application/vnd.ogc.se_xml',
                          "srs": "VERT:LOGP",
                          "path_str": ",".join(f"{wp[0]:.2f},{wp[1]:.2f}" for wp in self.wps),
                          "bbox": self.bbox,
                          "format": "image/png",
                          "size": (width, height)
                        }
                wms = MSUIWebMapService(url,
                                        username=self.config["WMS_login"][url][0],
                                        password=self.config["WMS_login"][url][1],
                                        version='1.3.0'
                                        )

                img = wms.getmap(**kwargs)

                image_io = io.BytesIO(img.read())
                img = PIL.Image.open(image_io)
                self.myfig.draw_image(img)
                self.myfig.fig.savefig(f"{flight}_{layer}.png", bbox_inches='tight')


class LinearViewPlotting(Plotting):
    def __init__(self):
        super(LinearViewPlotting, self).__init__()
        self.myfig = qt.MyLinearViewFigure()
        self.ax = self.myfig.ax
        matplotlib.backends.backend_agg.FigureCanvasAgg(self.myfig.fig)
        self.fig = self.myfig.fig

    def setup(self):
        self.bbox = (self.num_interpolation_points,)
        linearview_size_settings = config_loader(dataset="linearview")
        settings_dict = {"plot_title_size": linearview_size_settings["plot_title_size"],
                         "axes_label_size": linearview_size_settings["axes_label_size"]}
        self.myfig.set_settings(settings_dict)
        self.myfig.setup_linear_view()

    def LinearViewDraw(self):
        for flight, section, vertical, filename, init_time, time in \
            self.config["automated_plotting_flights"]:
            for url, layer, style in self.config["automated_plotting_lsecs"]:
                width, height = self.myfig.get_plot_size_in_px()

                if not init_time:
                    init_time = None

                wms = MSUIWebMapService(url,
                                        username=self.config["WMS_login"][url][0],
                                        password=self.config["WMS_login"][url][1],
                                        version='1.3.0')

                path_string = ""
                for i, wp in enumerate(self.wps):
                    path_string += f"{wp[0]:.2f},{wp[1]:.2f},{self.wp_press[i]},"
                path_string = path_string[:-1]

                # retrieve and draw image
                kwargs = {"layers": [layer],
                          "styles": [style],
                          "time": time,
                          "init_time": init_time,
                          "exceptions": 'application/vnd.ogc.se_xml',
                          "srs": "LINE:1",
                          "path_str": path_string,
                          "bbox": self.bbox,
                          "format": "text/xml",
                          "size": (width, height)
                         }

                xmls = wms.getmap(**kwargs)
                urlstr = wms.getmap(return_only_url=True, **kwargs)
                ending = ".xml"

                if not os.path.exists(self.wms_cache):
                    os.makedirs(self.wms_cache)
                md5_filename = os.path.join(self.wms_cache, hashlib.md5(urlstr.encode('utf-8')).hexdigest() + ending)
                with open(md5_filename, "w") as cache:
                    cache.write(str(xmls.read(), encoding="utf8"))
                if not type(xmls) == 'list':
                    xmls = [xmls]

                xml_objects = []
                for xml_ in xmls:
                    xml_data = etree.fromstring(xml_.read())
                    xml_objects.append(xml_data)

                self.myfig.draw_image(xml_objects, colors=None, scales=None)
                self.myfig.redraw_xaxis(self.lats, self.lons)
                highlight = [[wp[0], wp[1]] for wp in self.wps]
                self.myfig.draw_vertical_lines(highlight, self.lats, self.lons)
                self.myfig.fig.savefig(f"{flight}_{layer}.png", bbox_inches='tight')


def main():
    h = TopViewPlotting()
    h.TopViewPath()
    h.TopViewDraw()
    v = SideViewPlotting()
    v.setup()
    v.SideViewPath()
    v.SideViewDraw()
    ls = LinearViewPlotting()
    ls.setup()
    ls.LinearViewDraw()


if __name__ == "__main__":
    main()
