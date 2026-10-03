# -*- coding: utf-8 -*-
"""

    tests._test_mswms.test_wms
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests mswms.wms

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2016-2026 by the MSS team, see AUTHORS.
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
import os
from shutil import move

import mock
from nco import Nco
import pytest

import mslib.mswms.wms
import mslib.mswms.gallery_builder
from importlib import reload
from tests.utils import callback_ok_image, callback_ok_xml, callback_ok_html, callback_404_plain
from tests.constants import MSWMS_DATA_DIR


HSEC_QUERY = (
    'layers=ecmwf_EUR_LL015.PLDiv01&styles=&elevation=200&srs=EPSG%3A4326&format=image%2Fpng&'
    'request=GetMap&height=376&dim_init_time=2012-10-17T12%3A00%3A00Z&width=479&'
    'version=1.1.1&bbox=-50.0%2C20.0%2C20.0%2C75.0&time=2012-10-17T12%3A00%3A00Z&transparent=FALSE')
VSEC_QUERY = (
    'layers=ecmwf_EUR_LL015.VS_HV01&styles=&srs=VERT%3ALOGP&format=image%2Fpng&'
    'request=GetMap&height=245&dim_init_time=2012-10-17T12%3A00%3A00Z&width=842&'
    'version=1.1.1&bbox=201%2C500.0%2C10%2C100.0&time=2012-10-17T12%3A00%3A00Z&'
    'path=52.78%2C-8.93%2C48.08%2C11.28&transparent=FALSE')
LSEC_QUERY = (
    'layers=ecmwf_EUR_LL015.LS_HV01&styles=&srs=LINE%3A1&format=text%2Fxml&'
    'request=GetMap&dim_init_time=2012-10-17T12%3A00%3A00Z&'
    'version=1.1.1&bbox=201&time=2012-10-17T12%3A00%3A00Z&'
    'path=52.78%2C-8.93%2C25000%2C48.08%2C11.28%2C25000')


class Test_WMS:
    @pytest.fixture(autouse=True)
    def setup(self, mswms_app):
        self.app = mswms_app

    def test_get_query_string_missing_parameters(self):
        environ = {
            'wsgi.url_scheme': 'http',
            'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
            'QUERY_STRING': 'request=GetCapabilities'}

        self.client = self.app.test_client()
        result = self.client.get('/?{}'.format(environ["QUERY_STRING"]))
        callback_404_plain(result.status, result.headers)
        assert isinstance(result.data, bytes), result

    def test_get_query_string_wrong_values(self):
        # version implemented is 1.1.1 and 1.3.0
        environ = {
            'wsgi.url_scheme': 'http',
            'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
            'QUERY_STRING': 'request=GetCapabilities&service=WMS&version=1.4.0'}

        self.client = self.app.test_client()
        result = self.client.get('/?{}'.format(environ["QUERY_STRING"]))
        callback_404_plain(result.status, result.headers)
        assert isinstance(result.data, bytes), result

    def test_get_capabilities(self):
        cases = (
            {
                'wsgi.url_scheme': 'http',
                'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
                'QUERY_STRING': 'request=GetCapabilities&service=WMS&version=1.1.1'
            },
            {
                'wsgi.url_scheme': 'http',
                'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
                'QUERY_STRING': 'request=GetCapabilities&service=WMS&version=1.3.0'
            },
            {
                'wsgi.url_scheme': 'http',
                'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
                'QUERY_STRING': 'request=capabilities&service=WMS&version=1.1.1'
            },
            {
                'wsgi.url_scheme': 'http',
                'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
                'QUERY_STRING': 'request=capabilities&service=WMS&version=1.3.0'
            },
            {
                'wsgi.url_scheme': 'http',
                'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1',
                'HTTP_HOST': 'localhost:8081',
                'QUERY_STRING': 'request=capabilities&service=WMS&version'
            },
            {
                'wsgi.url_scheme': 'http',
                'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1',
                'HTTP_HOST': 'localhost:8081',
                'QUERY_STRING': 'request=capabilities&service=WMS'
            },
        )

        for tst_case in cases:
            self.client = self.app.test_client()
            result = self.client.get('/?{}'.format(tst_case["QUERY_STRING"]))
            callback_ok_xml(result.status, result.headers)
            assert isinstance(result.data, bytes), result

    def test_get_capabilities_lowercase(self):
        environ = {
            'wsgi.url_scheme': 'http',
            'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
            'QUERY_STRING': 'request=getcapabilities&service=wms&version=1.1.1'}
        self.client = self.app.test_client()
        result = self.client.get('/?{}'.format(environ["QUERY_STRING"]))
        callback_ok_xml(result.status, result.headers)
        assert isinstance(result.data, bytes), result

    def test_produce_hsec_plot(self):
        environ = {
            'wsgi.url_scheme': 'http',
            'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
            'QUERY_STRING':
                'layers=ecmwf_EUR_LL015.PLDiv01&styles=&elevation=200&srs=EPSG%3A4326&format=image%2Fpng&'
                'request=GetMap&bgcolor=0xFFFFFF&height=376&dim_init_time=2012-10-17T12%3A00%3A00Z&width=479&'
                'version=1.1.1&bbox=-50.0%2C20.0%2C20.0%2C75.0&time=2012-10-17T12%3A00%3A00Z&'
                'exceptions=application%2Fvnd.ogc.se_xml&transparent=FALSE'}
        self.client = self.app.test_client()
        result = self.client.get('/?{}'.format(environ["QUERY_STRING"]))
        callback_ok_image(result.status, result.headers)

        environ = {
            'wsgi.url_scheme': 'http',
            'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
            'QUERY_STRING':
                'layers=ecmwf_EUR_LL015.PLDiv01&styles=&elevation=200&crs=EPSG%3A4326&format=image%2Fpng&'
                'request=GetMap&bgcolor=0xFFFFFF&height=376&dim_init_time=2012-10-17T12%3A00%3A00Z&width=479&'
                'version=1.3.0&bbox=20.0%2C-50.0%2C75.0%2C20.0&time=2012-10-17T12%3A00%3A00Z&'
                'exceptions=XML&transparent=FALSE'}
        result = self.client.get('/?{}'.format(environ["QUERY_STRING"]))
        callback_ok_image(result.status, result.headers)

    def test_produce_hsec_service_exception(self):
        environ = {
            'wsgi.url_scheme': 'http',
            'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
            'QUERY_STRING':
                'layers=ecmwf_EUR_LL015.PLDiv01&styles=&elevation=200&srs=EPSG%3A4326&format=image%2Fpng&'
                'request=GetMap&bgcolor=0xFFFFFF&height=376&dim_init_time=2012-10-17T12%3A00%3A00Z&width=479&'
                'version=1.1.1&bbox=-50.0%2C20.0%2C20.0%2C75.0&time=2012-10-17T12%3A00%3A00Z&'
                'exceptions=application%2Fvnd.ogc.se_xml&transparent=FALSE'}
        query_string = environ["QUERY_STRING"]
        self.client = self.app.test_client()
        result = self.client.get('/?{}'.format(query_string))
        callback_ok_image(result.status, result.headers)
        assert result.data.count(b"ServiceExceptionReport") == 0, result

        for orig, fake in [
                ("dim_init_time=2012-10-17T12%3A00%3A00Z", "dim_init_time=a20121017T12%3A00%3A00Z"),
                ("time=2012-10-17T12%3A00%3A00Z", "time=a20121-0-17T12%3A00%3A00Z"),
                ("time=2012-10-17T12%3A00%3A00Z", "time=2012-01-17T12%3A00%3A00Z"),
                ("&dim_init_time=2012-10-17T12%3A00%3A00Z", ""),
                ("&time=2012-10-17T12%3A00%3A00Z", ""),
                ("srs=EPSG%3A4326", "srs=EPSH%3A4326"),
                ("srs=EPSG%3A4326", "srs=EPSG%3AABCD"),
                ("srs=EPSG%3A4326", "srs=EPSG%3A6666"),
                ("ecmwf_EUR_LL015.PLDiv01", "PLDiv01"),
                ("ecmwf_EUR_LL015.PLDiv01", "ecmwf_EUR_LL015.PLDav01"),
                ("ecmwf_EUR_LL015.PLDiv01", "ecmwf_AUR_LL015.PLDiv01"),
                ("format=image%2Fpng", "format=omage%2Fpng"),  # codespell:ignore omage
                ("bbox=-50.0%2C20.0%2C20.0%2C75.0", "bbox=-abcd%2C20.0%2C20.0%2C75.0")]:
            environ["QUERY_STRING"] = query_string.replace(orig, fake)
            result = self.client.get('/?{}'.format(environ["QUERY_STRING"]))
            callback_ok_xml(result.status, result.headers)
            assert result.data.count(b"ServiceExceptionReport") > 0, result

    def test_produce_vsec_plot(self):
        environ = {
            'wsgi.url_scheme': 'http',
            'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
            'QUERY_STRING':
                'layers=ecmwf_EUR_LL015.VS_HV01&styles=&srs=VERT%3ALOGP&format=image%2Fpng&'
                'request=GetMap&bgcolor=0xFFFFFF&height=245&dim_init_time=2012-10-17T12%3A00%3A00Z&width=842&'
                'version=1.1.1&bbox=201%2C500.0%2C10%2C100.0&time=2012-10-17T12%3A00%3A00Z&'
                'exceptions=application%2Fvnd.ogc.se_xml&path=52.78%2C-8.93%2C48.08%2C11.28&transparent=FALSE'}

        self.client = self.app.test_client()
        result = self.client.get('/?{}'.format(environ["QUERY_STRING"]))
        callback_ok_image(result.status, result.headers)

        environ = {
            'wsgi.url_scheme': 'http',
            'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
            'QUERY_STRING':
                'layers=ecmwf_EUR_LL015.VS_HV01&styles=&crs=VERT%3ALOGP&format=image%2Fpng&'
                'request=GetMap&bgcolor=0xFFFFFF&height=245&dim_init_time=2012-10-17T12%3A00%3A00Z&width=842&'
                'version=1.3.0&bbox=201%2C500.0%2C10%2C100.0&time=2012-10-17T12%3A00%3A00Z&'
                'exceptions=XML&path=52.78%2C-8.93%2C48.08%2C11.28&transparent=FALSE'}

        result = self.client.get('/?{}'.format(environ["QUERY_STRING"]))
        callback_ok_image(result.status, result.headers)

    def test_produce_vsec_service_exception(self):
        environ = {
            'wsgi.url_scheme': 'http',
            'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
            'QUERY_STRING':
                'layers=ecmwf_EUR_LL015.VS_HV01&styles=&srs=VERT%3ALOGP&format=image%2Fpng&'
                'request=GetMap&bgcolor=0xFFFFFF&height=245&dim_init_time=2012-10-17T12%3A00%3A00Z&width=842&'
                'version=1.1.1&bbox=201%2C500.0%2C10%2C100.0&time=2012-10-17T12%3A00%3A00Z&'
                'exceptions=application%2Fvnd.ogc.se_xml&path=52.78%2C-8.93%2C48.08%2C11.28&transparent=FALSE'}
        query_string = environ["QUERY_STRING"]

        self.client = self.app.test_client()
        result = self.client.get('/?{}'.format(query_string))
        callback_ok_image(result.status, result.headers)
        assert result.data.count(b"ServiceExceptionReport") == 0, result

        for orig, fake in [
                ("time=2012-10-17T12%3A00%3A00Z", "time=2012-01-17T12%3A00%3A00Z"),
                ("&dim_init_time=2012-10-17T12%3A00%3A00Z", ""),
                ("&time=2012-10-17T12%3A00%3A00Z", ""),
                ("layers=ecmwf_EUR_LL015.VS_HV01", "layers=ecmwf_AUR_LL015.VS_HV01"),
                ("layers=ecmwf_EUR_LL015.VS_HV01", "layers=ecmwf_EUR_LL015.VS_HV99"),
                ("format=image%2Fpng", "format=omage%2Fpng"),  # codespell:ignore omage
                ("path=52.78%2C-8.93%2C48.08%2C11.28", "path=aaaa%2C-8.93%2C48.08%2C11.28"),
                ("&path=52.78%2C-8.93%2C48.08%2C11.28", ""),
                ("bbox=201%2C500.0%2C10%2C100.0", "bbox=aaa%2C500.0%2C10%2C100.0")]:
            environ["QUERY_STRING"] = query_string.replace(orig, fake)

            result = self.client.get('/?{}'.format(environ["QUERY_STRING"]))
            callback_ok_xml(result.status, result.headers)
            assert result.data.count(b"ServiceExceptionReport") > 0, result

    def test_produce_lsec_plot(self):
        environ = {
            'wsgi.url_scheme': 'http',
            'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
            'QUERY_STRING':
                'layers=ecmwf_EUR_LL015.LS_HV01&styles=&srs=LINE%3A1&format=text%2Fxml&'
                'request=GetMap&dim_init_time=2012-10-17T12%3A00%3A00Z&'
                'version=1.1.1&bbox=201&time=2012-10-17T12%3A00%3A00Z&'
                'exceptions=application%2Fvnd.ogc.se_xml&path=52.78%2C-8.93%2C25000%2C48.08%2C11.28%2C25000'}

        self.client = self.app.test_client()
        result = self.client.get('/?{}'.format(environ["QUERY_STRING"]))
        callback_ok_xml(result.status, result.headers)

        environ = {
            'wsgi.url_scheme': 'http',
            'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
            'QUERY_STRING':
                'layers=ecmwf_EUR_LL015.LS_HV01&styles=&crs=LINE%3A1&format=text%2Fxml&'
                'request=GetMap&dim_init_time=2012-10-17T12%3A00%3A00Z&'
                'version=1.3.0&bbox=201&time=2012-10-17T12%3A00%3A00Z&'
                'exceptions=application%2Fvnd.ogc.se_xml&path=52.78%2C-8.93%2C25000%2C48.08%2C11.28%2C25000'}

        result = self.client.get('/?{}'.format(environ["QUERY_STRING"]))
        callback_ok_xml(result.status, result.headers)

    def test_produce_lsec_service_exception(self):
        environ = {
            'wsgi.url_scheme': 'http',
            'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
            'QUERY_STRING':
                'layers=ecmwf_EUR_LL015.LS_HV01&styles=&srs=LINE%3A1&format=text%2Fxml&'
                'request=GetMap&dim_init_time=2012-10-17T12%3A00%3A00Z&'
                'version=1.1.1&bbox=201&time=2012-10-17T12%3A00%3A00Z&'
                'exceptions=application%2Fvnd.ogc.se_xml&path=52.78%2C-8.93%2C25000%2C48.08%2C11.28%2C25000'}
        query_string = environ["QUERY_STRING"]

        self.client = self.app.test_client()
        result = self.client.get('/?{}'.format(query_string))
        callback_ok_xml(result.status, result.headers)
        assert result.data.count(b"ServiceExceptionReport") == 0, result

        for orig, fake in [
                ("time=2012-10-17T12%3A00%3A00Z", "time=2012-01-17T12%3A00%3A00Z"),
                ("&dim_init_time=2012-10-17T12%3A00%3A00Z", ""),
                ("&time=2012-10-17T12%3A00%3A00Z", ""),
                ("layers=ecmwf_EUR_LL015.LS_HV01", "layers=ecmwf_AUR_LL015.LS_HV01"),
                ("layers=ecmwf_EUR_LL015.LS_HV01", "layers=ecmwf_EUR_LL015.LS_HV99"),
                ("format=text%2Fxml", "format=oext%2Fxml"),
                ("path=52.78%2C-8.93%2C25000%2C48.08%2C11.28%2C25000",
                 "path=aaaa%2C-8.93%2C25000%2C48.08%2C11.28%2C25000"),
                ("&path=52.78%2C-8.93%2C25000%2C48.08%2C11.28%2C25000", ""),
                ("bbox=201", "bbox=aaa")]:
            environ["QUERY_STRING"] = query_string.replace(orig, fake)

            result = self.client.get('/?{}'.format(environ["QUERY_STRING"]))
            callback_ok_xml(result.status, result.headers)
            assert result.data.count(b"ServiceExceptionReport") > 0, result

    def test_application_request(self):
        environ = {
            'wsgi.url_scheme': 'http',
            'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
            'QUERY_STRING':
                'layers=ecmwf_EUR_LL015.PLDiv01&styles=&elevation=200&srs=EPSG%3A4326&format=image%2Fpng&'
                'request=GetMap&bgcolor=0xFFFFFF&height=376&dim_init_time=2012-10-17T12%3A00%3A00Z&width=479&'
                'version=1.1.1&bbox=-50.0%2C20.0%2C20.0%2C75.0&time=2012-10-17T12%3A00%3A00Z&'
                'exceptions=application%2Fvnd.ogc.se_xml&transparent=FALSE'}

        self.client = self.app.test_client()
        result = self.client.get('/?{}'.format(environ["QUERY_STRING"]))
        assert isinstance(result.data, bytes), result

    def test_application_request_lowercase(self):
        environ = {
            'wsgi.url_scheme': 'http',
            'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
            'QUERY_STRING':
                'layers=ecmwf_EUR_LL015.PLDiv01&styles=&elevation=200&srs=EPSG%3A4326&format=image%2Fpng&'
                'request=getmap&bgcolor=0xFFFFFF&height=376&dim_init_time=2012-10-17T12%3A00%3A00Z&width=479&'
                'version=1.1.1&bbox=-50.0%2C20.0%2C20.0%2C75.0&time=2012-10-17T12%3A00%3A00Z&'
                'exceptions=application%2Fvnd.ogc.se_xml&transparent=FALSE'}

        self.client = self.app.test_client()
        result = self.client.get('/?{}'.format(environ["QUERY_STRING"]))
        assert isinstance(result.data, bytes), result

    def test_application_norequest(self):
        environ = {
            'wsgi.url_scheme': 'http',
            'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
            'QUERY_STRING': '',
        }

        self.client = self.app.test_client()
        result = self.client.get('/?{}'.format(environ["QUERY_STRING"]))
        callback_ok_html(result.status, result.headers)
        assert isinstance(result.data, bytes), result
        assert result.data.count(b"") >= 1, result

    def test_application_unkown_request(self):
        environ = {
            'wsgi.url_scheme': 'http',
            'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
            'QUERY_STRING': 'request=abraham',
        }
        self.client = self.app.test_client()
        result = self.client.get('/?{}'.format(environ["QUERY_STRING"]))
        callback_404_plain(result.status, result.headers)
        assert isinstance(result.data, bytes), result
        assert result.data.count(b"") > 0, result

    def test_multiple_images(self):
        environ = {
            'wsgi.url_scheme': 'http',
            'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
            'QUERY_STRING':
                'layers=ecmwf_EUR_LL015.PLDiv01,ecmwf_EUR_LL015.PLTemp01&styles=&elevation=200&'
                'srs=EPSG%3A4326&format=image%2Fpng&'
                'request=GetMap&bgcolor=0xFFFFFF&height=376&dim_init_time=2012-10-17T12%3A00%3A00Z&width=479&'
                'version=1.1.1&bbox=-50.0%2C20.0%2C20.0%2C75.0&time=2012-10-17T12%3A00%3A00Z&'
                'exceptions=application%2Fvnd.ogc.se_xml&transparent=FALSE'}

        self.client = self.app.test_client()
        result = self.client.get('/?{}'.format(environ["QUERY_STRING"]))
        callback_ok_image(result.status, result.headers)
        assert isinstance(result.data, bytes), result

    def test_multiple_xml(self):
        environ = {
            'wsgi.url_scheme': 'http',
            'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
            'QUERY_STRING':
                'layers=ecmwf_EUR_LL015.LS_HV01,ecmwf_EUR_LL015.LS_HV01&styles=&srs=LINE%3A1&format=text%2Fxml&'
                'request=GetMap&dim_init_time=2012-10-17T12%3A00%3A00Z&'
                'version=1.1.1&bbox=201&time=2012-10-17T12%3A00%3A00Z&'
                'exceptions=application%2Fvnd.ogc.se_xml&path=52.78%2C-8.93%2C25000%2C48.08%2C11.28%2C25000'}

        self.client = self.app.test_client()
        result = self.client.get('/?{}'.format(environ["QUERY_STRING"]))
        callback_ok_xml(result.status, result.headers)

    @pytest.mark.parametrize("query, orig, fake, message", [
        (HSEC_QUERY, "width=479", "width=65000", b"WIDTH must be between 1 and 4096"),
        (HSEC_QUERY, "height=376", "height=65000", b"HEIGHT must be between 1 and 4096"),
        (VSEC_QUERY, "width=842", "width=4097", b"WIDTH must be between 1 and 4096"),
        (HSEC_QUERY, "width=479", "width=0", b"WIDTH must be between"),
        (HSEC_QUERY, "width=479", "width=-479", b"WIDTH must be between"),
        (HSEC_QUERY, "width=479", "width=nan", b"WIDTH must be a finite number"),
        (HSEC_QUERY, "height=376", "height=inf", b"HEIGHT must be a finite number"),
        (HSEC_QUERY, "width=479", "width=abc", b"Invalid WIDTH"),
        (HSEC_QUERY, "layers=ecmwf_EUR_LL015.PLDiv01", "layers=" + ",".join(["ecmwf_EUR_LL015.PLDiv01"] * 11),
         b"At most 10 LAYERS"),
        (HSEC_QUERY, "layers=ecmwf_EUR_LL015.PLDiv01", "layers=ecmwf_EUR_LL015.PLDiv01,ecmwf_EUR_LL015.PLDiv01",
         b"LAYERS must not contain the same layer with the same style more than once"),
        (HSEC_QUERY, "bbox=-50.0%2C20.0%2C20.0%2C75.0", "bbox=-1000%2C-90%2C1000%2C90",
         b"BBOX must span at most 360 degrees of longitude"),
        (HSEC_QUERY, "bbox=-50.0%2C20.0%2C20.0%2C75.0", "bbox=0%2C0%2C0%2C0",
         b"BBOX must have minimum values smaller than its maximum values"),
        (HSEC_QUERY, "bbox=-50.0%2C20.0%2C20.0%2C75.0", "bbox=20.0%2C20.0%2C-50.0%2C75.0",
         b"BBOX must have minimum values smaller than its maximum values"),
        (HSEC_QUERY, "bbox=-50.0%2C20.0%2C20.0%2C75.0", "bbox=-50.0%2C20.0%2C20.0%2C95.0",
         b"BBOX latitudes must be between -90 and 90"),
        (HSEC_QUERY, "layers=ecmwf_EUR_LL015.PLDiv01", "layers=", b"LAYERS not specified"),
        (HSEC_QUERY, "bbox=-50.0", "bbox=nan", b"BBOX must be a finite number"),
        (HSEC_QUERY, "bbox=-50.0%2C", "bbox=", b"BBOX needs 4 values, got 3"),
        (HSEC_QUERY, "elevation=200", "elevation=abc", b"Invalid ELEVATION"),
        (HSEC_QUERY, "elevation=200", "elevation=-inf", b"ELEVATION must be a finite number"),
        (VSEC_QUERY, "bbox=201", "bbox=1e8", b"BBOX number of points must be between 2 and 2000"),
        (VSEC_QUERY, "bbox=201", "bbox=1", b"BBOX number of points must be between 2 and 2000"),
        (VSEC_QUERY, "bbox=201", "bbox=201.5", b"BBOX number of points must be an integer"),
        (VSEC_QUERY, "bbox=201", "bbox=nan", b"BBOX must be a finite number"),
        (VSEC_QUERY, "%2C10%2C", "%2C0%2C", b"BBOX number of labels must be between 1 and 2000"),
        (VSEC_QUERY, "%2C10%2C", "%2C1e9%2C", b"BBOX number of labels must be between 1 and 2000"),
        (VSEC_QUERY, "500.0", "inf", b"BBOX must be a finite number"),
        (VSEC_QUERY, "%2C100.0", "", b"BBOX needs 4 values, got 3"),
        (VSEC_QUERY, "path=52.78%2C-8.93%2C48.08%2C11.28", "path=" + "%2C".join(["52.78%2C-8.93"] * 1001),
         b"PATH has more than 2000 values"),
        (VSEC_QUERY, "path=52.78", "path=inf", b"PATH must be a finite number"),
        (VSEC_QUERY, "path=52.78%2C-8.93%2C48.08%2C11.28", "path=5", b"PATH needs at least 4 values, got 1"),
        (VSEC_QUERY, "path=52.78%2C-8.93%2C48.08%2C11.28", "path=52.78%2C-8.93%2C48.08",
         b"PATH needs at least 4 values, got 3"),
        (VSEC_QUERY, "path=52.78%2C-8.93%2C48.08%2C11.28", "path=52.78%2C-8.93%2C48.08%2C11.28%2C50",
         b"PATH needs a multiple of 2 values, got 5"),
        (LSEC_QUERY, "bbox=201", "bbox=5e6", b"BBOX number of points must be between 2 and 2000"),
        (LSEC_QUERY, "bbox=201", "bbox=nan", b"BBOX number of points must be a finite number"),
        (LSEC_QUERY, "path=52.78%2C-8.93%2C25000%2C48.08%2C11.28%2C25000",
         "path=" + "%2C".join(["52.78%2C-8.93%2C25000"] * 1001), b"PATH has more than 3000 values"),
        (LSEC_QUERY, "path=52.78", "path=nan", b"PATH must be a finite number"),
        (LSEC_QUERY, "path=52.78%2C-8.93%2C25000%2C48.08%2C11.28%2C25000", "path=52.78%2C-8.93%2C25000",
         b"PATH needs at least 6 values, got 3"),
        (LSEC_QUERY, "path=52.78%2C-8.93%2C25000%2C48.08%2C11.28%2C25000",
         "path=52.78%2C-8.93%2C25000%2C48.08%2C11.28%2C25000%2C1", b"PATH needs a multiple of 3 values, got 7"),
    ])
    def test_produce_plot_rejects_values_beyond_limits(self, query, orig, fake, message):
        assert orig in query
        result = self.app.test_client().get('/?{}'.format(query.replace(orig, fake, 1)))
        callback_ok_xml(result.status, result.headers)
        assert b"ServiceExceptionReport" in result.data, result.data
        assert message in result.data, result.data
        # InvalidParameterValue is no exception code of WMS 1.1.1 or 1.3.0
        assert b"InvalidParameterValue" not in result.data, result.data

    @pytest.mark.parametrize("query, setting, value", [
        (HSEC_QUERY, "max_image_width", 479),
        (HSEC_QUERY, "max_image_height", 376),
        (HSEC_QUERY, "max_layers", 1),
        (VSEC_QUERY, "max_section_points", 201),
        (VSEC_QUERY, "max_path_waypoints", 2),
        (LSEC_QUERY, "max_section_points", 201),
        (LSEC_QUERY, "max_path_waypoints", 2),
    ])
    def test_produce_plot_limits_are_configurable(self, query, setting, value):
        client = self.app.test_client()
        # the query uses exactly the limit
        with mock.patch.object(mslib.mswms.wms.mswms_settings, setting, value):
            result = client.get('/?{}'.format(query))
        assert b"ServiceExceptionReport" not in result.data, result.data
        with mock.patch.object(mslib.mswms.wms.mswms_settings, setting, value - 1):
            result = client.get('/?{}'.format(query))
        callback_ok_xml(result.status, result.headers)
        assert b"ServiceExceptionReport" in result.data, result.data

    def test_produce_plot_accepts_limits(self):
        # msui sends integers, but other clients may send WIDTH/HEIGHT as float
        result = self.app.test_client().get('/?{}'.format(
            HSEC_QUERY.replace("width=479", "width=479.0").replace("height=376", "height=")))
        callback_ok_image(result.status, result.headers)
        result = self.app.test_client().get('/?{}'.format(VSEC_QUERY.replace("bbox=201", "bbox=2")))
        callback_ok_image(result.status, result.headers)
        result = self.app.test_client().get('/?{}'.format(
            HSEC_QUERY.replace("width=479", "width=4096").replace("height=376", "height=4096")))
        callback_ok_image(result.status, result.headers)

    def test_produce_plot_linear_section_ignores_image_size(self):
        # a linear section returns XML, it draws no image
        result = self.app.test_client().get('/?{}&width=65000&height=nan'.format(LSEC_QUERY))
        callback_ok_xml(result.status, result.headers)
        assert b"ServiceExceptionReport" not in result.data, result.data

    def test_get_capabilities_advertises_limits(self):
        result = self.app.test_client().get('/?request=GetCapabilities&service=WMS&version=1.3.0')
        callback_ok_xml(result.status, result.headers)
        assert b"<LayerLimit>10</LayerLimit>" in result.data
        assert b"<MaxWidth>4096</MaxWidth>" in result.data
        assert b"<MaxHeight>4096</MaxHeight>" in result.data

    @pytest.mark.skip(reason="disabled because of reload")
    def test_import_error(self):
        with mock.patch.dict("sys.modules", {"mswms_settings": None, "mswms_auth": None}):
            reload(mslib.mswms.wms)
            assert mslib.mswms.wms.mswms_settings.__file__ is None
            assert mslib.mswms.wms.mswms_auth.__file__ is None
        reload(mslib.mswms.wms)
        assert mslib.mswms.wms.mswms_settings.__file__ is not None
        assert mslib.mswms.wms.mswms_auth.__file__ is not None

    def test_files_changed(self):
        def do_test():
            environ = {
                'wsgi.url_scheme': 'http',
                'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
                'QUERY_STRING':
                'layers=ecmwf_EUR_LL015.PLDiv01&styles=&elevation=200&crs=EPSG%3A4326&format=image%2Fpng&'
                'request=GetMap&bgcolor=0xFFFFFF&height=376&dim_init_time=2012-10-17T12%3A00%3A00Z&width=479&'
                'version=1.3.0&bbox=20.0%2C-50.0%2C75.0%2C20.0&time=2012-10-17T12%3A00%3A00Z&'
                'exceptions=XML&transparent=FALSE'}
            pl_file = next(file for file in os.listdir(MSWMS_DATA_DIR) if ".pl" in file)

            self.client = self.app.test_client()
            result = self.client.get('/?{}'.format(environ["QUERY_STRING"]))

            # Assert modified file was reloaded and now looks different
            nco = Nco()
            nco.ncap2(input=os.path.join(MSWMS_DATA_DIR, pl_file), output=os.path.join(MSWMS_DATA_DIR, pl_file),
                      options=["-s \"geopotential_height*=2\""])
            result2 = self.client.get('/?{}'.format(environ["QUERY_STRING"]))
            nco.ncap2(input=os.path.join(MSWMS_DATA_DIR, pl_file), output=os.path.join(MSWMS_DATA_DIR, pl_file),
                      options=["-s \"geopotential_height/=2\""])
            assert result.data != result2.data

            # Assert moved file was reloaded and now looks like the first image
            move(os.path.join(MSWMS_DATA_DIR, pl_file), os.path.join(MSWMS_DATA_DIR, pl_file + "2"))
            result3 = self.client.get('/?{}'.format(environ["QUERY_STRING"]))
            move(os.path.join(MSWMS_DATA_DIR, pl_file + "2"), os.path.join(MSWMS_DATA_DIR, pl_file))
            assert result.data == result3.data

        with pytest.raises(AssertionError):
            do_test()

        watch_access = mslib.mswms.dataaccess.WatchModificationDataAccess(
            mslib.mswms.wms.mswms_settings._datapath, "EUR_LL015")
        watch_access.setup()
        with mock.patch.object(
            mslib.mswms.wms.server.hsec_layer_registry["ecmwf_EUR_LL015"]["PLDiv01"].driver,
            "data_access", new=watch_access):
            do_test()

    @pytest.mark.skip("""\
