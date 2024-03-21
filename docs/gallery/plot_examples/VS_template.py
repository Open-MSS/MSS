"""
    This file is part of MSS.

    :copyright: Copyright 2021-2024 by the MSS team, see AUTHORS.
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
import mslib.mswms.mpl_vsec_styles


class VS_Template(mslib.mswms.mpl_vsec_styles.AbstractVerticalSectionStyle):
    name = "VSTemplate"  # Pick a proper name starting with "VS"
    title = "Air Temperature"
    abstract = "Air Temperature (degC)"

    required_datafields = [
        # level type, CF standard name, unit
        ("pl", "air_pressure", "Pa"),  # air_pressure must be given for VS plots
        ("pl", "air_temperature", "degC"),
    ]

    def _plot_style(self):
        fill_range = np.arange(-93, 28, 2)
        fill_entity = "air_temperature"
        contour_entity = "air_temperature"

        # main plot
        cmap = mpl.cm.plasma

        cf = self.ax.contourf(
            self.horizontal_coordinate, self.data["air_pressure"], self.data[fill_entity],
            fill_range, cmap=cmap, extend="both")
        self.add_colorbar(cf, fill_entity)

        # contour
        temps_c = self.ax.contour(
            self.horizontal_coordinate, self.data["air_pressure"], self.data[contour_entity], colors="w")
        self.ax.clabel(temps_c, fmt="%i")

        # finalise the plot
        self._latlon_logp_setup()
