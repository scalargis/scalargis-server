import logging
import requests
import lxml.etree as ET
from io import BytesIO
from urllib.parse import urlparse

from flask import Blueprint, request, make_response
from flask_security import current_user
from instance import config_ows
from app.utils import http, constants
from app.utils.security import get_user_token, get_user_from_token
from app.utils.xml import XmlParser


logger = logging.getLogger(__name__)

mod = Blueprint('ows',  __name__, template_folder='templates', static_folder='static')


@mod.route('/ows/<group>/<service>', methods=['GET', 'POST'])
@http.crossdomain(origin='*')
def ows(group, service):
    request_type = None
    service_type = None
    query_args = {}

    service_config = None

    try:
        for item in config_ows.OWS_CONFIG:
            if item.get('group').lower() == group.lower() and item.get('service').lower() == service.lower():
                service_config = item
                break

        #Service not found
        if not service_config:
            return '', 404

        #Service authentication
        user = None
        if service_config.get('protected'):
            if current_user and current_user.is_authenticated:
                user = current_user
            else:
                if request.authorization and request.authorization["username"]:
                    token = get_user_token(request.authorization["username"], request.authorization["password"])
                    if token:
                        user = get_user_from_token(token)
                    else:
                        return '', 401
                else:
                    return '', 401

            user_roles = [constants.ROLE_AUTHENTICATED.lower()]
            for ru in user.roles:
                user_roles.append(ru.name.lower())

            service_roles = []
            if service_config.get('roles') == '*':
                service_roles.append(constants.ROLE_AUTHENTICATED.lower())
            else:
                for rs in service_config.get('roles'):
                    service_roles.append(rs.lower())

            if len(set(user_roles).intersection(service_roles)) == 0:
                return '', 401


        #Service type and request
        for k in request.args:
            query_args[k] = request.args.get(k)

            if k.lower() == 'request':
                request_type = request.args.get(k)
            elif k.lower() == 'service':
                service_type = request.args.get(k)

        if not (service_type and (service_config.get('type') == '*' or
                service_type.lower() in map(lambda x: x.lower(), service_config.get('type')))):
            return '', 403

        if not (request_type and (service_config.get('operation') == '*' or
                request_type.lower() in map(lambda x: x.lower(), service_config.get('operation')))):
            return '', 403

        if request_type and request_type.lower() == 'getcapabilities':
            if service_type and service_type.lower() == 'wms':
                return do_get_wms_capabilities(service_config)
            elif service_type and service_type.lower() == 'wfs':
                return do_get_wfs_capabilities(service_config)
            elif service_type and service_type.lower() == 'wcs':
                return do_get_wcs_capabilities(service_config)
            elif service_type and service_type.lower() == 'wmts':
                return do_get_wmts_capabilities(service_config)
            elif service_type and service_type.lower() == 'csw':
                return '', 501
        else:
            url = service_config.get('url')

            s = requests.Session()

            logger.info('OWS Proxy request: ' + url)

            if request.method == 'POST':
                r = s.post(url, data=request.data, params=query_args, verify=False)
            else:
                r = s.get(url, params=query_args, verify=False)

            resp = make_response(r.content)
            for h in r.headers:
                if h.lower() in ['content-type', 'content-disposition']:
                    resp.headers.set(h, r.headers.get(h))

            return resp
    except Exception as e:
        return '', 500


def do_get_wms_capabilities(config):
    url = config.get('url')

    s = requests.Session()

    params = {}

    data = request.args.to_dict()
    for key, value in data.items():
        params[key] = value

    logger.info('OWS Proxy request: ' + url)

    r = s.get(url, verify=False, params=params)
    root = ET.fromstring(r.content)

    #Get Namespaces
    nss = {}
    for n in root.nsmap:
        if n is None:
            nss['wms'] = root.nsmap[n]
        else:
            nss[n] = root.nsmap[n]

    service_version = root.get('version')

    if len(nss) > 0:
        elems = root.xpath('//wms:OnlineResource', namespaces=nss)
    else:
        elems = root.xpath('//OnlineResource')

    new_base_url = None
    new_scheme_url = urlparse(request.url).scheme
    new_hostname_url = get_ows_server_name()
    new_port_url = urlparse(request.url).port
    new_path_url = urlparse(request.url).path
    if urlparse(request.url).port:
        new_base_url = '{0}://{1}:{2}{3}'.format(new_scheme_url, new_hostname_url, new_port_url, new_path_url)
    else:
        new_base_url = '{0}://{1}{2}'.format(new_scheme_url, new_hostname_url, new_path_url)

    for elem in elems:
        xlinkns = 'http://www.w3.org/1999/xlink'
        if 'xlink' in nss:
            xlinkns = nss['xlink']

        old_url = elem.get('{0}href'.format('{' + xlinkns + '}'))
        params_url = urlparse(old_url).query

        if params_url:
            elem.set('{0}href'.format('{' + xlinkns + '}'), '{0}?{1}'.format(new_base_url, params_url))
        else:
            elem.set('{0}href'.format('{' + xlinkns + '}'), new_base_url)

    resp = get_capabilities_response(r, root)
    #resp = make_response(ET.tostring(root).decode())

    return resp


