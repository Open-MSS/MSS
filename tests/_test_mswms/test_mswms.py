# -*- coding: utf-8 -*-
"""

    tests._test_mswms.test_mswms
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests mslib.mswms.mswms

    This file is part of MSS.

    :copyright: Copyright 2022 Reimar Bauer
    :copyright: Copyright 2022-2026 by the MSS team, see AUTHORS.
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

import argparse
import pytest

from mslib.mswms import mswms


def _args(**kwargs):
    defaults = dict(
        version=False,
        seed=False,
        host="127.0.0.1",
        port="8081",
        use_threadpool=False,
        debug=False,
        logfile=None,
        action=None,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _gallery_args(**kwargs):
    defaults = dict(
        version=False,
        seed=False,
        host="127.0.0.1",
        port="8081",
        use_threadpool=False,
        debug=False,
        logfile=None,
        action="gallery",
        create=False,
        clear=False,
        refresh=False,
        levels="",
        itimes="",
        vtimes="",
        show_code=False,
        url_prefix="",
        plot_types=None,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture
def mock_wms(mocker):
    """Patch wms module attributes accessed via local import inside main()."""
    mock_settings = mocker.MagicMock()
    mock_settings.__file__ = "/fake/mswms_settings.py"
    mock_server = mocker.MagicMock()
    mocker.patch("mslib.mswms.wms.mswms_settings", mock_settings)
    mocker.patch("mslib.mswms.wms.server", mock_server)
    return mock_server


@pytest.fixture
def mock_make_server(mocker):
    """Patch werkzeug make_server; returns a mock server with a default address."""
    srv = mocker.MagicMock()
    srv.server_address = ("127.0.0.1", 8081)
    return mocker.patch("werkzeug.serving.make_server", return_value=srv)


# ---------------------------------------------------------------------------
# Version flag
# ---------------------------------------------------------------------------

class TestMainVersion:
    def test_version_exits(self, mocker):
        mocker.patch("mslib.mswms.mswms.argparse.ArgumentParser.parse_args",
                     return_value=_args(version=True))
        with pytest.raises(SystemExit):
            mswms.main()

    def test_version_prints_mss_header(self, mocker, capsys):
        mocker.patch("mslib.mswms.mswms.argparse.ArgumentParser.parse_args",
                     return_value=_args(version=True))
        with pytest.raises(SystemExit):
            mswms.main()
        out = capsys.readouterr().out
        assert "Mission Support System" in out
        assert "Version" in out


# ---------------------------------------------------------------------------
# Server startup
# ---------------------------------------------------------------------------

class TestMainServerStart:
    def test_default_host_and_port_printed(self, mocker, capsys, mock_wms, mock_make_server):
        mocker.patch("mslib.mswms.mswms.argparse.ArgumentParser.parse_args",
                     return_value=_args())
        mswms.main()
        assert "http://127.0.0.1:8081" in capsys.readouterr().out

    def test_custom_host_and_port(self, mocker, capsys, mock_wms, mock_make_server):
        mock_make_server.return_value.server_address = ("0.0.0.0", 9000)
        mocker.patch("mslib.mswms.mswms.argparse.ArgumentParser.parse_args",
                     return_value=_args(host="0.0.0.0", port="9000"))
        mswms.main()
        assert "http://0.0.0.0:9000" in capsys.readouterr().out

    def test_port_zero_prints_only_actual_port(self, mocker, capsys, mock_wms, mock_make_server):
        mock_make_server.return_value.server_address = ("127.0.0.1", 54321)
        mocker.patch("mslib.mswms.mswms.argparse.ArgumentParser.parse_args",
                     return_value=_args(port="0"))
        mswms.main()
        out = capsys.readouterr().out
        assert "54321" in out
        assert "MSS WMS server" not in out

    def test_make_server_called_with_correct_args(self, mocker, mock_wms, mock_make_server):
        mock_make_server.return_value.server_address = ("localhost", 9999)
        mocker.patch("mslib.mswms.mswms.argparse.ArgumentParser.parse_args",
                     return_value=_args(host="localhost", port="9999"))
        mswms.main()
        mock_make_server.assert_called_once_with("localhost", 9999, mocker.ANY, threaded=True)


# ---------------------------------------------------------------------------
# Seed flag
# ---------------------------------------------------------------------------

class TestMainSeed:
    def test_seed_calls_create_server_config_and_data(self, mocker, tmp_path,
                                                      mock_wms, mock_make_server):
        mock_examples = mocker.MagicMock()
        mocker.patch("mslib.mswms.mswms.argparse.ArgumentParser.parse_args",
                     return_value=_args(seed=True))
        mocker.patch("mslib.mswms.mswms.DataFiles", return_value=mock_examples)
        mocker.patch("mslib.mswms.mswms.Path.home", return_value=tmp_path)
        mswms.main()
        mock_examples.create_server_config.assert_called_once_with(detailed_information=True)
        mock_examples.create_data.assert_called_once()

    def test_seed_prints_pythonpath_hint(self, mocker, tmp_path, capsys,
                                         mock_wms, mock_make_server):
        mocker.patch("mslib.mswms.mswms.argparse.ArgumentParser.parse_args",
                     return_value=_args(seed=True))
        mocker.patch("mslib.mswms.mswms.DataFiles")
        mocker.patch("mslib.mswms.mswms.Path.home", return_value=tmp_path)
        mswms.main()
        assert "PYTHONPATH" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Gallery subcommand
# ---------------------------------------------------------------------------

class TestMainGallery:
    @pytest.fixture(autouse=True)
    def _patch_wms(self, mocker):
        mock_settings = mocker.MagicMock()
        mock_settings.__file__ = "/fake/mswms_settings.py"
        mocker.patch("mslib.mswms.wms.mswms_settings", mock_settings)
        self.mock_gallery_server = mocker.MagicMock()
        mocker.patch("mslib.mswms.wms.server", self.mock_gallery_server)

    def _run(self, mocker, args):
        mocker.patch("mslib.mswms.mswms.argparse.ArgumentParser.parse_args", return_value=args)
        with pytest.raises(SystemExit):
            mswms.main()
        return self.mock_gallery_server

    def test_gallery_exits(self, mocker):
        self._run(mocker, _gallery_args())

    def test_gallery_default_plot_types(self, mocker):
        srv = self._run(mocker, _gallery_args())
        srv.generate_gallery.assert_called_once_with(
            False, False, False,
            url_prefix="", levels="", itimes="", vtimes="",
            plot_types=["Top", "Side", "Linear"],
        )

    def test_gallery_custom_plot_types(self, mocker):
        srv = self._run(mocker, _gallery_args(plot_types="Top,Side"))
        _, kwargs = srv.generate_gallery.call_args
        assert kwargs["plot_types"] == ["Top", "Side"]

    def test_gallery_plot_types_strips_spaces(self, mocker):
        srv = self._run(mocker, _gallery_args(plot_types="Top, Side, Linear"))
        _, kwargs = srv.generate_gallery.call_args
        assert kwargs["plot_types"] == ["Top", "Side", "Linear"]

    def test_gallery_create_flag(self, mocker):
        srv = self._run(mocker, _gallery_args(create=True))
        pos, _ = srv.generate_gallery.call_args
        assert pos[0] is True   # create
        assert pos[1] is False  # clear

    def test_gallery_clear_flag(self, mocker):
        srv = self._run(mocker, _gallery_args(clear=True))
        pos, _ = srv.generate_gallery.call_args
        assert pos[0] is False  # create
        assert pos[1] is True   # clear

    def test_gallery_refresh_sets_both_create_and_clear(self, mocker):
        srv = self._run(mocker, _gallery_args(refresh=True))
        pos, _ = srv.generate_gallery.call_args
        assert pos[0] is True   # create
        assert pos[1] is True   # clear

    def test_gallery_show_code(self, mocker):
        srv = self._run(mocker, _gallery_args(show_code=True))
        pos, _ = srv.generate_gallery.call_args
        assert pos[2] is True

    def test_gallery_url_prefix(self, mocker):
        srv = self._run(mocker, _gallery_args(url_prefix="/demo"))
        _, kwargs = srv.generate_gallery.call_args
        assert kwargs["url_prefix"] == "/demo"

    def test_gallery_levels_itimes_vtimes(self, mocker):
        srv = self._run(mocker, _gallery_args(
            levels="200,300",
            itimes="2012-10-17T12:00:00",
            vtimes="2012-10-19T12:00:00",
        ))
        _, kwargs = srv.generate_gallery.call_args
        assert kwargs["levels"] == "200,300"
        assert kwargs["itimes"] == "2012-10-17T12:00:00"
        assert kwargs["vtimes"] == "2012-10-19T12:00:00"
