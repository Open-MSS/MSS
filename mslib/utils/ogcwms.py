# -*- coding: ISO-8859-15 -*-
# Copyright (c) 2006, Ancient World Mapping Center
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the University of North Carolina nor the names of
#      its contributors may be used to endorse or promote products derived
#      from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
#
#
#
# =============================================================================
# Copyright (c) 2004, 2006 Sean C. Gillies
# Copyright (c) 2005 Nuxeo SARL <http://nuxeo.com>
#
# Authors : Sean Gillies <sgillies@frii.com>
#           Julien Anguenot <ja@nuxeo.com>
#
# Contact email: sgillies@frii.com
#
# ******************************************************************************
# Changes made for the MSS (flagged with "(mss)"):
#   -- added 'Abstract' to Layer keywords (2010-08).
#   -- bugfix: copy parent SRS only if it has been defined (2010-09-22)
#   -- added dimensions and extents parsing (2011-01-13)
#   -- added storage of capabilities document (2011-01-17)
#   -- renamed to ogcwms (2017-04-28)
#   -- PEP8 review
#   -- adopted it to the recent 0.14 version https://pypi.python.org/pypi/OWSLib/0.14.0
#   -- reduced to what MSS actually adds to owslib, everything else is owslib's
#      again: version negotiation, the capabilities document, the full set of
#      dimensions, proxy support (2026-09)
# ******************************************************************************
#
# =============================================================================

"""
API for Web Map Service (WMS) methods and metadata.

Currently supports only versions 1.1.1/1.3.0 of the WMS protocol.

Only what MSS needs on top of owslib lives here, see `WebMapService`. The
`openURL` below is owslib's, with proxy support added; it is used for the
capabilities request and by `mslib.msui.wms_control` for GetMap.
"""

import defusedxml.ElementTree as etree
import requests
import logging

from owslib.util import ServiceException
from owslib.etree import ParseError
from owslib.map import wms111, wms130, common
from owslib.util import ResponseWrapper, Authentication, strip_bom
from mslib.utils.config import config_loader


#: The version assumed for servers announcing one MSS does not implement.
DEFAULT_VERSION = "1.1.1"

#: The owslib service class per WMS version, as owslib.wms.WebMapService dispatches them.
SERVICE_CLASSES = {
    "1.1.1": wms111.WebMapService_1_1_1,
    "1.3.0": wms130.WebMapService_1_3_0,
}

#: The XML namespace of the layer elements per WMS version, 1.1.1 has none.
WMS_NAMESPACES = {
    "1.1.1": "",
    "1.3.0": "{http://www.opengis.net/wms}",
}


def openURL(url_base, data=None, method='Get', cookies=None,
            username=None, password=None, timeout=None,
            headers=None, verify=None, cert=None, auth=None, proxies=None):
    # (mss) added proxies
    # (mss) timeout defaults to the configured WMS_request_timeout
    """
    Function to open URLs.

    Uses requests library but with additional checks for OGC service exceptions and url formatting.
    Also handles cookies and simple user password authentication.
    """
    headers = headers if headers is not None else {}
    rkwargs = {}

    # (mss) read at call time, the configuration may have changed since import
    rkwargs['timeout'] = config_loader(dataset="WMS_request_timeout") if timeout is None else timeout

    if auth:
        if username:
            auth.username = username
        if password:
            auth.password = password
        if cert:
            auth.cert = cert
        verify = verify and auth.verify
    else:
        auth = Authentication(username, password, cert, verify)
    if auth.username and auth.password:
        rkwargs['auth'] = (auth.username, auth.password)
    rkwargs['cert'] = auth.cert
    rkwargs['verify'] = verify

    # FIXUP for WFS in particular, remove xml style namespace
    # @TODO does this belong here?
    method = method.split("}")[-1]

    if method.lower() == 'post':
        try:
            etree.fromstring(data)
            headers['Content-Type'] = 'text/xml'
        except (ParseError, UnicodeEncodeError) as error:
            # (mss)
            logging.debug("ParseError, UnicodeEncodeError %s", error)

        rkwargs['data'] = data

    elif method.lower() == 'get':
        rkwargs['params'] = data

    else:
        raise ValueError(f"Unknown method ('{method}'), expected 'get' or 'post'")

    if cookies is not None:
        rkwargs['cookies'] = cookies

    req = requests.request(method.upper(),
                           url_base,
                           headers=headers,
                           # MSS
                           proxies=proxies,
                           **rkwargs)

    if req.status_code in [400, 401]:
        raise ServiceException(req.text)

    if req.status_code in [404, 500, 502, 503, 504]:  # add more if needed
        req.raise_for_status()

    # check for service exceptions without the http header set
    if 'Content-Type' in req.headers and req.headers['Content-Type'] in [
            'text/xml', 'application/xml', 'application/vnd.ogc.se_xml', 'application/vnd.ogc.wms_xml']:
        # just in case 400 headers were not set, going to have to read the xml to see if it's an exception report.
        se_tree = etree.fromstring(req.content)

        # to handle the variety of namespaces and terms across services
        # and versions, especially for "legacy" responses like WMS 1.3.0
        possible_errors = [
            '{http://www.opengis.net/ows}Exception',
            '{http://www.opengis.net/ows/1.1}Exception',
            '{http://www.opengis.net/ogc}ServiceException',
            'ServiceException'
        ]

        for possible_error in possible_errors:
            serviceException = se_tree.find(possible_error)
            if serviceException is not None:
                # and we need to deal with some message nesting
                raise ServiceException(
                    '\n'.join([str(t).strip() for t in serviceException.itertext() if t.strip()]))

    return ResponseWrapper(req)


