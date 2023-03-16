import requests
from enum import Enum
import lxml.etree as ET


class EnumGroup(Enum):
    Group = -1
    Intranet = 0
    All = 3


class EnumOperation(Enum):
    View = 0
    Download = 1
    Editing = 2
    Notify = 3
    Interactive = 5
    Featured = 6


class EnumElementSetName(Enum):
    summary = 0
    brief = 1
    full = 2


class EnumSpatialOperator(Enum):
    BBOX = 0
    Equals = 1
    Overlaps = 2
    Disjoint = 3
    Intersects = 4
    Touches = 5
    Crosses = 6
    Within = 7
    Contains = 8


class EnumLogicalOperator(Enum):
    EqualTo = 0
    Like = 1
    LessThan = 2
    GreaterThan = 3
    LessThanOrEqualTo = 4
    GreaterThanOrEqualTo = 5
    NotEqualTo = 6
    Between = 7
    NullCheck = 8


class Service:

    def __init__(self, url=None, username=None, password=None):
        self.__server_url = url
        self.__session_container = None

        if username is not None:
            self.__session_container = self.__login_csw_service(username, password)

    def __login_csw_service(self, username, password):
        return ['sds','sdsd']

    def login(self, username, password):
        self.__session_container = self.__login_csw_service()

        return True

    def logout(self):
        self.__session_container = None

        return False

    def search_metadata(self, service_id, any_text, keywords, resource_type,
        service_type, topic_category, inspire_themes, begin_date, end_date, spatial_operator,
        geographic_extent, elementset_name, start_position, max_records, sort_order):

        result = None
        xml_filter = None

        lines = []

        lines.append("<csw:GetRecords xmlns:csw='http://www.opengis.net/cat/csw/2.0.2' xmlns:gmd='http://www.isotc211.org/2005/gmd' service='CSW' version='2.0.2' resultType='results' outputSchema='http://www.isotc211.org/2005/gmd' startPosition='{0}' maxRecords='{1}'>".format(start_position, max_records))
        lines.append("<csw:Query typeNames='gmd:MD_Metadata'  xmlns:ogc='http://www.opengis.net/ogc' xmlns:gml='http://www.opengis.net/gml'>")
        lines.append("<csw:ElementSetName>{0}</csw:ElementSetName>".format(elementset_name.name))
        lines.append("<csw:Constraint version='1.1.0'>")
        lines.append("<ogc:Filter xmlns='http://www.opengis.net/ogc'>")

        # Build Filter
        lines_filter = []

        if any_text and not any_text.isspace():
            aux_xml = self.build_property_filter("AnyText", any_text)
            if aux_xml and not aux_xml.isspace():
                lines_filter.append(aux_xml)

        if keywords and not keywords.isspace():
            aux_xml = self.build_property_filter("keyword", keywords.strip().replace(" ", "_"))
            if aux_xml and not aux_xml.isspace():
                lines_filter.append(aux_xml)

        if resource_type and not resource_type.isspace():
            aux_xml = self.build_property_filter("type", resource_type.strip())
            if aux_xml and not aux_xml.isspace():
                lines_filter.append(aux_xml)

        if service_type and not service_type.isspace():
            aux_xml = self.build_property_filter("serviceType", service_type.strip())
            if aux_xml and not aux_xml.isspace():
                lines_filter.append(aux_xml)

        if topic_category and not topic_category.isspace():
            aux_xml = self.build_property_filter("topicCat", topic_category.strip())
            if aux_xml and not aux_xml.isspace():
                lines_filter.append(aux_xml)

        if inspire_themes and not inspire_themes.isspace():
            aux_xml = self.build_property_filter("keyword", inspire_themes.strip().replace(" ", "_"))
            if aux_xml and not aux_xml.isspace():
                lines_filter.append(aux_xml)

        if spatial_operator and (geographic_extent and not geographic_extent.isspace()):
            aux_xml = self.build_boundingbox_filter(spatial_operator.name, geographic_extent)
            if aux_xml and not aux_xml.isspace():
                lines_filter.append(aux_xml)

        if begin_date or end_date:
            aux_xml = self.build_temporal_filter(begin_date, end_date)
            if aux_xml and not aux_xml.isspace():
                lines_filter.append(aux_xml)

        xml_filter = "".join(lines_filter)

        if xml_filter and not xml_filter.isspace():
            if len(lines_filter) > 1:
                lines.append("<ogc:And>")
                lines.append(xml_filter)
                lines.append("</ogc:And>")
            else:
                lines.append(xml_filter)

        # End Build Filter

        lines.append("</ogc:Filter>")
        lines.append("</csw:Constraint>")
        lines.append("</csw:Query>")
        lines.append("</csw:GetRecords>")

        xml = "".join(lines)

        response = self.do_post_request(self.__server_url, xml.encode('utf8'))
        xml_root = ET.fromstring(response.encode('utf8'))

        nsmap = {'csw': 'http://www.opengis.net/cat/csw/2.0.2'}
        results = xml_root.xpath('//csw:SearchResults | //SearchResults', namespaces=nsmap)

        total = int(results[0].attrib.get("numberOfRecordsMatched"))
        next_record = int(results[0].attrib.get("nextRecord"))

        result = [response, total, next_record]

        return result

    def search_geoportal_metadata(self, service_id, any_text, resource_type,
        topic_category, begin_date, end_date, spatial_operator, geographic_extent,
        elementset_name, start_position, max_records, sort_order):

        result = None
        xml_filter = None

        lines = []

        lines.append("<csw:GetRecords xmlns:csw='http://www.opengis.net/cat/csw/2.0.2' version='2.0.2' service='CSW' resultType='results' startPosition='{0}' maxRecords='{1}'>".format(start_position, max_records))
        lines.append("<csw:Query typeNames='csw:Record'  xmlns:ogc='http://www.opengis.net/ogc' xmlns:gml='http://www.opengis.net/gml'>")
        lines.append("<csw:ElementSetName>{0}</csw:ElementSetName>".format(elementset_name.name))
        lines.append("<csw:Constraint version='1.1.0'>")
        lines.append("<ogc:Filter>")

        # Build Filter
        lines_filter = []

        if any_text and not any_text.isspace():
            aux_xml = self.build_property_filter("AnyText", any_text)
            if aux_xml and not aux_xml.isspace():
                lines_filter.append(aux_xml)

        if resource_type and not resource_type.isspace():
            aux_xml = self.build_property_filter("type", resource_type.strip())
            if aux_xml and not aux_xml.isspace():
                lines_filter.append(aux_xml)

        if topic_category and not topic_category.isspace():
            aux_xml = self.build_property_filter("subject", topic_category.strip())
            if aux_xml and not aux_xml.isspace():
                lines_filter.append(aux_xml)

        if spatial_operator and (geographic_extent and not geographic_extent.isspace()):
            aux_xml = self.build_boundingbox_filter(spatial_operator.name, geographic_extent)
            if aux_xml and not aux_xml.isspace():
                lines_filter.append(aux_xml)

        if begin_date or end_date:
            aux_xml = self.build_temporal_filter(begin_date, end_date)
            if aux_xml and not aux_xml.isspace():
                lines_filter.append(aux_xml)

        xml_filter = "".join(lines_filter)

        if xml_filter and not xml_filter.isspace():
            if len(lines_filter) > 1:
                lines.append("<ogc:And>")
                lines.append(xml_filter)
                lines.append("</ogc:And>")
            else:
                lines.append(xml_filter)

        # End Build Filter

        lines.append("</ogc:Filter>")
        lines.append("</csw:Constraint>")
        lines.append("</csw:Query>")
        lines.append("</csw:GetRecords>")

        xml = "".join(lines)

        response = self.do_post_request(self.__server_url, xml.encode('utf8'))
        xml_root = ET.fromstring(response.encode('utf8'))

        nsmap = {'csw': 'http://www.opengis.net/cat/csw/2.0.2'}
        results = xml_root.xpath('//csw:SearchResults | //SearchResults', namespaces=nsmap)

        total = int(results[0].attrib.get("numberOfRecordsMatched"))
        next_record = int(results[0].attrib.get("nextRecord"))

        result = [response, total, next_record]

        return result

    def do_show_metadata_xml(self, uuid):
        result = None
        xml = None

        lines = []

        lines.append("<csw:GetRecordById xmlns:csw=\"http://www.opengis.net/cat/csw/2.0.2\" service=\"CSW\" version=\"2.0.2\" outputSchema=\"csw:IsoRecord\">")
        lines.append("<csw:ElementSetName>full</csw:ElementSetName>")
        lines.append("<csw:Id>" + uuid + "</csw:Id>")
        lines.append("</csw:GetRecordById>")

        xml = "".join(lines)

        response = self.do_post_request(self.__server_url, xml)

        return response

    def do_post_request(self, url, xml):
        response = None

        headers = {'Content-Type': 'application/xml'}  # set what your server accepts
        response = requests.post(url, data=xml, headers=headers).text

        return response

    def build_property_filter(self, property_name, values):
        lines = []
        xml = None
        kw = values.split(';')

        for val in kw:
            lines.append("<ogc:PropertyIsLike matchCase='false' wildCard='%' singleChar='_' escapeChar='\'>")
            lines.append("<ogc:PropertyName>{0}</ogc:PropertyName>".format(property_name))
            lines.append("<ogc:Literal>%{0}%</ogc:Literal>".format(val.strip()))
            lines.append("</ogc:PropertyIsLike>")

        xml = "".join(lines)

        return xml

    def build_boundingbox_filter(self, spatial_operator, geographic_extent):
        lines = []
        xml = None
        extent = geographic_extent.split(" ")
        operator = spatial_operator

        if spatial_operator == "within":
            operator = "Within"
        elif spatial_operator == "intersects":
            operator = "Intersects"

        lines.append("<ogc:{0}>".format(operator))
        lines.append("<ogc:PropertyName>ows:BoundingBox</ogc:PropertyName>")
        lines.append("<gml:Envelope xmlns:gml='http://www.opengis.net/gml'>")
        lines.append("<gml:lowerCorner>{0} {1}</gml:lowerCorner>".format(extent[0], extent[1]))
        lines.append("<gml:upperCorner>{0} {1}</gml:upperCorner>".format(extent[2], extent[3]))
        lines.append("</gml:Envelope>")
        lines.append("</ogc:{0}>".format(operator))

        xml = "".join(lines)

        return xml

    def build_temporal_filter(self, begin_date, end_date):
        lines = []
        xml = None

        lines.append("<ogc:And>")
        if begin_date:
            lines.append("<ogc:PropertyIs{0}>".format(EnumLogicalOperator.GreaterThanOrEqualTo.name))
            lines.append("<ogc:PropertyName>TempExtent_begin</ogc:PropertyName>")
            lines.append("<ogc:Literal>{0}</ogc:Literal>".format(begin_date.strftime('%Y-%m-%d')))
            lines.append("</ogc:PropertyIs{0}>".format(EnumLogicalOperator.GreaterThanOrEqualTo.name))
        if end_date:
            lines.append("<ogc:PropertyIs{0}>".format(EnumLogicalOperator.LessThanOrEqualTo.name))
            lines.append("<ogc:PropertyName>TempExtent_end</ogc:PropertyName>")
            lines.append("<ogc:Literal>{0}</ogc:Literal>".format(end_date.strftime('%Y-%m-%d')))
            lines.append("</ogc:PropertyIs{0}>".format(EnumLogicalOperator.LessThanOrEqualTo.name))
        lines.append("</ogc:And>")

        xml = "".join(lines)

        return xml
