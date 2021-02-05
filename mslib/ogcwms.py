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
# ******************************************************************************
#
# =============================================================================

"""
API for Web Map Service (WMS) methods and metadata.

Currently supports only versions 1.1.1/1.3.0 of the WMS protocol.
"""

from future import standard_library
standard_library.install_aliases()

import defusedxml.ElementTree as etree
import requests
import logging

from owslib.util import ServiceException
from owslib.etree import ParseError
from owslib.map import wms111, wms130, common
from owslib.util import ResponseWrapper, Authentication, strip_bom
from mslib.msui import MissionSupportSystemDefaultConfig as mss_default
from mslib.utils import config_loader


def openURL(url_base, data=None, method='Get', cookies=None,
            username=None, password=None,
            timeout=config_loader(dataset="WMS_request_timeout", default=mss_default.WMS_request_timeout),
            headers=None, verify=None, cert=None, auth=None, proxies=None):
    # (mss) added proxies
    # (mss) timeout default of 30secs set by the config_loader
    """
    Function to open URLs.

    Uses requests library but with additional checks for OGC service exceptions and url formatting.
    Also handles cookies and simple user password authentication.
    """
    headers = headers if headers is not None else {}
    rkwargs = {}

    rkwargs['timeout'] = timeout

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


class WebMapService(wms111.WebMapService_1_1_1):
    """Abstraction for OGC Web Map Service (WMS).

    Implements IWebMapService.
    """

    def __init__(self, url, version='1.3.0', xml=None, username=None, password=None,
                 parse_remote_metadata=False, headers=None,
                 timeout=config_loader(dataset="WMS_request_timeout", default=mss_default.WMS_request_timeout),
                 auth=None):
        """Initialize."""
        self.WMS_NAMESPACE = "{http://www.opengis.net/wms}" if version == "1.3.0" else ""
        self.OGC_NAMESPACE = "{http://www.opengis.net/ogc}" if version == "1.3.0" else ""

        if auth:
            if username:
                auth.username = username
            if password:
                auth.password = password
        self.url = url
        self.version = version
        self.timeout = timeout
        self.headers = headers
        self._capabilities = None
        self.auth = auth or Authentication(username, password)

        # Authentication handled by Reader
        reader = WMSCapabilitiesReader(self.version, url=self.url, headers=headers, auth=self.auth)
        if xml:
            # read from stored xml
            self._capabilities = reader.readString(xml)
        else:
            # read from server
            self._capabilities = reader.read(self.url, timeout=self.timeout)

        self.request = reader.request

        # avoid building capabilities metadata if the
        # response is a ServiceExceptionReport
        se = self._capabilities.find('ServiceException')
        if se is not None:
            err_message = str(se.text).strip()
            raise ServiceException(err_message)

        # (mss) Store capabilities document.
        self.capabilities_document = reader.capabilities_document
        # (mss)

        # build metadata objects
        self._buildMetadata(parse_remote_metadata)

    def _buildMetadata(self, parse_remote_metadata=False):
        ''' set up capabilities metadata objects '''

        # serviceIdentification metadata
        serviceelem = self._capabilities.find(f'{self.WMS_NAMESPACE}Service')
        self.identification = (wms130 if self.version == "1.3.0" else wms111)\
            .ServiceIdentification(serviceelem, self.version)

        # serviceProvider metadata
        self.provider = wms130.ServiceProvider(serviceelem)

        # serviceOperations metadata
        self.operations = []
        for elem in self._capabilities.find(f'{self.WMS_NAMESPACE}Capability/{self.WMS_NAMESPACE}Request')[:]:
            self.operations.append((wms130 if self.version == "1.3.0" else wms111).OperationMetadata(elem))

        # serviceContents metadata: our assumption is that services use a top-level
        # layer as a metadata organizer, nothing more.
        self.contents = {}
        caps = self._capabilities.find(f'{self.WMS_NAMESPACE}Capability')

        def gather_layers(parent_elem, parent_metadata):
            layers = []
            for index, elem in enumerate(parent_elem.findall(f'{self.WMS_NAMESPACE}Layer')):
                cm = ContentMetadata(elem, parent=parent_metadata,
                                     index=index + 1,
                                     parse_remote_metadata=parse_remote_metadata,
                                     version=self.version)
                if cm.id:
                    if cm.id in self.contents:
                        logging.debug('Content metadata for layer "%s" already exists. Using child layer' % cm.id)
                    layers.append(cm)
                    self.contents[cm.id] = cm
                cm.children = gather_layers(elem, cm)
            return layers
        gather_layers(caps, None)

        #for elem in caps.findall(f'{self.WMS_NAMESPACE}Layer'):
        #    cm = ContentMetadata(elem, version=self.version)
        #    self.contents[cm.id] = cm
        #    for subelem in elem.findall(f'{self.WMS_NAMESPACE}Layer'):
        #        subcm = ContentMetadata(subelem, cm, version=self.version)
        #        self.contents[subcm.id] = subcm

        # exceptions
        self.exceptions = [f.text for f in self._capabilities.findall(
            f'{self.WMS_NAMESPACE}Capability/{self.WMS_NAMESPACE}Exception/{self.WMS_NAMESPACE}Format')]

    @property
    def getcapabilities(self):
        """ Request and return capabilities document from the WMS as a
            file-like object.
            NOTE: this is effectively redundant now
        """
        reader = WMSCapabilitiesReader(self.version, url=self.url, auth=self.auth)
        u = self._open(reader.capabilities_url(self.url))
        # check for service exceptions, and return
        if u.info()['Content-Type'] == 'application/vnd.ogc.se_xml':
            se_xml = u.read()
            se_tree = etree.fromstring(se_xml)
            err_message = str(se_tree.find(f'{self.OGC_NAMESPACE}ServiceException').text).strip()
            raise ServiceException(err_message, se_xml)
        return u

    def getfeatureinfo(self):
        raise NotImplementedError


