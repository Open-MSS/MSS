# -*- coding: utf-8 -*-
"""

    tests._test_mswms.test_mswms_samples
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module loads the mswms samples of docs/samples, which the documentation
    shows, with the server code.

    This file is part of MSS.

    :copyright: Copyright 2026 by the MSS team, see AUTHORS.
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
import importlib.util
import pathlib
import re

import pytest

import mslib.mswms.wms
from mslib.mswms.mpl_hsec import MPLBasemapHorizontalSectionStyle
from mslib.mswms.seed import DataFiles
from tests.constants import MSWMS_DATA_DIR

MSWMS_SAMPLES = pathlib.Path(__file__).parent.parent.parent / "docs" / "samples" / "config" / "mswms"


def _load_sample(path, tmp_path, name):
    """Loads a sample as module, with its data paths pointing to the demodata of the tests."""
    text = re.sub(r'r?"/path/to/data/mss[^"]*"', repr(str(MSWMS_DATA_DIR)), path.read_text(encoding="utf-8"))
    module_path = tmp_path / f"{name}.py"
    module_path.write_text(text, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("sample", ["mswms_settings.py.sample", "mswms_settings.py.demodata",
                                    "mswms_settings.py.chem_plots"])
def test_settings_sample_registers_its_layers(sample, tmp_path, monkeypatch):
    # the chem_plots sample imports mss_chem_plots, which lives next to it
    monkeypatch.syspath_prepend(str(MSWMS_SAMPLES))
    settings = _load_sample(MSWMS_SAMPLES / sample, tmp_path, "sample_mswms_settings")
    monkeypatch.setattr(mslib.mswms.wms, "mswms_settings", settings)
    server = mslib.mswms.wms.WMSServer()
    try:
        assert any(server.hsec_layer_registry.values())
        assert any(server.vsec_layer_registry.values())
        assert any(server.lsec_layer_registry.values())
    finally:
        server.close_datasets()


def test_chem_plots_sample(monkeypatch):
    monkeypatch.syspath_prepend(str(MSWMS_SAMPLES))
    import mss_chem_plots
    layer = mss_chem_plots.VS_MSSChemStyle_PL_NH3_nfrac
    # the vertical layering, the last two characters of the name, decides how the plot gets its air pressure
    assert layer.name == "VS_mole_fraction_of_ammonia_in_air_pl"
    assert mss_chem_plots.HS_MSSChemStyle_ML_NO2_mfrac.name == "HS_mass_fraction_of_nitrogen_dioxide_in_air_ml"


def test_plotting_layer_sample(tmp_path):
    module = _load_sample(MSWMS_SAMPLES / "mswms_plotting_layer.py.sample", tmp_path, "sample_plotting_layer")
    assert issubclass(module.HS_BrightnessTemperature, MPLBasemapHorizontalSectionStyle)


def test_demodata_sample_is_the_seed_config(tmp_path):
    """The sample shows the mswms_settings.py that "mswms --seed" writes."""
    DataFiles(mswms_data_dir="/path/to/data/mss/testdata",
              mswms_server_config_dir=tmp_path).create_server_config(detailed_information=True)
    seed_config = (tmp_path / "mswms_settings.py").read_text(encoding="utf-8")
    assert seed_config == (MSWMS_SAMPLES / "mswms_settings.py.demodata").read_text(encoding="utf-8")
