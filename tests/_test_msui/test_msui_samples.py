# -*- coding: utf-8 -*-
"""

    tests._test_msui.test_msui_samples
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module loads the msui samples of docs/samples, which the documentation
    shows, with the code of msui.

    This file is part of MSS.

    :copyright: Copyright 2026 by Reimar Bauer.
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
import ast
import importlib
import json
import pathlib

import mock
import pytest
from fastkml import KML

from mslib.msui.aircraft import SimpleAircraft
from mslib.msui.flighttrack import load_from_xml_data
from mslib.msui.kmloverlay_dockwidget import KMLPatch
from mslib.msui.satellite_dockwidget import read_nasa_satellite_prediction
from mslib.msui.utils.config import MSUIDefaultConfig, config_loader, read_config_file

SAMPLES = pathlib.Path(__file__).parent.parent.parent / "docs" / "samples"
MSUI_SAMPLES = SAMPLES / "config" / "msui"
SETTINGS_SAMPLES = ["msui_settings.json.sample", "mssautoplot.json.sample", "autoplot_dockwidget.json.sample"]
SNIPPETS = ["caching.sample", "proxies.sample"]


def _assert_msui_uses_all_values(path):
    """msui ignores a value of the settings file whose type or structure differs from the default."""
    sample = json.loads(path.read_text(encoding="utf-8"))
    read_config_file(path)
    unknown = [key for key in sample if not hasattr(MSUIDefaultConfig, key)]
    assert unknown == []
    for key, value in sample.items():
        if key in ("import_plugins", "export_plugins"):
            # msui adds the file picker to a plugin given without it
            value = {name: plugin + ["default"] if len(plugin) == 3 else plugin for name, plugin in value.items()}
        if value == [] and key.startswith("automated_plotting_"):
            # the autoplot dock writes an empty list for a view without plots
            continue
        assert config_loader(dataset=key) == value, key


@pytest.mark.parametrize("sample", SETTINGS_SAMPLES)
def test_settings_sample(sample):
    _assert_msui_uses_all_values(MSUI_SAMPLES / sample)


@pytest.mark.parametrize("snippet", SNIPPETS)
def test_settings_snippet(snippet, tmp_path):
    text = (MSUI_SAMPLES / "snippets" / snippet).read_text(encoding="utf-8").strip().rstrip(",")
    path = tmp_path / "msui_settings.json"
    path.write_text("{" + text + "}", encoding="utf-8")
    _assert_msui_uses_all_values(path)


def test_settings_sample_has_the_login_of_its_mscolab_server():
    sample = json.loads((MSUI_SAMPLES / "msui_settings.json.sample").read_text(encoding="utf-8"))
    for url in sample["default_MSCOLAB"]:
        assert url in sample["MSS_auth"]


def test_ftml_sample():
    waypoints = load_from_xml_data((SAMPLES / "flight-tracks" / "example.ftml").read_text(encoding="utf-8"))
    assert len(waypoints) == 5


def test_performance_sample():
    aircraft = SimpleAircraft(json.loads((MSUI_SAMPLES / "performance_simple.json.sample").read_text()))
    assert aircraft.name == "DUMMY"
    assert aircraft.empty_weight == 56000


def test_satellite_predictor_sample():
    assert len(read_nasa_satellite_prediction(str(SAMPLES / "satellite_tracks" / "satellite_predictor.txt"))) > 0


@pytest.mark.parametrize("kml", sorted(path.name for path in (SAMPLES / "kml").glob("*.kml")))
def test_kml_sample(kml):
    mapcanvas = mock.Mock(side_effect=lambda x, y: (x, y))
    mapcanvas.plot = mock.Mock(return_value=[mock.Mock()])
    mapcanvas.gcpoints_path = mock.Mock(side_effect=lambda x, y: (x, y))
    patch = KMLPatch(mapcanvas, KML.parse(str(SAMPLES / "kml" / kml), strict=False))
    assert len(patch.patches) > 0


def test_navaid_plugin_sample():
    """The plugin needs the addons geomag, geopy and geographiclib, so only its imports of mslib are checked."""
    tree = ast.parse((SAMPLES / "plugins" / "navaid.py").read_text(encoding="utf-8"))
    imports = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module.startswith("mslib")]
    assert imports != []
    for node in imports:
        module = importlib.import_module(node.module)
        for alias in node.names:
            assert hasattr(module, alias.name), f"{node.module}.{alias.name}"
    assert "save_to_navaid" in {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
