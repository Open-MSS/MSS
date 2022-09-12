import sys
import argparse
import datetime
import io
import os
import xml
from fs import open_fs
import PIL.Image

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

    waypoints_list = []
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

        waypoints_list.append((lat, lon, flightlevel, location, comments))
    return waypoints_list


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
        for flight, section, vertical, filename, init_time, time in \
            self.config["automated_plotting_flights"]:
            self.params = mslib.utils.coordinate.get_projection_params(
                self.config["predefined_map_sections"][section]["CRS"].lower())
            self.params["basemap"].update(self.config["predefined_map_sections"][section]["map"])
            print(self.params)
            print("hooo")
            self.wps = load_from_ftml(filename)
            self.wp_lats, self.wp_lons, self.wp_locs = [[x[i] for x in self.wps] for i in [0, 1, 3]]
            self.wp_presss = [mslib.utils.thermolib.flightlevel2pressure(wp[2] * units.hft).to("Pa").m for wp in self.wps]
            self.fig.clear()
            self.ax = self.fig.add_subplot(111, zorder=99)
            self.path = [(wp[0], wp[1], datetime.datetime.now()) for wp in self.wps]
            self.lats, self.lons = mslib.utils.coordinate.path_points([_x[0] for _x in self.path], [_x[1] for _x in self.path],
                                                                      numpoints=self.num_interpolation_points + 1,
                                                                      connection="greatcircle")


class HsecPlotting(Plotting):
    def __init__(self):
        super(HsecPlotting, self).__init__()
        self.myfig = qt.MyTopViewFigure()
        self.myfig.fig.clear()
        self.myfig.fig.canvas.draw()
        self.line = None

    def HsecPath(self):
        self.myfig.fig.clear()
        self.ax = self.myfig.ax
        self.myfig.init_map(**(self.params["basemap"]))

        # plot path
        self.myfig.fig.canvas.draw()
        self.vertices = [list(a) for a in (zip(self.wp_lons, self.wp_lats))]
        x, y = self.myfig.map.gcpoints_path([a[0] for a in self.vertices], [a[1] for a in self.vertices])
        x, y = self.myfig.map(self.wp_lons, self.wp_lats)
        self.vertices = list(zip(x, y))
        if self.line is None:
            line, = self.myfig.ax.plot(x, y, color="blue", linestyle='-', linewidth=2, zorder=100)
        line.set_data(list(zip(*self.vertices)))
        self.myfig.ax.draw_artist(line)
        wp_scatter = self.myfig.ax.scatter(x, y, color="red", s=20, zorder=3, animated=True, visible=True)
        self.myfig.ax.draw_artist(wp_scatter)

    def HsecLabel(self):
        x, y = list(zip(*self.vertices))
        for i in range(len(self.wps)):
            textlabel = f"{self.wp_locs[i] if self.wp_locs[i] else str(i)}   "
            x, y = self.myfig.map(self.wp_lons, self.wp_lats)
            wp_labels = self.plotlabel(x, y, textlabel, len(self.wps))
            for t in wp_labels:
                self.myfig.ax.draw_artist(t)

    def plotlabel(self, x, y, textlabel, len_wps):
        wp_labels = []
        for i in range(len_wps):
            t = self.myfig.ax.text(x[i],
                             y[i],
                             textlabel,
                             bbox=dict(boxstyle="round",
                                       facecolor="white",
                                       alpha=0.5,
                                       edgecolor="none"),
                             fontweight="bold",
                             zorder=4,
                             rotation=90,
                             animated=True,
                             clip_on=True,
                             visible=True
                        )
            wp_labels.append(t)
        return wp_labels

    def HsecRetrieve(self):
        for flight, section, vertical, filename, init_time, time in \
            self.config["automated_plotting_flights"]:
            for url, layer, style, elevation in self.config["automated_plotting_hsecs"]:
                ax_bounds = plt.gca().bbox.bounds
                width, height = int(round(ax_bounds[2])), int(round(ax_bounds[3]))
                self.bbox = self.params['basemap']

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
                self.myfig.set_map()
                self.fig.savefig(f"{flight}_{layer}.png")


