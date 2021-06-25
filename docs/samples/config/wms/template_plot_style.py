import numpy as np
import matplotlib as mpl
import mslib.mswms.mpl_hsec_styles


class HS_Template(mslib.mswms.mpl_hsec_styles.MPLBasemapHorizontalSectionStyle):
    name = "HSTemplate"  # Pick a proper camel case name starting with HS
    title = "Air Temperature with Geopotential Height"
    abstract = "Air Temperature (degC) with Geopotential Height (km) Contours"

    required_datafields = [
        # level type, CF standard name, unit
        ("pl", "air_temperature", "degC"),
        ("pl", "geopotential_height", "km")
    ]

    def _plot_style(self):
        temp_range = np.arange(-93, 28, 2)
        height_range = np.arange(0, 21, 0.1)
        fill_entity = "air_temperature"
        contour_entity = "geopotential_height"

        # main plot
        cmap = mpl.cm.plasma

        cf = self.bm.contourf(
            self.lonmesh, self.latmesh, self.data[fill_entity],
            temp_range, cmap=cmap, extend="both")
        self.add_colorbar(cf, fill_entity)

        # contour
        heights_c = self.bm.contour(
            self.lonmesh, self.latmesh, self.data[contour_entity],
            height_range, colors="white")
        self.bm.ax.clabel(heights_c, fmt="%i")
