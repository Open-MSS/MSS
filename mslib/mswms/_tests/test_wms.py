# -*- coding: utf-8 -*-
"""

    mslib.mswms._tests.test_wms
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests mswms.wms

    This file is part of mss.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2017 Joern Ungermann
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

import mock
import os
import mslib.mswms.wms
import mslib.mswms.gallery_builder
import mslib.mswms.mswms as mswms
from importlib import reload
from mslib._tests.utils import callback_ok_image, callback_ok_xml, callback_ok_html, callback_404_plain


class Test_WMS(object):
    def test_get_query_string_missing_parameters(self):
        environ = {
            'wsgi.url_scheme': 'http',
            'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
            'QUERY_STRING': 'request=GetCapabilities'}

        self.client = mswms.application.test_client()
        result = self.client.get('/?{}'.format(environ["QUERY_STRING"]))
        callback_404_plain(result.status, result.headers)
        assert isinstance(result.data, bytes), result

    def test_get_query_string_wrong_values(self):
        # version implemented is 1.1.1 and 1.3.0
        environ = {
            'wsgi.url_scheme': 'http',
            'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
            'QUERY_STRING': 'request=GetCapabilities&service=WMS&version=1.4.0'}

        self.client = mswms.application.test_client()
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
            self.client = mswms.application.test_client()
            result = self.client.get('/?{}'.format(tst_case["QUERY_STRING"]))
            callback_ok_xml(result.status, result.headers)
            assert isinstance(result.data, bytes), result

    def test_get_capabilities_lowercase(self):
        environ = {
            'wsgi.url_scheme': 'http',
            'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
            'QUERY_STRING': 'request=getcapabilities&service=wms&version=1.1.1'}
        self.client = mswms.application.test_client()
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
        self.client = mswms.application.test_client()
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
        self.client = mswms.application.test_client()
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
                ("format=image%2Fpng", "format=omage%2Fpng"),
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

        self.client = mswms.application.test_client()
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

        self.client = mswms.application.test_client()
        result = self.client.get('/?{}'.format(query_string))
        callback_ok_image(result.status, result.headers)
        assert result.data.count(b"ServiceExceptionReport") == 0, result

        for orig, fake in [
                ("time=2012-10-17T12%3A00%3A00Z", "time=2012-01-17T12%3A00%3A00Z"),
                ("&dim_init_time=2012-10-17T12%3A00%3A00Z", ""),
                ("&time=2012-10-17T12%3A00%3A00Z", ""),
                ("layers=ecmwf_EUR_LL015.VS_HV01", "layers=ecmwf_AUR_LL015.VS_HV01"),
                ("layers=ecmwf_EUR_LL015.VS_HV01", "layers=ecmwf_EUR_LL015.VS_HV99"),
                ("format=image%2Fpng", "format=omage%2Fpng"),
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

        self.client = mswms.application.test_client()
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

        self.client = mswms.application.test_client()
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

        self.client = mswms.application.test_client()
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

        self.client = mswms.application.test_client()
        result = self.client.get('/?{}'.format(environ["QUERY_STRING"]))
        assert isinstance(result.data, bytes), result

    def test_application_norequest(self):
        environ = {
            'wsgi.url_scheme': 'http',
            'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'SERVER_PROTOCOL': 'HTTP/1.1', 'HTTP_HOST': 'localhost:8081',
            'QUERY_STRING': '',
        }

        self.client = mswms.application.test_client()
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
        self.client = mswms.application.test_client()
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

        self.client = mswms.application.test_client()
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

        self.client = mswms.application.test_client()
        result = self.client.get('/?{}'.format(environ["QUERY_STRING"]))
        callback_ok_xml(result.status, result.headers)

    def test_import_error(self):
        with mock.patch.dict("sys.modules", {"mss_wms_settings": None, "mss_wms_auth": None}):
            reload(mslib.mswms.wms)
            assert mslib.mswms.wms.mss_wms_settings.__file__ is None
            assert mslib.mswms.wms.mss_wms_auth.__file__ is None
        reload(mslib.mswms.wms)
        assert mslib.mswms.wms.mss_wms_settings.__file__ is not None
        assert mslib.mswms.wms.mss_wms_auth.__file__ is not None

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

        mslib.mswms.wms.server.generate_gallery(generate_code=False, plot_list=linear_plots)
        assert not os.path.exists(os.path.join(tempdir, "code"))

        file = os.path.join(tempdir, "plots", os.listdir(os.path.join(tempdir, "plots"))[0])
        file2 = os.path.join(tempdir, "plots", os.listdir(os.path.join(tempdir, "plots"))[1])
        modified_at = os.path.getmtime(file2)
        os.remove(file)
        assert not os.path.exists(file)
        mslib.mswms.wms.server.generate_gallery(generate_code=False, plot_list=linear_plots)
        assert not os.path.exists(os.path.join(tempdir, "code"))
        assert os.path.exists(file)
        assert modified_at == os.path.getmtime(file2)

        mslib.mswms.wms.server.generate_gallery(clear=True, create=True, plot_list=linear_plots)
        assert modified_at != os.path.getmtime(file2)

        mslib.mswms.wms.server.generate_gallery(clear=True, generate_code=True, sphinx=True,
                                                plot_list=linear_plots)
        assert os.path.exists(os.path.join(docsdir, "plots"))
        assert os.path.exists(os.path.join(docsdir, "code"))
        assert os.path.exists(os.path.join(docsdir, "plots.html"))
