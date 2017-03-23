# -*- coding: utf-8 -*-
"""

    mslib.mswms._tests.test_mss_plot_driver
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests mslib.mswms.mss_plot_driver

    This file is part of mss.

    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2017 Reimar Bauer, Joern Ungermann
    :copyright: Copyright 2016-2017 by the mss team, see AUTHORS.
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

from datetime import datetime
import pytest
from mslib.mswms.mss_plot_driver import VerticalSectionDriver, HorizontalSectionDriver
import mss_wms_settings
import mslib.mswms.mpl_vsec_styles as mpl_vsec_styles
import mslib.mswms.mpl_hsec_styles as mpl_hsec_styles


def test_vsec_clouds_path():
    """
    TEST: Create a vertical section of the CLOUDS style.
    """
    # Define cross-section path (great circle interpolation between two points).
    p1 = [45.00, 8.]
    p2 = [50.00, 12.]
    p3 = [51.00, 15.]
    p4 = [48.00, 11.]

    bbox = [3, 500, 3, 10]
    nwpaccess = mss_wms_settings.nwpaccess["ecmwf_EUR_LL015"]

    init_time = datetime(2012, 10, 17, 12)
    valid_time = datetime(2012, 10, 17, 12)

    # plot_object = mpl_vsec_styles.VSCloudsStyle01(p_top=20000.)
    vsec = VerticalSectionDriver(nwpaccess)
    plot_object = mpl_vsec_styles.VS_TemperatureStyle_01(driver=vsec)

    vsec.set_plot_parameters(plot_object=plot_object,
                             bbox=bbox,
                             vsec_path=[p1, p2, p3, p4],
                             vsec_numpoints=101,
                             vsec_path_connection='greatcircle',
                             init_time=init_time,
                             valid_time=valid_time,
                             noframe=False,
                             show=False)
    img = vsec.plot()
    assert img is not None


def test_vsec_generic():
    """
    TEST: Create a vertical section of the CLOUDS style.
    """
    # Define cross-section path (great circle interpolation between two points).
    p1 = [45.00, 8.]
    p2 = [50.00, 12.]
    p3 = [51.00, 15.]
    p4 = [48.00, 11.]

    bbox = [3, 500, 3, 10]
    nwpaccess = mss_wms_settings.nwpaccess["ecmwf_EUR_LL015"]

    init_time = datetime(2012, 10, 17, 12)
    valid_time = datetime(2012, 10, 17, 12)

    # plot_object = mpl_vsec_styles.VSCloudsStyle01(p_top=20000.)
    vsec = VerticalSectionDriver(nwpaccess)
    plot_object = mpl_vsec_styles.VS_GenericStyle_PL_ertel_potential_vorticity(driver=vsec)

    vsec.set_plot_parameters(plot_object=plot_object,
                             bbox=bbox,
                             vsec_path=[p1, p2, p3, p4],
                             vsec_numpoints=101,
                             vsec_path_connection='greatcircle',
                             init_time=init_time,
                             style="default",
                             valid_time=valid_time,
                             noframe=False,
                             show=False)
    img = vsec.plot()
    assert img is not None

    plot_object = mpl_vsec_styles.VS_GenericStyle_TL_ertel_potential_vorticity(driver=vsec)

    vsec.set_plot_parameters(plot_object=plot_object,
                             bbox=bbox,
                             vsec_path=[p1, p2, p3, p4],
                             vsec_numpoints=101,
                             vsec_path_connection='greatcircle',
                             init_time=init_time,
                             style="default",
                             valid_time=valid_time,
                             noframe=False,
                             show=False)
    img = vsec.plot()
    assert img is not None


def test_hsec_clouds_total():
    """
    TEST: Create a horizontal section of the CLOUDS style.
    """
    pytest.skip("Test data not available")
    # Define a bounding box for the map.
    bbox = [-22.5, 27.5, 55, 62.5]

    nwpaccess = mss_wms_settings.nwpaccess["ecmwf_EUR_LL015"]
    init_time = datetime(2012, 10, 17, 12)
    valid_time = datetime(2012, 10, 17, 12)

    plot_object = mpl_hsec_styles.HS_CloudsStyle_01()

    hsec = HorizontalSectionDriver(nwpaccess)
    hsec.set_plot_parameters(plot_object=plot_object,
                             bbox=bbox,
                             epsg=77790010,
                             init_time=init_time,
                             valid_time=valid_time,
                             noframe=False,
                             show=False)
    img = hsec.plot()
    assert img is not None


def test_hsec_temp():
    """
    TEST: Create a horizontal section of the TEMPERATURE style.
    """
    # Define a bounding box for the map.
    #    bbox = [0,30,30,60]
    bbox = [-22.5, 27.5, 55, 62.5]

    nwpaccess = mss_wms_settings.nwpaccess["ecmwf_EUR_LL015"]

    init_time = datetime(2012, 10, 17, 12)
    valid_time = datetime(2012, 10, 17, 12)

    plot_object = mpl_hsec_styles.HS_TemperatureStyle_PL_01()
    level = 925

    hsec = HorizontalSectionDriver(nwpaccess)
    hsec.set_plot_parameters(plot_object=plot_object,
                             bbox=bbox,
                             level=level,
                             epsg=77790010,
                             init_time=init_time,
                             valid_time=valid_time,
                             noframe=True,
                             show=False)
    img = hsec.plot()
    assert img is not None


def test_hsec_geopwind():
    """
    TEST: Create a horizontal section.
    """
    # Define a bounding box for the map.
    bbox = [-22.5, 27.5, 55, 62.5]

    nwpaccess = mss_wms_settings.nwpaccess["ecmwf_EUR_LL015"]

    init_time = datetime(2012, 10, 17, 12)
    valid_time = datetime(2012, 10, 17, 12)

    plot_object = mpl_hsec_styles.HS_GeopotentialWindStyle_PL()
    level = 300

    hsec = HorizontalSectionDriver(nwpaccess)
    hsec.set_plot_parameters(plot_object=plot_object,
                             bbox=bbox,
                             level=level,
                             epsg=77790010,
                             style="default",
                             init_time=init_time,
                             valid_time=valid_time,
                             noframe=True,
                             show=False)
    img = hsec.plot()
    assert img is not None

def test_hsec_generic():
    """
    TEST: Create a horizontal section.
    """
    # Define a bounding box for the map.
    bbox = [-22.5, 27.5, 55, 62.5]

    nwpaccess = mss_wms_settings.nwpaccess["ecmwf_EUR_LL015"]

    init_time = datetime(2012, 10, 17, 12)
    valid_time = datetime(2012, 10, 17, 12)

    hsec = HorizontalSectionDriver(nwpaccess)
    plot_object = mpl_hsec_styles.HS_GenericStyle_PL_ertel_potential_vorticity(driver=hsec)
    level = 300

    hsec.set_plot_parameters(plot_object=plot_object,
                             bbox=bbox,
                             level=level,
                             epsg=77790010,
                             style="default",
                             init_time=init_time,
                             valid_time=valid_time,
                             noframe=True,
                             show=False)
    img = hsec.plot()
    assert img is not None

    plot_object = mpl_hsec_styles.HS_GenericStyle_TL_ertel_potential_vorticity(driver=hsec)
    level = 300

    hsec.set_plot_parameters(plot_object=plot_object,
                             bbox=bbox,
                             level=level,
                             epsg=77790010,
                             style="default",
                             init_time=init_time,
                             valid_time=valid_time,
                             noframe=True,
                             show=False)
    img = hsec.plot()
    assert img is not None