class VsecPlotting(Plotting):
    def __init__(self):
        super(VsecPlotting, self).__init__()
        self.tick_index_step = self.num_interpolation_points // self.num_labels
        self.vertices = None
        self.fig.clear()
        self.fig.canvas.draw()

    def setup(self):
        for flight, section, vertical, filename, init_time, time in \
            self.config["automated_plotting_flights"]:
            self.intermediate_indexes = []
            ipoint = 0
            for i, (lat, lon) in enumerate(zip(self.lats, self.lons)):
                if abs(lat - self.wps[ipoint][0]) < 1E-10 and abs(lon - self.wps[ipoint][1]) < 1E-10:
                    self.intermediate_indexes.append(i)
                    ipoint += 1
                if ipoint >= len(self.wps):
                    break
            for url, layer, style, vsec_type in self.config["automated_plotting_vsecs"]:
                self.fig.clear()
                self.ax = self.fig.add_subplot(111, zorder=99)
                self.ax.set_yscale("log")
                p_bot, p_top = [float(x) * 100 for x in vertical.split(",")]
                self.bbox = tuple([x for x in (self.num_interpolation_points,
                                  p_bot / 100, self.num_labels, p_top / 100)]
                                 )
                self.ax.grid(b=True)
                self.ax.patch.set_facecolor("None")
                sideview_size_settings = config_loader(dataset="sideview")
                plot_title_size = sideview_size_settings["plot_title_size"]
                axes_label_size = sideview_size_settings["axes_label_size"]
                pres_maj = mslib.msui.mpl_qtwidget.MySideViewFigure._pres_maj
                pres_min = mslib.msui.mpl_qtwidget.MySideViewFigure._pres_min
                lat_inds = np.arange(len(self.lats))
                tick_index_step = len(lat_inds) // self.num_labels

                if vsec_type == "no secondary axis":
                    major_ticks = [] * units.pascal
                    minor_ticks = [] * units.pascal
                    labels = []
                    ylabel = ""
                elif vsec_type == "pressure":
                    # Compute the position of major and minor ticks. Major ticks are labelled.
                    major_ticks = pres_maj[(pres_maj <= p_bot) & (pres_maj >= p_top)]
                    minor_ticks = pres_min[(pres_min <= p_bot) & (pres_min >= p_top)]
                    labels = [f"{int(_x / 100)}"
                              if (_x / 100) - int(_x / 100) == 0 else f"{float(_x / 100)}" for _x in major_ticks]
                    if len(labels) > 20:
                        labels = ["" if x.split(".")[-1][0] in "975" else x for x in labels]
                    elif len(labels) > 10:
                        labels = ["" if x.split(".")[-1][0] in "9" else x for x in labels]
                    ylabel = "pressure (hPa)"
                elif vsec_type == "pressure altitude":
                    bot_km = thermolib.pressure2flightlevel(p_bot * units.Pa).to(units.km).magnitude
                    top_km = thermolib.pressure2flightlevel(p_top * units.Pa).to(units.km).magnitude
                    ma_dist, mi_dist = 4, 1.0
                    if (top_km - bot_km) <= 20:
                        ma_dist, mi_dist = 1, 0.5
                    elif (top_km - bot_km) <= 40:
                        ma_dist, mi_dist = 2, 0.5
                    major_heights = np.arange(0, top_km + 1, ma_dist)
                    minor_heights = np.arange(0, top_km + 1, mi_dist)
                    major_ticks = thermolib.flightlevel2pressure(major_heights * units.km).magnitude
                    minor_ticks = thermolib.flightlevel2pressure(minor_heights * units.km).magnitude
                    labels = major_heights
                    ylabel = "pressure altitude (km)"
                elif vsec_type == "flight level":
                    bot_km = thermolib.pressure2flightlevel(p_bot * units.Pa).to(units.km).magnitude
                    top_km = thermolib.pressure2flightlevel(p_top * units.Pa).to(units.km).magnitude
                    ma_dist, mi_dist = 50, 10
                    if (top_km - bot_km) <= 10:
                        ma_dist, mi_dist = 20, 10
                    elif (top_km - bot_km) <= 40:
                        ma_dist, mi_dist = 40, 10
                    major_fl = np.arange(0, 2132, ma_dist)
                    minor_fl = np.arange(0, 2132, mi_dist)
                    major_ticks = thermolib.flightlevel2pressure(major_fl * units.hft).magnitude
                    minor_ticks = thermolib.flightlevel2pressure(minor_fl * units.hft).magnitude
                    labels = major_fl
                    ylabel = "flight level (hft)"
                else:
                    raise RuntimeError(f"Unsupported vertical axis type: '{vsec_type}'")

                self.ax.tick_params(axis='x', labelsize=axes_label_size)
                self.ax.set_title("vertical flight profile", fontsize=plot_title_size,
                                  horizontalalignment="left", x=0
                                 )
                self.ax.set_xlabel("lat/lon", fontsize=plot_title_size)
                self.ax.set_ylabel(ylabel, fontsize=plot_title_size)
                self.ax.set_yticks(minor_ticks, minor=True)
                self.ax.set_yticks(major_ticks, minor=False)
                self.ax.set_yticklabels([], minor=True)
                self.ax.set_yticklabels(labels, minor=False, fontsize=axes_label_size)
                self.ax.set_ylim(p_bot, p_top)
                self.ax.set_xlim(0, len(self.lats) - 1)
                self.ax.set_xticks(lat_inds[::tick_index_step])
                self.ax.set_xticklabels([f"{x[0]:2.1f}, {x[1]:2.1f}"
                                        for x in zip(self.lats[::tick_index_step], self.lons[::tick_index_step])],
                                        rotation=25, fontsize=10, horizontalalignment="right"
                                        )

    def VsecPath(self):
        for flight, section, vertical, filename, init_time, time in \
            self.config["automated_plotting_flights"]:
            for url, layer, style, elevation in self.config["automated_plotting_vsecs"]:
                self.fig.canvas.draw()
                line, = self.ax.plot(self.intermediate_indexes, self.wp_presss,
                                     color="blue", linestyle='-', linewidth=2, zorder=100
                                    )
                line.set_visible(True)

    def VsecLabel(self):
        for flight, section, vertical, filename, init_time, time in \
            self.config["automated_plotting_flights"]:
            for url, layer, style, elevation in self.config["automated_plotting_vsecs"]:
                wp_labels = []
                for i in range(len(self.wps)):
                    textlabel = f"{self.wp_locs[i] if self.wp_locs[i] else str(i)}"
                    t = self.ax.text(self.intermediate_indexes[i],
                                     self.wp_presss[i],
                                     textlabel,
                                     bbox=dict(boxstyle="round",
                                               facecolor="white",
                                               alpha=0.5,
                                               edgecolor="none"),
                                     fontweight="bold",
                                     zorder=4,
                                     rotation=90,
                                     animated=True,
                                     clip_on=True,
                                     visible=True
                                    )
                    wp_labels.append(t)
                self.fig.canvas.draw()
                for t in wp_labels:
                    self.ax.draw_artist(t)

    def VsecRetrieve(self):
        self.fig.canvas.draw()
        for flight, section, vertical, filename, init_time, time in \
            self.config["automated_plotting_flights"]:
            for url, layer, style, elevation in self.config["automated_plotting_vsecs"]:
                ax_bounds = plt.gca().bbox.bounds
                width, height = int(round(ax_bounds[2])), int(round(ax_bounds[3]))

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
                imgax = self.fig.add_axes(self.ax.get_position(), frameon=True,
                                          xticks=[], yticks=[], label="ax2", zorder=0)
                wms_image = self.VsecDraw(img, imgax)
                imgax.set_xlim(0, img.size[0] - 1)
                imgax.set_ylim(img.size[1] - 1, 0)

                plt.savefig(f"{flight}_{layer}.png")

    def VsecDraw(self, img, imgax):
        wms_image = imgax.imshow(img, interpolation="nearest", aspect="auto", origin="upper")
        return wms_image


