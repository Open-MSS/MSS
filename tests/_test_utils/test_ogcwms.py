# -*- coding: utf-8 -*-
"""

    tests._test_utils.test_ogcwms
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests mslib.utils.ogcwms

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
import pytest

from owslib.util import ServiceException

from mslib.utils.ogcwms import DEFAULT_VERSION, WebMapService


CAPABILITIES_111 = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<WMT_MS_Capabilities version="{version}" updateSequence="17">
  <Service>
    <Name>OGC:WMS</Name>
    <Title>Mission Support System Web Map Service</Title>
    <Abstract>Service abstract</Abstract>
    <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="http://localhost:8081/"/>
    <ContactInformation>
      <ContactPersonPrimary>
        <ContactPerson>Erika Mustermann</ContactPerson>
        <ContactOrganization>MSS</ContactOrganization>
      </ContactPersonPrimary>
    </ContactInformation>
  </Service>
  <Capability>
    <Request>
      <GetCapabilities>
        <Format>application/vnd.ogc.wms_xml</Format>
        <DCPType><HTTP><Get>
          <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="http://localhost:8081/?"/>
        </Get></HTTP></DCPType>
      </GetCapabilities>
      <GetMap>
        <Format>image/png</Format>
        <DCPType><HTTP><Get>
          <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="http://localhost:8081/?"/>
        </Get></HTTP></DCPType>
      </GetMap>
    </Request>
    <Exception>
      <Format>application/vnd.ogc.se_xml</Format>
    </Exception>
    <Layer>
      <Title>Mission Support WMS Server</Title>
      <Abstract>Root layer abstract</Abstract>
      <SRS>CRS:84</SRS>
      <Layer>
        <Name>group</Name>
        <Title>A group of layers</Title>
        <Layer>
          <Name>ecmwf_EUR_LL015.PLTemp01</Name>
          <Title>Temperature (degC) and Geopotential Height (m)</Title>
          <Abstract>Layer abstract</Abstract>
          <LatLonBoundingBox minx="-180" maxx="180" miny="-90" maxy="90"/>
          <Dimension name="TIME" units="ISO8610"/>
          <Extent name="TIME">2012-10-17T12:00:00Z,2012-10-17T18:00:00Z</Extent>
          <Dimension name="INIT_TIME" units="ISO8610"/>
          <Extent name="INIT_TIME">2012-10-16T12:00:00Z</Extent>
          <Dimension name="ELEVATION" units="hPa"/>
          <Extent name="ELEVATION" default="900.0">500.0,900.0</Extent>
          <Dimension name="EMPTY" units="hPa"/>
          <Extent name="EMPTY"/>
        </Layer>
      </Layer>
    </Layer>
  </Capability>
</WMT_MS_Capabilities>
"""

CAPABILITIES_130 = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<WMS_Capabilities version="{version}" updateSequence="17" xmlns="http://www.opengis.net/wms"
                  xmlns:xlink="http://www.w3.org/1999/xlink">
  <Service>
    <Name>WMS</Name>
    <Title>Mission Support System Web Map Service</Title>
    <Abstract>Service abstract</Abstract>
    <OnlineResource xlink:href="http://localhost:8081/"/>
    <ContactInformation>
      <ContactPersonPrimary>
        <ContactPerson>Erika Mustermann</ContactPerson>
        <ContactOrganization>MSS</ContactOrganization>
      </ContactPersonPrimary>
    </ContactInformation>
  </Service>
  <Capability>
    <Request>
      <GetCapabilities>
        <Format>text/xml</Format>
        <DCPType><HTTP><Get>
          <OnlineResource xlink:href="http://localhost:8081/?"/>
        </Get></HTTP></DCPType>
      </GetCapabilities>
      <GetMap>
        <Format>image/png</Format>
        <DCPType><HTTP><Get>
          <OnlineResource xlink:href="http://localhost:8081/?"/>
        </Get></HTTP></DCPType>
      </GetMap>
    </Request>
    <Exception>
      <Format>XML</Format>
    </Exception>
    <Layer>
      <Title>Mission Support WMS Server</Title>
      <Abstract>Root layer abstract</Abstract>
      <CRS>CRS:84</CRS>
      <Layer>
        <Name>group</Name>
        <Title>A group of layers</Title>
        <Layer>
          <Name>ecmwf_EUR_LL015.PLTemp01</Name>
          <Title>Temperature (degC) and Geopotential Height (m)</Title>
          <Abstract>Layer abstract</Abstract>
          <EX_GeographicBoundingBox>
            <westBoundLongitude>-180</westBoundLongitude>
            <eastBoundLongitude>180</eastBoundLongitude>
            <southBoundLatitude>-90</southBoundLatitude>
            <northBoundLatitude>90</northBoundLatitude>
          </EX_GeographicBoundingBox>
          <Dimension name="TIME" units="ISO8610">2012-10-17T12:00:00Z,2012-10-17T18:00:00Z</Dimension>
          <Dimension name="INIT_TIME" units="ISO8610">2012-10-16T12:00:00Z</Dimension>
          <Dimension name="ELEVATION" units="hPa" default="900.0">500.0,900.0</Dimension>
          <Dimension name="EMPTY" units="hPa"/>
        </Layer>
      </Layer>
    </Layer>
  </Capability>
