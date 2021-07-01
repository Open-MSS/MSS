"""
    This file is part of mss.

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
        fill_range = np.arange(-93, 28, 2)
        fill_entity = "air_temperature"
        contour_entity = "geopotential_height"

        # main plot
        cmap = mpl.cm.plasma

        cf = self.bm.contourf(
            self.lonmesh, self.latmesh, self.data[fill_entity],
            fill_range, cmap=cmap, extend="both")
        self.add_colorbar(cf, fill_entity)

        # contour
        heights_c = self.bm.contour(
            self.lonmesh, self.latmesh, self.data[contour_entity], colors="white")
        self.bm.ax.clabel(heights_c, fmt="%i")