This test changes global variables (e.g. DOCS_LOCATION) which can affect other tests depending on test order
(e.g. tests/_test_mswms/test_mss_plot_driver.py::Test_VSec::test_VS_gallery_template fails consistently in reverse order
on macOS 14).
""".strip(),
    )
    def test_gallery(self, tmpdir):
        tempdir = tmpdir.mkdir("static")
        docsdir = tmpdir.mkdir("docs")
        mslib.mswms.wms.STATIC_LOCATION = tempdir
        mslib.mswms.gallery_builder.STATIC_LOCATION = tempdir
        mslib.mswms.wms.DOCS_LOCATION = docsdir
        mslib.mswms.gallery_builder.DOCS_LOCATION = docsdir
        linear_plots = [[mslib.mswms.wms.server.lsec_drivers, mslib.mswms.wms.server.lsec_layer_registry]]

        mslib.mswms.wms.server.generate_gallery(generate_code=True, plot_list=linear_plots)
        assert os.path.exists(os.path.join(tempdir, "plots"))
        assert os.path.exists(os.path.join(tempdir, "code"))
        assert os.path.exists(os.path.join(tempdir, "plots.html"))
        mslib.mswms.gallery_builder.plot_htmls = {}

        mslib.mswms.wms.server.generate_gallery(generate_code=False, plot_list=linear_plots)
        assert not os.path.exists(os.path.join(tempdir, "code"))

        file = os.path.join(tempdir, "plots", os.listdir(os.path.join(tempdir, "plots"))[0])
        file2 = os.path.join(tempdir, "plots", os.listdir(os.path.join(tempdir, "plots"))[1])
        modified_at = os.path.getmtime(file2)
        os.remove(file)
        assert not os.path.exists(file)
        mslib.mswms.wms.server.generate_gallery(generate_code=False, plot_list=linear_plots)
        assert not os.path.exists(os.path.join(tempdir, "code"))
        assert os.path.exists(file), file
        assert modified_at == os.path.getmtime(file2), \
            (modified_at, os.path.getmtime(file2))

        mslib.mswms.wms.server.generate_gallery(clear=True, create=True, plot_list=linear_plots)
        assert modified_at != os.path.getmtime(file2)
        mslib.mswms.gallery_builder.plot_htmls = {}

        mslib.mswms.wms.server.generate_gallery(clear=True, generate_code=True, sphinx=True,
                                                plot_list=linear_plots)
        assert os.path.exists(os.path.join(docsdir, "plots"))
        assert os.path.exists(os.path.join(docsdir, "code"))
        assert os.path.exists(os.path.join(docsdir, "plots.html"))
        mslib.mswms.gallery_builder.plot_htmls = {}