</WMS_Capabilities>
"""

CAPABILITIES = {"1.1.1": CAPABILITIES_111, "1.3.0": CAPABILITIES_130}

LAYER = "ecmwf_EUR_LL015.PLTemp01"


def capabilities(version, announced=None):
    """The capabilities document of `version`, announcing `announced` if given."""
    return CAPABILITIES[version].format(version=announced or version)


@pytest.fixture(params=sorted(CAPABILITIES))
def wms(request):
    """A WebMapService per supported WMS version, with the version negotiated from the document."""
    return WebMapService(None, xml=capabilities(request.param))


class TestVersionNegotiation:
    @pytest.mark.parametrize("version", sorted(CAPABILITIES))
    def test_version_taken_from_document(self, version):
        assert WebMapService(None, xml=capabilities(version)).version == version

    def test_unsupported_version_falls_back(self):
        """A server announcing a version MSS does not implement is read as the default one.

        Only pre 1.3.0 documents can be read that way, they share the 1.1.1
        layout; a namespaced document announcing an unknown version cannot be
        parsed at all.
        """
        wms = WebMapService(None, xml=capabilities("1.1.1", announced="1.1.0"))
        assert wms.version == DEFAULT_VERSION
        assert sorted(wms.contents) == [LAYER, "group"]

    @pytest.mark.parametrize("version", sorted(CAPABILITIES))
    def test_given_version_wins(self, version):
        """An explicitly requested version is not overwritten by the document."""
        wms = WebMapService(None, version=version, xml=capabilities(version, announced="1.0.0"))
        assert wms.version == version

    def test_unsupported_requested_version_raises(self):
        with pytest.raises(NotImplementedError, match="1.0.0"):
            WebMapService(None, version="1.0.0", xml=capabilities("1.1.1"))


class TestCapabilitiesDocument:
    def test_document_is_kept(self, wms):
        """The capabilities browser and the server cache read the raw document back."""
        assert wms.capabilities_document.decode("utf-8") == capabilities(wms.version)

    @pytest.mark.parametrize("version", sorted(CAPABILITIES))
    def test_document_may_be_bytes(self, version):
        """owslib parses with lxml, which only accepts an encoding declaration in bytes."""
        wms = WebMapService(None, xml=capabilities(version).encode("utf-8"))
        assert wms.version == version
        assert sorted(wms.contents) == [LAYER, "group"]


class TestServiceMetadata:
    """These come from owslib; the MSS subclass must not lose them."""

    def test_identification(self, wms):
        assert wms.identification.title == "Mission Support System Web Map Service"
        assert wms.identification.abstract == "Service abstract"
        assert wms.identification.version == wms.version

    def test_provider(self, wms):
        assert wms.provider.name == "MSS"
        assert wms.provider.url == "http://localhost:8081/"
        assert wms.provider.contact.name == "Erika Mustermann"

    def test_operations(self, wms):
        assert [operation.name for operation in wms.operations] == ["GetCapabilities", "GetMap"]
        assert wms.getOperationByName("GetMap").methods[0]["url"] == "http://localhost:8081/?"

    def test_exceptions(self, wms):
        expected = "application/vnd.ogc.se_xml" if wms.version == "1.1.1" else "XML"
        assert wms.exceptions == [expected]

    def test_update_sequence(self, wms):
        assert wms.updateSequence == "17"

    def test_service_exception_report(self):
        report = ('<?xml version="1.0"?><WMT_MS_Capabilities version="1.1.1">'
                  '<ServiceException>Nope</ServiceException></WMT_MS_Capabilities>')
        with pytest.raises(ServiceException, match="Nope"):
            WebMapService(None, xml=report)


class TestLayerMetadata:
    def test_contents(self, wms):
        """Only named layers end up in contents, the unnamed root layer does not."""
        assert sorted(wms.contents) == [LAYER, "group"]

    def test_layer_attributes(self, wms):
        """Name, title and abstract are parsed by owslib and must survive the MSS additions."""
        layer = wms.contents[LAYER]
        assert layer.name == layer.id == LAYER
        assert layer.title == "Temperature (degC) and Geopotential Height (m)"
        assert layer.abstract == "Layer abstract"
        assert layer.boundingBoxWGS84 == (-180.0, -90.0, 180.0, 90.0)

    def test_layer_tree(self, wms):
        """Group layers know their children in both versions.

        This used to be broken for 1.3.0: the MSS layer list was collected
        without the namespace and therefore always empty.
        """
        group = wms.contents["group"]
        assert [child.name for child in group.children] == [LAYER]
        assert wms.contents[LAYER].children == []
        assert wms.contents[LAYER].parent is group


class TestDimensions:
    """(mss) owslib keeps only the predefined time and elevation dimensions."""

    def test_all_dimensions_are_kept(self, wms):
        layer = wms.contents[LAYER]
        assert sorted(layer.dimensions) == ["elevation", "empty", "init_time", "time"]
        assert layer.dimensions["elevation"]["units"] == "hPa"

    def test_extent_values(self, wms):
        extents = wms.contents[LAYER].extents
        assert extents["time"]["values"] == ["2012-10-17T12:00:00Z", "2012-10-17T18:00:00Z"]
        assert extents["init_time"]["values"] == ["2012-10-16T12:00:00Z"]
        assert extents["elevation"]["values"] == ["500.0", "900.0"]
        assert extents["elevation"]["default"] == "900.0"

    def test_dimension_without_values(self, wms):
        """An announced but empty dimension must not raise."""
        assert wms.contents[LAYER].extents["empty"]["values"] == []

    def test_layer_without_dimensions(self, wms):
        group = wms.contents["group"]
        assert group.dimensions == {}
        assert group.extents == {}

    def test_dimensions_on_the_layer_tree(self, wms):
        """owslib builds `children` and `layers` as two parallel trees of distinct objects.

        MSS walks `layers` to find the selectable layers, so those need the
        dimensions as well. For 1.3.0 this tree used to be empty altogether.
        """
        layer = wms.contents["group"].layers[0]
        assert layer.name == LAYER
        assert sorted(layer.dimensions) == ["elevation", "empty", "init_time", "time"]
