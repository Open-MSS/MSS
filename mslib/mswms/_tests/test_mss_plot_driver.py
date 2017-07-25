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


class Test_VSec(object):
    def setup(self):
        p1 = [45.00, 8.]
        p2 = [50.00, 12.]
        p3 = [51.00, 15.]
        p4 = [48.00, 11.]
        nwpaccess = mss_wms_settings.nwpaccess["ecmwf_EUR_LL015"]

        self.path = [p1, p2, p3, p4]
        self.bbox = [3, 500, 3, 10]
        self.init_time = datetime(2012, 10, 17, 12)
        self.valid_time = datetime(2012, 10, 17, 12)
        self.vsec = VerticalSectionDriver(nwpaccess)

    def plot(self, plot_object, style="default"):
        self.vsec.set_plot_parameters(plot_object=plot_object,
                                      bbox=self.bbox,
                                      vsec_path=self.path,
                                      vsec_numpoints=101,
                                      vsec_path_connection='greatcircle',
                                      init_time=self.init_time,
                                      valid_time=self.valid_time,
                                      style=style,
                                      noframe=False,
                                      show=False)
        return self.vsec.plot()

    def test_repeated_locations(self):
        p1 = [45.00, 8.]
        p2 = [50.00, 12.]
        self.path = [p1, p1]
        img = self.plot(mpl_vsec_styles.VS_TemperatureStyle_01(driver=self.vsec))
        assert img is not None
        self.path = [p1, p1, p2]
        img = self.plot(mpl_vsec_styles.VS_TemperatureStyle_01(driver=self.vsec))
        assert img is not None
        self.path = [p1, p2, p2]
        img = self.plot(mpl_vsec_styles.VS_TemperatureStyle_01(driver=self.vsec))
        assert img is not None

    def test_VS_TemperatureStyle_01(self):
        img = self.plot(mpl_vsec_styles.VS_TemperatureStyle_01(driver=self.vsec))
        assert img is not None

    def test_VS_GenericStyle(self):
        img = self.plot(mpl_vsec_styles.VS_GenericStyle_PL_mole_fraction_of_ozone_in_air(driver=self.vsec))
        assert img is not None

        img = self.plot(mpl_vsec_styles.VS_GenericStyle_TL_mole_fraction_of_ozone_in_air(driver=self.vsec))
        assert img is not None

    def test_VS_MSSChemStyle(self):
        for style in mpl_vsec_styles.VS_MSSChemStyle_PL_O3_mfrac.styles:
            img = self.plot(mpl_vsec_styles.VS_MSSChemStyle_PL_O3_mfrac(driver=self.vsec), style=style[0])
        assert img is not None

    def test_VS_CloudsStyle_01(self):
        img = self.plot(mpl_vsec_styles.VS_CloudsStyle_01(driver=self.vsec))
        assert img is not None

    def test_VS_CloudsWindStyle_01(self):
        img = self.plot(mpl_vsec_styles.VS_CloudsWindStyle_01(driver=self.vsec))
        assert img is not None

    def test_VS_RelativeHumdityStyle_01(self):
        img = self.plot(mpl_vsec_styles.VS_RelativeHumdityStyle_01(driver=self.vsec))
        assert img is not None

    def test_VS_SpecificHumdityStyle_01(self):
        img = self.plot(mpl_vsec_styles.VS_SpecificHumdityStyle_01(driver=self.vsec))
        assert img is not None

    def test_VS_VerticalVelocityStyle_01(self):
        img = self.plot(mpl_vsec_styles.VS_VerticalVelocityStyle_01(driver=self.vsec))
        assert img is not None

    def test_VS_HorizontalVelocityStyle_01(self):
        img = self.plot(mpl_vsec_styles.VS_HorizontalVelocityStyle_01(driver=self.vsec))
        assert img is not None

    def test_VS_PotentialVorticityStyle_01(self):
        img = self.plot(mpl_vsec_styles.VS_PotentialVorticityStyle_01(driver=self.vsec))
        assert img is not None

    def test_VS_ProbabilityOfWCBStyle_01(self):
        img = self.plot(mpl_vsec_styles.VS_ProbabilityOfWCBStyle_01(driver=self.vsec))
        assert img is not None

    def test_VS_LagrantoTrajStyle_PL_01(self):
        pytest.skip("data not available")
        img = self.plot(mpl_vsec_styles.VS_LagrantoTrajStyle_PL_01(driver=self.vsec))
        assert img is not None

    def test_VS_EMACEyja_Style_01(self):
        img = self.plot(mpl_vsec_styles.VS_EMACEyja_Style_01(driver=self.vsec))
        assert img is not None