def _parse_dimensions(elem, version):
    """(mss) Parse all dimensions of a layer element and their extents.

    owslib only keeps the two dimensions the standard predefines, "time" and
    "elevation". MSS offers whatever a server announces, e.g. "init_time".

    Up to 1.1.1 the values of a dimension live in a separate <Extent> element,
    1.3.0 merged them into <Dimension>. Both are reported as `extents` here.
    """
    namespace = WMS_NAMESPACES[version]
    dimensions, extents = {}, {}

    def values(element):
        return element.text.strip().split(",") if element.text else []

    for dimension in elem.findall(f"{namespace}Dimension"):
        name = dimension.attrib.get("name").lower()
        dimensions[name] = dict(dimension.attrib)
        if version == "1.3.0":
            extents[name] = dict(dimension.attrib, values=values(dimension))
    for extent in elem.findall(f"{namespace}Extent"):
        name = extent.attrib.get("name").lower()
        extents[name] = dict(extent.attrib, values=values(extent))

    return dimensions, extents


def _patch_content_metadata(module, version):
    """(mss) Let owslib's layer metadata carry every dimension a layer announces.

    owslib instantiates ContentMetadata in two places, WebMapService._buildMetadata
    and the recursion that builds layer.layers, and both resolve the class through
    the module globals. Those are two parallel trees of distinct objects and MSS
    reads dimensions from either, so extending __init__ in place is the one spot
    that covers all of them. Replacing the class by a subclass would not work:
    owslib calls `super(ContentMetadata, self)` with the patched module global and
    would recurse endlessly.
    """
    original_init = module.ContentMetadata.__init__

    def patched_init(self, elem, *args, **kwargs):
        original_init(self, elem, *args, **kwargs)
        self.dimensions, self.extents = _parse_dimensions(elem, version)

    module.ContentMetadata.__init__ = patched_init


for _version, _module in (("1.1.1", wms111), ("1.3.0", wms130)):
    _patch_content_metadata(_module, _version)


def _capabilities_version(capabilities_document):
    """(mss) The WMS version a capabilities document announces, as far as MSS implements it."""
    version = etree.fromstring(capabilities_document).attrib.get("version")
    if version not in SERVICE_CLASSES:
        logging.debug("WMS version '%s' is not supported, reading the document as '%s'",
                      version, DEFAULT_VERSION)
        version = DEFAULT_VERSION
    return version


def _read_capabilities(url, version=None, headers=None, auth=None, timeout=None):
    """(mss) Request a capabilities document through the configured proxies.

    Returns the document and the URL it was requested from. A `version` of None
    leaves the choice to the server.
    """
    request = common.WMSCapabilitiesReader(version, url=url, headers=headers, auth=auth) \
        .capabilities_url(url)
    # (mss) Don't specify a version if it is to be determined
    request = request.replace("&version=None", "").replace("?version=None", "")

    base_url, _, query = request.partition("?")
    response = openURL(base_url, query, method='Get', headers=headers, auth=auth,
                       timeout=timeout, proxies=config_loader(dataset="proxies"))
    return strip_bom(response.read()), request


def WebMapService(url, version=None, xml=None, username=None, password=None,
                  parse_remote_metadata=False, headers=None, timeout=None, auth=None,
                  service_classes=None):
    """(mss) The MSS counterpart of owslib.wms.WebMapService.

    Like owslib it returns a version specific owslib service object, but on top
    of that it

      * negotiates the version with the server if none is given -- MSS talks to
        servers it knows nothing about beforehand,
      * keeps the capabilities document as `capabilities_document`, MSS shows it
        and compares it against the cached one,
      * routes the request through the proxies configured for MSS,
      * reports every dimension a layer announces, not just time and elevation,
        see `_patch_content_metadata`.

    `service_classes` maps a version to the class to instantiate, it exists so
    that mslib.msui.wms_control can add its own GetMap implementation.
    """
    if auth:
        if username:
            auth.username = username
        if password:
            auth.password = password
    else:
        auth = Authentication(username, password)

    if service_classes is None:
        service_classes = SERVICE_CLASSES
    if version is not None and version not in service_classes:
        raise NotImplementedError(
            f"The WMS version ({version}) you requested is not implemented. Please use 1.1.1 or 1.3.0.")

    request = None
    if xml is None:
        xml, request = _read_capabilities(url, version, headers=headers, auth=auth, timeout=timeout)
    elif isinstance(xml, str):
        # (mss) owslib parses with lxml, which refuses a str with an encoding declaration
        xml = xml.encode("utf-8")

    if version is None:
        version = _capabilities_version(xml)

    service = service_classes[version](
        url, version=version, xml=xml, parse_remote_metadata=parse_remote_metadata, headers=headers,
        timeout=config_loader(dataset="WMS_request_timeout") if timeout is None else timeout, auth=auth)

    # (mss) Store capabilities document.
    service.capabilities_document = xml
    if request is not None:
        # (mss) owslib only knows the request URL when it did the request itself
        service.request = request
    return service


def removeXMLNamespace(tree):
    for elem in tree.iter():
        if elem.tag.startswith("{"):
            elem.tag = elem.tag.split("}")[-1]