class LsecPlotting(Plotting):
    def __init__(self):
        super(LsecPlotting, self).__init__()
        self.fig.clear()

    def setup_ticks_and_labels(self):
        self.fig.clear()
        linearview_size_settings = config_loader(dataset="linearview")
        plot_title_size = linearview_size_settings["plot_title_size"]
        axes_label_size = linearview_size_settings["axes_label_size"]

        self.bbox = (self.num_interpolation_points,)
        lat_inds = np.arange(len(self.lats))
        tick_index_step = len(lat_inds) // self.num_labels
        self.ax = self.fig.add_subplot(111, zorder=99)

        self.fig.canvas.draw()
        self.ax.tick_params(axis='both', labelsize=axes_label_size)
        self.ax.set_title("Linear flight profile", fontsize=plot_title_size, horizontalalignment='left', x=0)
        self.ax.set_xlim(0, len(self.lats) - 1)

        # setup ticks and labels
        self.ax.set_xticks(lat_inds[::tick_index_step])
        self.ax.set_xticklabels([f'{d[0]:2.1f}, {d[1]:2.1f}'for d in zip(self.lats[::tick_index_step],
                                                                            self.lons[::tick_index_step])],
                                rotation=25, horizontalalignment="right"
                                )
        self.ax.set_yscale("linear")
        self.fig.subplots_adjust(left=0.08, right=0.96, top=0.9, bottom=0.14)

    def LsecDraw(self):
        for flight, section, vertical, filename, init_time, time in \
            self.config["automated_plotting_flights"]:
            for url, layer, style in self.config["automated_plotting_lsecs"]:
                ax_bounds = plt.gca().bbox.bounds
                width, height = int(round(ax_bounds[2])), int(round(ax_bounds[3]))

                if not init_time:
                    init_time = None

                wms = MSUIWebMapService(url,
                                        username=self.config["WMS_login"][url][0],
                                        password=self.config["WMS_login"][url][1],
                                        version='1.3.0')

                path_string = ""
                for i, wp in enumerate(self.wps):
                    path_string += f"{wp[0]:.2f},{wp[1]:.2f},{self.wp_presss[i]},"
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

                for i, xm in enumerate(xml_objects):
                    data = xm.find("Data")
                    values = [float(value) for value in data.text.split(",")]
                    unit = data.attrib["unit"]
                    numpoints = int(data.attrib["num_waypoints"])

                    color = "#00AAFF"
                    scale = "linear"
                    offset = 40

                    par = self.ax.twinx() if i > 0 else self.ax
                    par.set_yscale(scale)

                    par.plot(range(numpoints), values, color)
                    if i > 0:
                        par.spines["right"].set_position(("outward", (i - 1) * offset))
                    if unit:
                        par.set_ylabel(unit)

                par.yaxis.label.set_color(color.replace("0x", "#"))

                # draw vertical lines
                vertical_lines = []
                ipoint = 0
                highlight = [[wp[0], wp[1]] for wp in self.wps]
                for i, (lat, lon) in enumerate(zip(self.lats, self.lons)):
                    if (ipoint < len(highlight) and np.hypot(lat - highlight[ipoint][0],
                        lon - highlight[ipoint][1]) < 2E-10):
                        vertical_lines.append(self.ax.axvline(i, color='k', linewidth=2, linestyle='--', alpha=0.5))
                        ipoint += 1
                self.fig.tight_layout()
                self.fig.subplots_adjust(top=0.85, bottom=0.20)
                self.fig.canvas.draw()

                plt.savefig(f"{flight}_{layer}.png")


def main():
    h = HsecPlotting()
    h.HsecPath()
    h.HsecLabel()
    h.HsecRetrieve()
    v = VsecPlotting()
    v.setup()
    v.VsecPath()
    v.VsecLabel()
    v.VsecRetrieve()
    ls = LsecPlotting()
    ls.setup_ticks_and_labels()
    ls.LsecDraw()


if __name__ == "__main__":
    main()