class Test_HSec(object):
    def setup(self):
        nwpaccess = mss_wms_settings.nwpaccess["ecmwf_EUR_LL015"]

        self.bbox = [-22.5, 27.5, 55, 62.5]

        self.init_time = datetime(2012, 10, 17, 12)
        self.valid_time = datetime(2012, 10, 17, 12)
        self.hsec = HorizontalSectionDriver(nwpaccess)

    def plot(self, plot_object, style="default", level=None):
        self.hsec.set_plot_parameters(plot_object=plot_object,
                                      bbox=self.bbox,
                                      epsg=77790010,
                                      init_time=self.init_time,
                                      valid_time=self.valid_time,
                                      level=level,
                                      noframe=False,
                                      style=style,
                                      show=False)
        return self.hsec.plot()

    def test_repeated_locations(self):
        p1 = [45.00, 8.]
        p2 = [50.00, 12.]
        self.path = [p1, p1]
        img = self.plot(mpl_hsec_styles.HS_TemperatureStyle_ML_01(driver=self.hsec), level=10)
        assert img is not None
        self.path = [p1, p1, p2]
        img = self.plot(mpl_hsec_styles.HS_TemperatureStyle_ML_01(driver=self.hsec), level=10)
        assert img is not None
        self.path = [p1, p2, p2]
        img = self.plot(mpl_hsec_styles.HS_TemperatureStyle_ML_01(driver=self.hsec), level=10)
        assert img is not None

    def test_HS_CloudsStyle_01(self):
        for style in ["TOT", "HIGH", "MED", "LOW"]:
            img = self.plot(mpl_hsec_styles.HS_CloudsStyle_01(driver=self.hsec), style=style)
        assert img is not None

    def test_HS_MSLPStyle_01(self):
        img = self.plot(mpl_hsec_styles.HS_MSLPStyle_01(driver=self.hsec))
        assert img is not None

    def test_HS_SEAStyle_01(self):
        img = self.plot(mpl_hsec_styles.HS_SEAStyle_01(driver=self.hsec))
        assert img is not None

    def test_HS_SeaIceStyle_01(self):
        for style in ["PCOL", "CONT"]:
            img = self.plot(mpl_hsec_styles.HS_SeaIceStyle_01(driver=self.hsec), style=style)
        assert img is not None

    def test_HS_TemperatureStyle_ML_01(self):
        img = self.plot(mpl_hsec_styles.HS_TemperatureStyle_ML_01(driver=self.hsec), level=10)
        assert img is not None

    def test_HS_TemperatureStyle_PL_01(self):
        img = self.plot(mpl_hsec_styles.HS_TemperatureStyle_PL_01(driver=self.hsec), level=800)
        assert img is not None

    def test_HS_GeopotentialWindStyle_PL(self):
        img = self.plot(mpl_hsec_styles.HS_GeopotentialWindStyle_PL(driver=self.hsec), level=300)
        assert img is not None

    def test_HS_GenericStyle(self):
        for style in ["default", "nonlinear", "auto", "log", "autolog"]:
            img = self.plot(
                mpl_hsec_styles.HS_GenericStyle_PL_mole_fraction_of_ozone_in_air(driver=self.hsec),
                level=300, style=style)
            assert img is not None

        img = self.plot(mpl_hsec_styles.HS_GenericStyle_TL_mole_fraction_of_ozone_in_air(driver=self.hsec), level=300)
        assert img is not None

        img = self.plot(
            mpl_hsec_styles.HS_GenericStyle_PL_ertel_potential_vorticity(driver=self.hsec),
            style="ertel_potential_vorticity", level=300)
        assert img is not None

        img = self.plot(
            mpl_hsec_styles.HS_GenericStyle_PL_equivalent_latitude(driver=self.hsec),
            style="equivalent_latitude", level=300)
        assert img is not None

    def test_HS_MSSChemStyle(self):
        for style in mpl_hsec_styles.HS_MSSChemStyle_PL_O3_mfrac.styles:
            img = self.plot(mpl_hsec_styles.HS_MSSChemStyle_PL_O3_mfrac(driver=self.hsec), level=300, style=style[0])
        assert img is not None

    def test_HS_RelativeHumidityStyle_PL_01(self):
        img = self.plot(mpl_hsec_styles.HS_RelativeHumidityStyle_PL_01(driver=self.hsec), level=300)
        assert img is not None

    def test_HS_EQPTStyle_PL_01(self):
        img = self.plot(mpl_hsec_styles.HS_EQPTStyle_PL_01(driver=self.hsec), level=300)
        assert img is not None

    def test_HS_WStyle_PL_01(self):
        img = self.plot(mpl_hsec_styles.HS_WStyle_PL_01(driver=self.hsec), level=300)
        assert img is not None

    def test_HS_DivStyle_PL_01(self):
        img = self.plot(mpl_hsec_styles.HS_DivStyle_PL_01(driver=self.hsec), level=300)
        assert img is not None

    def test_HS_EMAC_TracerStyle_ML_01(self):
        img = self.plot(mpl_hsec_styles.HS_EMAC_TracerStyle_ML_01(driver=self.hsec), level=10)
        assert img is not None

    def test_HS_EMAC_TracerStyle_SFC_01(self):
        img = self.plot(mpl_hsec_styles.HS_EMAC_TracerStyle_SFC_01(driver=self.hsec))
        assert img is not None

    def test_HS_PVTropoStyle_PV_01(self):
        img = self.plot(mpl_hsec_styles.HS_PVTropoStyle_PV_01(driver=self.hsec), level=2)
        assert img is not None

    def test_HS_VIProbWCB_Style_01(self):
        img = self.plot(mpl_hsec_styles.HS_VIProbWCB_Style_01(driver=self.hsec))
        assert img is not None

    def test_HS_LagrantoTrajStyle_PL_01(self):
        img = self.plot(mpl_hsec_styles.HS_LagrantoTrajStyle_PL_01(driver=self.hsec), level=300)
        assert img is not None

    def test_HS_BLH_MSLP_Style_01(self):
        img = self.plot(mpl_hsec_styles.HS_BLH_MSLP_Style_01(driver=self.hsec))
        assert img is not None

    def test_HS_Meteosat_BT108_01(self):
        img = self.plot(mpl_hsec_styles.HS_Meteosat_BT108_01(driver=self.hsec))
        assert img is not None