def ContentMetadata(elem, parent=None, children=None, index=0,
                    parse_remote_metadata=False,
                    timeout=config_loader(dataset="WMS_request_timeout", default=mss_default.WMS_request_timeout),
                    auth=None, version="1.3.0"):
    WMS_NAMESPACE = "{http://www.opengis.net/wms}" if version == "1.3.0" else ""

    if version == "1.3.0":
        metadata = wms130.ContentMetadata(elem, parent=parent, children=children, index=index,
                                          parse_remote_metadata=parse_remote_metadata, timeout=timeout, auth=auth)
    else:
        metadata = wms111.ContentMetadata(elem, parent=parent, children=children, index=index,
                                          parse_remote_metadata=parse_remote_metadata, timeout=timeout, auth=auth)

    # (mss) Parse dimensions and their extents.
    metadata.dimensions = {}
    metadata.extents = {}
    for dim in elem.findall(f'{WMS_NAMESPACE}Dimension'):
        dimname = dim.attrib.get("name").lower()
        metadata.dimensions[dimname] = dim.attrib
        if version == "1.3.0":
            metadata.extents[dimname] = dim.attrib
            metadata.extents[dimname]["values"] = dim.text.strip().split(",")
    if version == "1.1.1":
        for extent in elem.findall(f'{WMS_NAMESPACE}Extent'):
            extname = extent.attrib.get("name").lower()
            metadata.extents[extname] = extent.attrib
            if extent.text:
                metadata.extents[extname]["values"] = extent.text.strip().split(",")
            else:
                metadata.extents[extname]["values"] = []
    # (mss)

    # (mss) Added "Abstract".
    for key in ('Name', 'Title', 'Abstract'):
        val = elem.find(WMS_NAMESPACE + key)
        # (mss) Added " and val.text is not None".
        if val is not None and val.text is not None:
            setattr(metadata, key.lower(), val.text.strip())
        else:
            setattr(metadata, key.lower(), None)
        metadata.id = metadata.name  # conform to new interface

    # (mss) Replace owslib ContentMetadata children with ogcwms ContentMetadata
    metadata.layers = []
    for child in elem.findall('Layer'):
        metadata.layers.append(ContentMetadata(child, metadata))

    return metadata


class WMSCapabilitiesReader(common.WMSCapabilitiesReader):
    """Read and parse capabilities document into a lxml.etree infoset
    """

    def __init__(self, version='1.3.0', url=None, un=None, pw=None, headers=None, auth=None):
        """Initialize"""
        super().__init__(version, url, un, pw, headers, auth)
        # (mss) Store capabilities document.
        self.capabilities_document = None
        # (mss)

    def read(self, service_url,
             timeout=config_loader(dataset="WMS_request_timeout", default=mss_default.WMS_request_timeout)):
        """Get and parse a WMS capabilities document, returning an
        elementtree instance

        service_url is the base url, to which is appended the service,
        version, and request parameters
        """
        getcaprequest = self.capabilities_url(service_url)

        proxies = config_loader(dataset="proxies", default=mss_default.proxies)

        # now split it up again to use the generic openURL function...
        spliturl = getcaprequest.split('?')
        u = openURL(spliturl[0], spliturl[1], method='Get', auth=self.auth, proxies=proxies)

        # (mss) Store capabilities document.
        self.capabilities_document = strip_bom(u.read())
        return etree.fromstring(self.capabilities_document)
        # (mss)

    def readString(self, st):
        """Parse a WMS capabilities document, returning an elementtree instance
                string should be an XML capabilities document
                """
        if not isinstance(st, str):
            raise ValueError("String must be of type string, not %s" % type(st))
        return etree.fromstring(st)


def removeXMLNamespace(tree):
    for elem in tree.iter():
        if elem.tag.startswith("{"):
            elem.tag = elem.tag.split("}")[-1]
