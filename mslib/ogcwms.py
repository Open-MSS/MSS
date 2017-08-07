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

Currently supports only version 1.1.1 of the WMS protocol.
"""

from future import standard_library
standard_library.install_aliases()

import cgi
import xml.etree.ElementTree as etree
import requests
import logging

from urllib.parse import urlencode
from owslib.util import ServiceException
from collections import OrderedDict
from owslib.etree import ParseError
from owslib.map import wms111
from owslib.util import ResponseWrapper
from mslib.msui import MissionSupportSystemDefaultConfig as mss_default
from mslib.utils import config_loader


def openURL(url_base, data=None, method='Get', cookies=None,
            username=None, password=None, timeout=30, headers=None, proxies=None):
    # (mss) added proxies
    """
    Function to open URLs.

    Uses requests library but with additional checks for OGC service exceptions and url formatting.
    Also handles cookies and simple user password authentication.
    """
    headers = headers if headers is not None else {}
    rkwargs = {}

    rkwargs['timeout'] = timeout

    auth = None
    if username and password:
        auth = (username, password)

    rkwargs['auth'] = auth

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
            pass

        rkwargs['data'] = data

    elif method.lower() == 'get':
        rkwargs['params'] = data

    else:
        raise ValueError("Unknown method ('{}'), expected 'get' or 'post'".format(method))

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
                    '\n'.join([str(t).strip() for t in serviceException.itertext() if str(t).strip()]))

    return ResponseWrapper(req)


class WebMapService(object):
    """Abstraction for OGC Web Map Service (WMS).

    Implements IWebMapService.
    """

    def __getitem__(self, name):
        ''' check contents dictionary to allow dict like access to service layers'''
        if name in list(self.__getattribute__('contents').keys()):
            return self.__getattribute__('contents')[name]
        else:
            raise KeyError("No content named %s" % name)

    def __init__(self, url, version='1.1.1', xml=None, username=None, password=None):
        """Initialize."""
        self.url = url
        self.username = username
        self.password = password
        self.version = version
        self._capabilities = None

        # Authentication handled by Reader
        reader = WMSCapabilitiesReader(self.version, url=self.url, un=self.username, pw=self.password)
        if xml:
            # read from stored xml
            self._capabilities = reader.readString(xml)
        else:
            # read from server
            self._capabilities = reader.read(self.url)

        # (mss) Store capabilities document.
        self.capabilities_document = reader.capabilities_document
        # (mss)

        # build metadata objects
        self._buildMetadata()

    def _getcapproperty(self):
        if not self._capabilities:
            reader = WMSCapabilitiesReader(self.version, url=self.url, un=self.username, pw=self.password)
            self._capabilities = wms111.ServiceMetadata(reader.read(self.url))
            # (mss) Store capabilities document.
            self.capabilities_document = reader.capabilities_document
            # (mss)
        return self._capabilities

    def _buildMetadata(self):
        ''' set up capabilities metadata objects '''

        # serviceIdentification metadata
        serviceelem = self._capabilities.find('Service')
        self.identification = ServiceIdentification(serviceelem, self.version)

        # serviceProvider metadata
        self.provider = wms111.ServiceProvider(serviceelem)

        # serviceOperations metadata
        self.operations = []
        for elem in self._capabilities.find('Capability/Request')[:]:
            self.operations.append(wms111.OperationMetadata(elem))

        # serviceContents metadata: our assumption is that services use a top-level
        # layer as a metadata organizer, nothing more.
        self.contents = {}
        caps = self._capabilities.find('Capability')
        for elem in caps.findall('Layer'):
            cm = ContentMetadata(elem)
            self.contents[cm.id] = cm
            for subelem in elem.findall('Layer'):
                subcm = ContentMetadata(subelem, cm)
                self.contents[subcm.id] = subcm

        # exceptions
        self.exceptions = [f.text for f in self._capabilities.findall('Capability/Exception/Format')]

    def items(self):
        '''supports dict-like items() access'''
        items = []
        for item in self.contents:
            items.append((item, self.contents[item]))
        return items

    @property
    def getcapabilities(self):
        """ Request and return capabilities document from the WMS as a
            file-like object.
            NOTE: this is effectively redundant now
        """
        reader = WMSCapabilitiesReader(self.version, url=self.url, un=self.username, pw=self.password)
        u = self._open(reader.capabilities_url(self.url))
        # check for service exceptions, and return
        if u.info().gettype() == 'application/vnd.ogc.se_xml':
            se_xml = u.read()
            se_tree = etree.fromstring(se_xml)
            err_message = str(se_tree.find('ServiceException').text).strip()
            raise ServiceException(err_message, se_xml)
        return u

    def getmap(self, layers=None, styles=None, srs=None, bbox=None,
               format=None, size=None, time=None, transparent=False,
               bgcolor='#FFFFFF',
               exceptions='application/vnd.ogc.se_xml',
               method='Get'
               ):
        """Request and return an image from the WMS as a file-like object.

        Parameters
        ----------
        layers : list
            List of content layer names.
        styles : list
            Optional list of named styles, must be the same length as the
            layers list.
        srs : string
            A spatial reference system identifier.
        bbox : tuple
            (left, bottom, right, top) in srs units.
        format : string
            Output image format such as 'image/jpeg'.
        size : tuple
            (width, height) in pixels.
        transparent : bool
            Optional. Transparent background if True.
        bgcolor : string
            Optional. Image background color.
        method : string
            Optional. HTTP DCP method name: Get or Post.

        Example
        -------
            >>> img = wms.getmap(layers=['global_mosaic'],
            ...                  styles=['visual'],
            ...                  srs='EPSG:4326',
            ...                  bbox=(-112,36,-106,41),
            ...                  format='image/jpeg',
            ...                  size=(300,250),
            ...                  transparent=True,
            ...                  )
            >>> out = open('example.jpg', 'wb')
            >>> out.write(img.read())
            >>> out.close()

        """
        base_url = self.getOperationByName('GetMap').methods[method]['url']
        request = {'version': self.version, 'request': 'GetMap'}

        # check layers and styles
        assert len(layers) > 0
        request['layers'] = ','.join(layers)
        if styles:
            assert len(styles) == len(layers)
            request['styles'] = ','.join(styles)
        else:
            request['styles'] = ''

        # size
        request['width'] = str(size[0])
        request['height'] = str(size[1])

        request['srs'] = str(srs)
        request['bbox'] = ','.join([str(x) for x in bbox])
        request['format'] = str(format)
        request['transparent'] = str(transparent).upper()
        request['bgcolor'] = '0x' + bgcolor[1:7]
        request['exceptions'] = str(exceptions)

        if time is not None:
            request['time'] = str(time)

        data = urlencode(request)
        proxies = config_loader(dataset="proxies", default=mss_default.proxies)
        u = openURL(base_url, data, method, username=self.username, password=self.password, proxies=proxies)

        # check for service exceptions, and return
        if u.info()['Content-Type'] == 'application/vnd.ogc.se_xml':
            se_xml = u.read()
            se_tree = etree.fromstring(se_xml)
            err_message = str(se_tree.find('ServiceException').text).strip()
            raise ServiceException(err_message, se_xml)
        return u

    def getServiceXML(self):
        xml = None
        if self._capabilities:
            xml = etree.tostring(self._capabilities)
        return xml

    def getfeatureinfo(self):
        raise NotImplementedError

    def getOperationByName(self, name):
        """Return a named content item."""
        for item in self.operations:
            if item.name == name:
                return item
        raise KeyError("No operation named %s" % name)


class ServiceIdentification(object):
    ''' Implements IServiceIdentificationMetadata '''

    def __init__(self, infoset, version):
        self._root = infoset
        self.type = self._root.find('Name').text
        self.version = version
        self.title = self._root.find('Title').text
        abstract = self._root.find('Abstract')
        if abstract is not None:
            self.abstract = abstract.text
        else:
            self.abstract = None
        self.keywords = [f.text for f in self._root.findall('KeywordList/Keyword')]
        accessconstraints = self._root.find('AccessConstraints')
        if accessconstraints is not None:
            self.accessconstraints = accessconstraints.text
        fees = self._root.find('Fees')
        if fees is not None:
            self.fees = fees.text
        # (mss) Always set a default value similar to abstract.
        else:
            self.fees = None
        # (mss)


class ContentMetadata(object):
    """
    Abstraction for WMS layer metadata.

    Implements IContentMetadata.
    """
    def __init__(self, elem, parent=None):
        self.parent = parent
        if elem.tag != 'Layer':
            raise ValueError('%s should be a Layer' % (elem,))
        # (mss) Added "Abstract".
        for key in ('Name', 'Title', 'Abstract'):
            val = elem.find(key)
            # (mss) Added " and val.text is not None".
            if val is not None and val.text is not None:
                setattr(self, key.lower(), val.text.strip())
            else:
                setattr(self, key.lower(), None)
            self.id = self.name  # conform to new interface
        # bboxes
        b = elem.find('BoundingBox')
        self.boundingBox = None
        if b is not None:
            try:  # sometimes the SRS attribute is (wrongly) not provided
                srs = b.attrib['SRS']
            except KeyError:
                srs = None
                self.boundingBox = (
                    float(b.attrib['minx']),
                    float(b.attrib['miny']),
                    float(b.attrib['maxx']),
                    float(b.attrib['maxy']),
                    srs,
                )
        elif self.parent:
            if hasattr(self.parent, 'boundingBox'):
                self.boundingBox = self.parent.boundingBox

        attribution = elem.find('Attribution')
        if attribution is not None:
            self.attribution = dict()
            title = attribution.find('Title')
            url = attribution.find('OnlineResource')
            logo = attribution.find('LogoURL')
            if title is not None:
                self.attribution['title'] = title.text
            if url is not None:
                self.attribution['url'] = url.attrib['{http://www.w3.org/1999/xlink}href']
            if logo is not None:
                self.attribution['logo_size'] = (int(logo.attrib['width']), int(logo.attrib['height']))
                self.attribution['logo_url'] = logo.find('OnlineResource').attrib['{http://www.w3.org/1999/xlink}href']

        b = elem.find('LatLonBoundingBox')
        if b is not None:
            self.boundingBoxWGS84 = (
                float(b.attrib['minx']),
                float(b.attrib['miny']),
                float(b.attrib['maxx']),
                float(b.attrib['maxy']),
            )
        elif self.parent:
            self.boundingBoxWGS84 = self.parent.boundingBoxWGS84
        else:
            self.boundingBoxWGS84 = None

        # SRS options
        self.crsOptions = []

        # Copy any parent SRS options (they are inheritable properties)
        if self.parent:
            # (mss) Copy parent SRS only if it has been defined (some WMS do not!).
            if self.parent.crsOptions:
                self.crsOptions = list(self.parent.crsOptions)

        # Look for SRS option attached to this layer
        if elem.find('SRS') is not None:
            # some servers found in the wild use a single SRS
            # tag containing a whitespace separated list of SRIDs
            # instead of several SRS tags. hence the inner loop
            for srslist in [x.text for x in elem.findall('SRS')]:
                if srslist:
                    for srs in srslist.split():
                        self.crsOptions.append(srs)

        # Get rid of duplicate entries
        self.crsOptions = list(set(self.crsOptions))

        # Set self.crsOptions to None if the layer (and parents) had no SRS options
        if len(self.crsOptions) == 0:
            # raise ValueError('%s no SRS available!?' % (elem,))
            # Comment by D Lowe.
            # Do not raise ValueError as it is possible that a layer is purely
            # a parent layer and does not have SRS specified. Instead set crsOptions to None
            self.crsOptions = None

        # Styles
        self.styles = OrderedDict()

        # Copy any parent styles (they are inheritable properties)
        if self.parent:
            self.styles = self.parent.styles.copy()

        # Get the styles for this layer (items with the same name are replaced)
        for s in elem.findall('Style'):

            name = s.find('Name')
            title = s.find('Title')
            if name is None or title is None:
                raise ValueError('%s missing name or title' % (s,))
                #             style = { 'title' : title.text }
                #             # legend url
                #             legend = s.find('LegendURL/OnlineResource')
                #             if legend is not None:
                #                 style['legend'] = legend.attrib['{http://www.w3.org/1999/xlink}href']
                #             self.styles[name.text] = style
                #            # (mss) fixed style strip() problem.
            else:
                style_name = name.text.strip() if type(name.text) is str else name.text
                style_title = title.text.strip() if type(title.text) is str else title.text
            style = {'title': style_title}
            legend = s.find('LegendURL/OnlineResource')
            if legend is not None:
                style['legend'] = legend.attrib['{http://www.w3.org/1999/xlink}href']
            self.styles[style_name] = style
            # (mss)

        # keywords
        self.keywords = [f.text for f in elem.findall('KeywordList/Keyword')]

        # timepositions - times for which data is available.
        self.timepositions = None
        for extent in elem.findall('Extent'):
            if extent.attrib.get("name").lower() == 'time':
                # (mss) inserted test for text attribute, as extent tags don't
                # have to contain text.
                if extent.text is not None:
                    self.timepositions = extent.text.split(',')
                    break

        # (mss) Parse dimensions and their extents.
        self.dimensions = {}
        self.extents = {}
        for dim in elem.findall('Dimension'):
            dimname = dim.attrib.get("name").lower()
            self.dimensions[dimname] = dim.attrib
        for extent in elem.findall('Extent'):
            extname = extent.attrib.get("name").lower()
            self.extents[extname] = extent.attrib
            if extent.text is not None:
                self.extents[extname]["values"] = extent.text.strip().split(",")
            else:
                self.extents[extname]["values"] = []
        # (mss)

        self.layers = []
        for child in elem.findall('Layer'):
            self.layers.append(ContentMetadata(child, self))

    def __str__(self):
        return 'Layer Name: %s Title: %s' % (self.name, self.title)


class WMSCapabilitiesReader(object):
    """Read and parse capabilities document into a lxml.etree infoset
    """

    def __init__(self, version='1.1.1', url=None, un=None, pw=None):
        """Initialize"""
        self.version = version
        self._infoset = None
        self.url = url
        self.username = un
        self.password = pw
        # (mss) Store capabilities document.
        self.capabilities_document = None
        # (mss)
        """
        # if self.username and self.password:
            # Provide login information in order to use the WMS server
            # Create an OpenerDirector with support for Basic HTTP
            # Authentication...
            # passman = HTTPPasswordMgrWithDefaultRealm()
            # passman.add_password(None, self.url, self.username, self.password)
            # auth_handler = HTTPBasicAuthHandler(passman)
            # opener = build_opener(auth_handler)
            # self._open = opener.open
        """
    def capabilities_url(self, service_url):
        """Return a capabilities url
        """
        qs = []
        if service_url.find('?') != -1:
            qs = cgi.parse_qsl(service_url.split('?')[1])

        params = [x[0] for x in qs]

        if 'service' not in params:
            qs.append(('service', 'WMS'))
        if 'request' not in params:
            qs.append(('request', 'GetCapabilities'))
        if 'version' not in params:
            qs.append(('version', self.version))

        urlqs = urlencode(tuple(qs))
        return service_url.split('?')[0] + '?' + urlqs

    def read(self, service_url):
        """Get and parse a WMS capabilities document, returning an
        elementtree instance

        service_url is the base url, to which is appended the service,
        version, and request parameters
        """
        getcaprequest = self.capabilities_url(service_url)

        proxies = config_loader(dataset="proxies", default=mss_default.proxies)

        # now split it up again to use the generic openURL function...
        spliturl = getcaprequest.split('?')
        u = openURL(spliturl[0], spliturl[1], method='Get',
                    username=self.username, password=self.password, proxies=proxies)
        # (mss) Store capabilities document.
        self.capabilities_document = u.read()
        return etree.fromstring(self.capabilities_document)
        # (mss)

    def readString(self, st):
        """Parse a WMS capabilities document, returning an elementtree instance

        string should be an XML capabilities document
        """
        if not isinstance(st, str):
            raise ValueError("String must be of type string, not %s" % type(st))
        return etree.fromstring(st)
