# -*- coding: utf-8 -*-
"""

    mslib.mswms._tests.test_mss_plot_driver
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests mslib.mswms.mss_plot_driver

    This file is part of mss.

    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2017 Reimar Bauer, Joern Ungermann
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

from datetime import datetime
import pytest
from PIL import Image
from xml.etree import ElementTree
import io
from mslib.mswms.mss_plot_driver import VerticalSectionDriver, HorizontalSectionDriver, LinearSectionDriver
import mss_wms_settings
import mslib.mswms.mpl_vsec_styles as mpl_vsec_styles
import mslib.mswms.mpl_hsec_styles as mpl_hsec_styles
import mslib.mswms.mpl_lsec_styles as mpl_lsec_styles


def is_image_transparent(img):
    with Image.open(io.BytesIO(img)) as image:
        if image.mode == "P":
            transparent = image.info.get("transparency", -1)
            for _, index in image.getcolors():
                if index == transparent:
                    return True
        elif image.mode == "RGBA":
            return image.getextrema()[3][0] < 255
        return False


class Test_VSec(object):
    def setup(self):
        p1 = [45.00, 8.]
        p2 = [50.00, 12.]
        p3 = [51.00, 15.]
        p4 = [48.00, 11.]
        data = mss_wms_settings.data["ecmwf_EUR_LL015"]
        data.setup()

        self.path = [p1, p2, p3, p4]
        self.bbox = [3, 500, 3, 10]
        self.init_time = datetime(2012, 10, 17, 12)
        self.valid_time = datetime(2012, 10, 17, 12)
        self.vsec = VerticalSectionDriver(data)

    def plot(self, plot_object, style="default", noframe=False, transparent=False, draw_verticals=False,
             return_format="image/png"):
        self.vsec.set_plot_parameters(plot_object=plot_object,
                                      bbox=self.bbox,
                                      vsec_path=self.path,
                                      vsec_numpoints=101,
                                      vsec_path_connection='greatcircle',
                                      init_time=self.init_time,
                                      valid_time=self.valid_time,
                                      style=style,
                                      noframe=noframe,
                                      draw_verticals=draw_verticals,
                                      transparent=transparent,
                                      return_format=return_format,
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

    def test_VS_verticals(self):
        img = self.plot(mpl_vsec_styles.VS_TemperatureStyle_01(driver=self.vsec), draw_verticals=True)
        assert img is not None
        assert not is_image_transparent(img)

    def test_VS_transparent(self):
        img = self.plot(mpl_vsec_styles.VS_TemperatureStyle_01(driver=self.vsec), transparent=True)
        assert img is not None
        assert is_image_transparent(img)

    def test_xml(self):
        img = self.plot(mpl_vsec_styles.VS_TemperatureStyle_01(driver=self.vsec), return_format="text/xml")
        assert img is not None
        ElementTree.fromstring(img)

    def test_VS_TemperatureStyle_01(self):
        img = self.plot(mpl_vsec_styles.VS_TemperatureStyle_01(driver=self.vsec))
        assert img is not None
        noframe = self.plot(mpl_vsec_styles.VS_TemperatureStyle_01(driver=self.vsec), noframe=True)
        assert noframe != img

    def test_VS_GenericStyle(self):
        img = self.plot(mpl_vsec_styles.VS_GenericStyle_PL_mole_fraction_of_ozone_in_air(driver=self.vsec))
        assert img is not None
        noframe = self.plot(mpl_vsec_styles.VS_GenericStyle_PL_mole_fraction_of_ozone_in_air(driver=self.vsec),
                            noframe=True)
        assert noframe != img

        img = self.plot(mpl_vsec_styles.VS_GenericStyle_TL_mole_fraction_of_ozone_in_air(driver=self.vsec))
        assert img is not None
        noframe = self.plot(mpl_vsec_styles.VS_GenericStyle_TL_mole_fraction_of_ozone_in_air(driver=self.vsec),
                            noframe=True)
        assert noframe != img

    def test_VS_CloudsStyle_01(self):
        img = self.plot(mpl_vsec_styles.VS_CloudsStyle_01(driver=self.vsec))
        assert img is not None
        noframe = self.plot(mpl_vsec_styles.VS_CloudsStyle_01(driver=self.vsec), noframe=True)
        assert noframe != img

    def test_VS_CloudsWindStyle_01(self):
        img = self.plot(mpl_vsec_styles.VS_CloudsWindStyle_01(driver=self.vsec))
        assert img is not None
        noframe = self.plot(mpl_vsec_styles.VS_CloudsWindStyle_01(driver=self.vsec), noframe=True)
        assert noframe != img

    def test_VS_RelativeHumdityStyle_01(self):
        img = self.plot(mpl_vsec_styles.VS_RelativeHumdityStyle_01(driver=self.vsec))
        assert img is not None
        noframe = self.plot(mpl_vsec_styles.VS_RelativeHumdityStyle_01(driver=self.vsec), noframe=True)
        assert noframe != img

    def test_VS_SpecificHumdityStyle_01(self):
        img = self.plot(mpl_vsec_styles.VS_SpecificHumdityStyle_01(driver=self.vsec))
        assert img is not None
        noframe = self.plot(mpl_vsec_styles.VS_SpecificHumdityStyle_01(driver=self.vsec), noframe=True)
        assert noframe != img

    def test_VS_VerticalVelocityStyle_01(self):
        img = self.plot(mpl_vsec_styles.VS_VerticalVelocityStyle_01(driver=self.vsec))
        assert img is not None

    def test_VS_HorizontalVelocityStyle_01(self):
        img = self.plot(mpl_vsec_styles.VS_HorizontalVelocityStyle_01(driver=self.vsec))
        assert img is not None
        noframe = self.plot(mpl_vsec_styles.VS_HorizontalVelocityStyle_01(driver=self.vsec), noframe=True)
        assert noframe != img

    def test_VS_PotentialVorticityStyle_01(self):
        img = self.plot(mpl_vsec_styles.VS_PotentialVorticityStyle_01(driver=self.vsec))
        assert img is not None
        noframe = self.plot(mpl_vsec_styles.VS_PotentialVorticityStyle_01(driver=self.vsec), noframe=True)
        assert noframe != img

    def test_VS_ProbabilityOfWCBStyle_01(self):
        img = self.plot(mpl_vsec_styles.VS_ProbabilityOfWCBStyle_01(driver=self.vsec))
        assert img is not None
        noframe = self.plot(mpl_vsec_styles.VS_ProbabilityOfWCBStyle_01(driver=self.vsec), noframe=True)
        assert noframe != img

    def test_VS_LagrantoTrajStyle_PL_01(self):
        pytest.skip("data not available")
        img = self.plot(mpl_vsec_styles.VS_LagrantoTrajStyle_PL_01(driver=self.vsec))
        assert img is not None
        noframe = self.plot(mpl_vsec_styles.VS_LagrantoTrajStyle_PL_01(driver=self.vsec), noframe=True)
        assert noframe != img

    def test_VS_EMACEyja_Style_01(self):
        img = self.plot(mpl_vsec_styles.VS_EMACEyja_Style_01(driver=self.vsec))
        assert img is not None
        noframe = self.plot(mpl_vsec_styles.VS_EMACEyja_Style_01(driver=self.vsec), noframe=True)
        assert noframe != img


class Test_LSec(object):
    def setup(self):
        p1 = [45.00, 8., 25000]
        p2 = [50.00, 12., 25000]
        p3 = [51.00, 15., 25000]
        p4 = [48.00, 11., 25000]
        data = mss_wms_settings.data["ecmwf_EUR_LL015"]
        data.setup()

        self.path = [p1, p2, p3, p4]
        self.bbox = [500]
        self.init_time = datetime(2012, 10, 17, 12)
        self.valid_time = datetime(2012, 10, 17, 12)
        self.lsec = LinearSectionDriver(data)

    def plot(self, plot_object):
        self.lsec.set_plot_parameters(plot_object=plot_object,
                                      bbox=self.bbox,
                                      lsec_path=self.path,
                                      lsec_numpoints=self.bbox[0],
                                      init_time=self.init_time,
                                      valid_time=self.valid_time)
        return self.lsec.plot()

    def test_repeated_locations(self):
        p1 = [45.00, 8., 25000]
        p2 = [50.00, 12., 25000]
        self.path = [p1, p1]
        img = self.plot(mpl_lsec_styles.LS_DefaultStyle(driver=self.lsec))
        assert img is not None
        self.path = [p1, p1, p2]
        img = self.plot(mpl_lsec_styles.LS_DefaultStyle(driver=self.lsec))
        assert img is not None
        self.path = [p1, p2, p2]
        img = self.plot(mpl_lsec_styles.LS_DefaultStyle(driver=self.lsec))
        assert img is not None

    def test_LS_DefaultStyle(self):
        for variable in ["air_temperature", "specific_humidity",
                         "cloud_area_fraction_in_atmosphere_layer", "specific_cloud_ice_water_content",
                         "specific_cloud_liquid_water_content", "ertel_potential_vorticity"]:
            img = self.plot(mpl_lsec_styles.LS_DefaultStyle(driver=self.lsec, variable=variable))
            assert img is not None

    def test_LS_DefaultStyle_PL(self):
        img = self.plot(mpl_lsec_styles.LS_DefaultStyle(driver=self.lsec, variable="air_potential_temperature",
                                                        filetype="pl"))
        assert img is not None

    def test_LS_RelativeHumdityStyle_01(self):
        img = self.plot(mpl_lsec_styles.LS_RelativeHumdityStyle_01(driver=self.lsec))
        assert img is not None

    def test_LS_HorizontalVelocityStyle_01(self):
        img = self.plot(mpl_lsec_styles.LS_HorizontalVelocityStyle_01(driver=self.lsec))
        assert img is not None

    def test_LS_VerticalVelocityStyle_01(self):
        img = self.plot(mpl_lsec_styles.LS_VerticalVelocityStyle_01(driver=self.lsec))
        assert img is not None


class Test_HSec(object):
    def setup(self):
        data = mss_wms_settings.data["ecmwf_EUR_LL015"]
        data.setup()

        self.bbox = [-22.5, 27.5, 55, 62.5]

        self.init_time = datetime(2012, 10, 17, 12)
        self.valid_time = datetime(2012, 10, 17, 12)
        self.hsec = HorizontalSectionDriver(data)

    def plot(self, plot_object, style="default", level=None, crs="EPSG:4326", bbox=None, noframe=False,
             transparent=False):
        if bbox is None:
            bbox = self.bbox
        self.hsec.set_plot_parameters(plot_object=plot_object, bbox=bbox, level=level, crs=crs,
                                      init_time=self.init_time, valid_time=self.valid_time, style=style,
                                      noframe=noframe, show=False, transparent=transparent)
        return self.hsec.plot()

    @pytest.mark.parametrize("crs", [
        "EPSG:4326",
        "EPSG:77890010", "EPSG:77790010",
        "MSS:stere,20,40,40", "MSS:lcc,20,0,40,20", "MSS:cass,20,40", "MSS:merc,40"])
    def test_degree_crs_codes(self, crs):
        img = self.plot(mpl_hsec_styles.HS_MSLPStyle_01(driver=self.hsec), crs=crs)
        assert img is not None

    @pytest.mark.parametrize("crs", ["EPSG:3031", "EPSG:3857", "EPSG:3413", "EPSG:3995"])
    def test_meter_crs_codes(self, crs):
        bbox_meter = [-1e7, -1e7, 1e7, 1e7]
        img = self.plot(mpl_hsec_styles.HS_MSLPStyle_01(driver=self.hsec), crs=crs, bbox=bbox_meter)
        assert img is not None

    @pytest.mark.parametrize("crs", ["EPSG:12345678", "FNORD", "MSS:lagranto"])
    def test_invalid_crs_codes(self, crs):
        with pytest.raises(ValueError):
            self.plot(mpl_hsec_styles.HS_MSLPStyle_01(driver=self.hsec), crs=crs)

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
            noframe = self.plot(mpl_hsec_styles.HS_CloudsStyle_01(driver=self.hsec), style=style, noframe=True)
            assert noframe != img
            assert not is_image_transparent(img)

    def test_HS_transparent(self):
        img = self.plot(mpl_hsec_styles.HS_MSLPStyle_01(driver=self.hsec), transparent=True)
        assert img is not None
        assert is_image_transparent(img)

    def test_HS_MSLPStyle_01(self):
        img = self.plot(mpl_hsec_styles.HS_MSLPStyle_01(driver=self.hsec))
        assert img is not None
        noframe = self.plot(mpl_hsec_styles.HS_MSLPStyle_01(driver=self.hsec), noframe=True)
        assert noframe != img

    def test_HS_SEAStyle_01(self):
        img = self.plot(mpl_hsec_styles.HS_SEAStyle_01(driver=self.hsec))
        assert img is not None
        noframe = self.plot(mpl_hsec_styles.HS_SEAStyle_01(driver=self.hsec), noframe=True)
        assert noframe != img

    @pytest.mark.parametrize("style", ["PCOL", "CONT"])
    def test_HS_SeaIceStyle_01(self, style):
        img = self.plot(mpl_hsec_styles.HS_SeaIceStyle_01(driver=self.hsec), style=style)
        assert img is not None
        noframe = self.plot(mpl_hsec_styles.HS_SeaIceStyle_01(driver=self.hsec), style=style, noframe=True)
        assert noframe != img

    def test_HS_TemperatureStyle_ML_01(self):
        img = self.plot(mpl_hsec_styles.HS_TemperatureStyle_ML_01(driver=self.hsec), level=10)
        assert img is not None
        noframe = self.plot(mpl_hsec_styles.HS_TemperatureStyle_ML_01(driver=self.hsec), level=10, noframe=True)
        assert noframe != img

    def test_HS_TemperatureStyle_PL_01(self):
        img = self.plot(mpl_hsec_styles.HS_TemperatureStyle_PL_01(driver=self.hsec), level=800)
        assert img is not None
        noframe = self.plot(mpl_hsec_styles.HS_TemperatureStyle_PL_01(driver=self.hsec), level=800, noframe=True)
        assert noframe != img

    def test_HS_GeopotentialWindStyle_PL(self):
        img = self.plot(mpl_hsec_styles.HS_GeopotentialWindStyle_PL(driver=self.hsec), level=300)
        assert img is not None
        noframe = self.plot(mpl_hsec_styles.HS_GeopotentialWindStyle_PL(driver=self.hsec), level=300, noframe=True)
        assert noframe != img

    @pytest.mark.parametrize("style", ["default", "nonlinear", "auto", "log", "autolog"])
    def test_HS_GenericStyle_styles(self, style):
        img = self.plot(
            mpl_hsec_styles.HS_GenericStyle_PL_mole_fraction_of_ozone_in_air(driver=self.hsec),
            level=300, style=style)
        assert img is not None
        noframe = self.plot(mpl_hsec_styles.HS_GenericStyle_PL_mole_fraction_of_ozone_in_air(driver=self.hsec),
                            level=300, style=style, noframe=True)
        assert noframe != img

    def test_HS_GenericStyle_other(self):
        img = self.plot(mpl_hsec_styles.HS_GenericStyle_TL_mole_fraction_of_ozone_in_air(driver=self.hsec), level=300)
        assert img is not None
        noframe = self.plot(mpl_hsec_styles.HS_GenericStyle_TL_mole_fraction_of_ozone_in_air(driver=self.hsec),
                            level=300, noframe=True)
        assert noframe != img

        img = self.plot(
            mpl_hsec_styles.HS_GenericStyle_PL_ertel_potential_vorticity(driver=self.hsec),
            style="ertel_potential_vorticity", level=300)
        assert img is not None
        noframe = self.plot(mpl_hsec_styles.HS_GenericStyle_PL_ertel_potential_vorticity(driver=self.hsec),
                            level=300, style="ertel_potential_vorticity", noframe=True)
        assert noframe != img

        img = self.plot(
            mpl_hsec_styles.HS_GenericStyle_PL_equivalent_latitude(driver=self.hsec),
            style="equivalent_latitude", level=300)
        assert img is not None
        noframe = self.plot(mpl_hsec_styles.HS_GenericStyle_PL_equivalent_latitude(driver=self.hsec),
                            level=300, style="equivalent_latitude", noframe=True)
        assert noframe != img

    def test_HS_RelativeHumidityStyle_PL_01(self):
        img = self.plot(mpl_hsec_styles.HS_RelativeHumidityStyle_PL_01(driver=self.hsec), level=300)
        assert img is not None
        noframe = self.plot(mpl_hsec_styles.HS_RelativeHumidityStyle_PL_01(driver=self.hsec), level=300, noframe=True)
        assert noframe != img

    def test_HS_EQPTStyle_PL_01(self):
        img = self.plot(mpl_hsec_styles.HS_EQPTStyle_PL_01(driver=self.hsec), level=300)
        assert img is not None
        noframe = self.plot(mpl_hsec_styles.HS_EQPTStyle_PL_01(driver=self.hsec), level=300, noframe=True)
        assert noframe != img

    def test_HS_WStyle_PL_01(self):
        img = self.plot(mpl_hsec_styles.HS_WStyle_PL_01(driver=self.hsec), level=300)
        assert img is not None
        noframe = self.plot(mpl_hsec_styles.HS_WStyle_PL_01(driver=self.hsec), level=300, noframe=True)
        assert noframe != img

    def test_HS_DivStyle_PL_01(self):
        img = self.plot(mpl_hsec_styles.HS_DivStyle_PL_01(driver=self.hsec), level=300)
        assert img is not None
        noframe = self.plot(mpl_hsec_styles.HS_DivStyle_PL_01(driver=self.hsec), level=300, noframe=True)
        assert noframe != img

    def test_HS_EMAC_TracerStyle_ML_01(self):
        img = self.plot(mpl_hsec_styles.HS_EMAC_TracerStyle_ML_01(driver=self.hsec), level=10)
        assert img is not None
        noframe = self.plot(mpl_hsec_styles.HS_EMAC_TracerStyle_ML_01(driver=self.hsec), level=10, noframe=True)
        assert noframe != img

    def test_HS_EMAC_TracerStyle_SFC_01(self):
        img = self.plot(mpl_hsec_styles.HS_EMAC_TracerStyle_SFC_01(driver=self.hsec))
        assert img is not None
        noframe = self.plot(mpl_hsec_styles.HS_EMAC_TracerStyle_SFC_01(driver=self.hsec), noframe=True)
        assert noframe != img

    def test_HS_PVTropoStyle_PV_01(self):
        # test fractional levels and non-existing levels
        for style in ["PRES", "PT", "GEOP"]:
            img = self.plot(mpl_hsec_styles.HS_PVTropoStyle_PV_01(driver=self.hsec), level=2.5, style=style)
            assert img is not None
        noframe = self.plot(mpl_hsec_styles.HS_PVTropoStyle_PV_01(driver=self.hsec), level=2.5, style=style,
                            noframe=True)
        assert noframe != img
        with pytest.raises(ValueError):
            self.plot(mpl_hsec_styles.HS_PVTropoStyle_PV_01(driver=self.hsec), level=2.75)

    def test_HS_VIProbWCB_Style_01(self):
        img = self.plot(mpl_hsec_styles.HS_VIProbWCB_Style_01(driver=self.hsec))
        assert img is not None
        noframe = self.plot(mpl_hsec_styles.HS_VIProbWCB_Style_01(driver=self.hsec), noframe=True)
        assert noframe != img

    def test_HS_LagrantoTrajStyle_PL_01(self):
        img = self.plot(mpl_hsec_styles.HS_LagrantoTrajStyle_PL_01(driver=self.hsec), level=300)
        assert img is not None
        noframe = self.plot(mpl_hsec_styles.HS_LagrantoTrajStyle_PL_01(driver=self.hsec), level=300, noframe=True)
        assert noframe != img

    def test_HS_BLH_MSLP_Style_01(self):
        img = self.plot(mpl_hsec_styles.HS_BLH_MSLP_Style_01(driver=self.hsec))
        assert img is not None
        noframe = self.plot(mpl_hsec_styles.HS_BLH_MSLP_Style_01(driver=self.hsec), noframe=True)
        assert noframe != img

    def test_HS_Meteosat_BT108_01(self):
        img = self.plot(mpl_hsec_styles.HS_Meteosat_BT108_01(driver=self.hsec))
        assert img is not None
        noframe = self.plot(mpl_hsec_styles.HS_Meteosat_BT108_01(driver=self.hsec), noframe=True)
        assert noframe != img
