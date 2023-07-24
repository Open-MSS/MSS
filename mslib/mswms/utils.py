# -*- coding: utf-8 -*-
"""

    mslib.mslib.utils
    ~~~~~~~~~~~~~~~~~

    This module provides functions for the wms server

    This file is part of MSS.

    :copyright: Copyright 2016 Joern Ungermann
    :copyright: Copyright 2016-2023 by the MSS team, see AUTHORS.
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

import matplotlib


def make_cbar_labels_readable(fig, axs):
    """
    Adjust font size of the colorbar labels and put a white background behind them
    such that they are readable in front of any background.
    """
    fontsize = fig.bbox.height * 0.024
    for x in axs.yaxis.majorTicks:
        x.label1.set_path_effects([matplotlib.patheffects.withStroke(linewidth=4, foreground='w')])
        x.label1.set_fontsize(fontsize)