def do_get_wfs_capabilities(config):
    url = config.get('url')

    s = requests.Session()

    params = {}

    data = request.args.to_dict()
    for key, value in data.items():
        params[key] = value

    logger.info('OWS Proxy request: ' + url)

    r = s.get(url, verify=False, params=params)
    root = ET.fromstring(r.content)

    #Get Namespaces
    nss = {}
    for n in root.nsmap:
        if n is None:
            nss['wfs'] = root.nsmap[n]
        else:
            nss[n] = root.nsmap[n]

    service_version = root.get('version')

    elems = root.xpath('//ows:HTTP/*[@xlink:href]', namespaces=nss)

    new_base_url = None
    new_scheme_url = urlparse(request.url).scheme
    new_hostname_url = get_ows_server_name()
    new_port_url = urlparse(request.url).port
    new_path_url = urlparse(request.url).path
    if urlparse(request.url).port:
        new_base_url = '{0}://{1}:{2}{3}'.format(new_scheme_url, new_hostname_url, new_port_url, new_path_url)
    else:
        new_base_url = '{0}://{1}{2}'.format(new_scheme_url, new_hostname_url, new_path_url)

    for elem in elems:
        old_url = elem.get('{0}href'.format('{' + nss['xlink'] + '}'))
        params_url = urlparse(old_url).query

        if params_url:
            elem.set('{0}href'.format('{' + nss['xlink'] + '}'), '{0}?{1}'.format(new_base_url, params_url))
        else:
            elem.set('{0}href'.format('{' + nss['xlink'] + '}'), new_base_url)

    resp = get_capabilities_response(r, root)
    #resp = make_response(ET.tostring(root).decode())

    return resp


def do_get_wmts_capabilities(config):
    url = config.get('url')

    s = requests.Session()

    params = {}

    data = request.args.to_dict()
    for key, value in data.items():
        params[key] = value

    logger.info('OWS Proxy request: ' + url)

    r = s.get(url, verify=False, params=params)
    root = ET.fromstring(r.content)

    #Get Namespaces
    nss = {}
    for n in root.nsmap:
        if n is None:
            nss['wmts'] = root.nsmap[n]
        else:
            nss[n] = root.nsmap[n]

    service_version = root.get('version')

    new_base_url = None
    new_scheme_url = urlparse(request.url).scheme
    new_hostname_url = get_ows_server_name()
    new_port_url = urlparse(request.url).port
    new_path_url = urlparse(request.url).path
    if urlparse(request.url).port:
        new_base_url = '{0}://{1}:{2}{3}'.format(new_scheme_url, new_hostname_url, new_port_url, new_path_url)
    else:
        new_base_url = '{0}://{1}{2}'.format(new_scheme_url, new_hostname_url, new_path_url)

    xlinkns = 'http://www.w3.org/1999/xlink'
    if 'xlink' in nss:
        xlinkns = nss['xlink']

    elems = root.xpath('//ows:ServiceProvider/ows:ProviderName', namespaces=nss)
    for elem in elems:
        elem.text = new_base_url

    elems = root.xpath('//ows:ServiceProvider/ows:ProviderSite', namespaces=nss)
    for elem in elems:
        elem.set('{0}href'.format('{' + xlinkns + '}'), new_base_url)

    elems = root.xpath('//*[@xlink:href]', namespaces=nss)
    for elem in elems:
        old_url = elem.get('{0}href'.format('{' + xlinkns + '}'))
        params_url = urlparse(old_url).query

        if params_url:
            elem.set('{0}href'.format('{' + xlinkns + '}'), '{0}?{1}'.format(new_base_url, params_url))
        else:
            elem.set('{0}href'.format('{' + xlinkns + '}'), new_base_url)

    resp = get_capabilities_response(r, root)
    #resp = make_response(ET.tostring(root).decode())

    return resp


def do_get_wcs_capabilities(config):
    url = config.get('url')

    s = requests.Session()

    params = {}

    data = request.args.to_dict()
    for key, value in data.items():
        params[key] = value

    logger.info('OWS Proxy request: ' + url)

    r = s.get(url, verify=False, params=params)
    root = ET.fromstring(r.content)

    #Get Namespaces
    nss = {}
    for n in root.nsmap:
        nss[n] = root.nsmap[n]

    service_version = root.get('version')

    if service_version == '1.0.0':
        elems = root.xpath('//wcs:HTTP/*/wcs:OnlineResource', namespaces=nss)
    else:
        elems = root.xpath('//ows:HTTP/*[@xlink:href]', namespaces=nss)

    new_base_url = None
    new_scheme_url = urlparse(request.url).scheme
    new_hostname_url = get_ows_server_name()
    new_port_url = urlparse(request.url).port
    new_path_url = urlparse(request.url).path
    if urlparse(request.url).port:
        new_base_url = '{0}://{1}:{2}{3}'.format(new_scheme_url, new_hostname_url, new_port_url, new_path_url)
    else:
        new_base_url = '{0}://{1}{2}'.format(new_scheme_url, new_hostname_url, new_path_url)

    for elem in elems:
        old_url = elem.get('{0}href'.format('{' + nss['xlink'] + '}'))
        params_url = urlparse(old_url).query

        if params_url:
            elem.set('{0}href'.format('{' + nss['xlink'] + '}'), '{0}?{1}'.format(new_base_url, params_url))
        else:
            elem.set('{0}href'.format('{' + nss['xlink'] + '}'), new_base_url)

    resp = get_capabilities_response(r, root)
    #resp = make_response(ET.tostring(root).decode())

    return resp


def get_capabilities_response(response, output_element):
    parser = XmlParser()
    parser.parse(response.content)
    encoding = parser.get_encoding()
    version = parser.get_version()
    standalone = parser.get_standalone()

    ret_val = make_response(ET.tostring(output_element, encoding=encoding, standalone=standalone,
                            xml_declaration=True,
                            pretty_print=True))
                            #,doctype='<!DOCTYPE tmx SYSTEM "tmx14a.dtd">'))

    for h in response.headers:
        if h.lower() in ['content-type', 'content-disposition']:
            ret_val.headers.set(h, response.headers.get(h))


    return ret_val


def get_ows_server_name():
    return config_ows.OWS_SERVER_NAME or urlparse(request.url).hostname
