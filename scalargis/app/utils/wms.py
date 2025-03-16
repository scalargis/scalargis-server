import logging
import requests
import math
import urllib.parse
from flask import current_app
from shapely import wkt
from PIL import Image
from io import BytesIO


logger = logging.getLogger(__name__)


def getmap_url(server_url, layers, bbox, width, height, geom_wkt=None, geom_srid=None, scale=None, buffer=None, opacity=1, force_local_url=False, **kwargs):
    if geom_wkt:
        center = center_map(geom_wkt)

    mapextent = calculate_bbox(scale, center[0], center[1], width, height)

    styles = ''
    if 'styles' in kwargs:
        styles = kwargs.get('styles')

    version = '1.3.0'
    if 'version' in kwargs:
        version = kwargs.get('version')

    format = 'img/png'
    if 'format' in kwargs:
        format = kwargs.get('format')

    transparent = True
    if 'transparent' in kwargs:
        transparent = kwargs.get('transparent')

    if (server_url[:7] == 'http://') or (server_url[:8] == 'https://'):
        url = server_url
    else:
        url = 'http://%s' % server_url

    if '?' not in url:
        url = url + "?"

    if force_local_url:
        url = replace_geoserver_url(url)

    url = url.replace('/gwc/service/', '/')  # for urls using GeoWebCache !

    url += 'service=WMS'
    url += '&version=%s' % version
    url += '&request=GetMap'
    url += '&layers=%s' % layers
    url += '&styles=%s' % styles
    url += '&bbox=%s,%s,%s,%s' % (mapextent[0], mapextent[1], mapextent[2], mapextent[3])
    url += '&width=%s' % int(width)
    url += '&height=%s' % int(height)
    url += '&srs=EPSG:%s' % geom_srid
    url += '&transparent=%s' % transparent
    url += '&format=%s' % format
    if 'cql_filter' in kwargs:
        url += '&cql_filter=%s' % urllib.parse.quote_plus(kwargs.get('cql_filter'))
    if 'viewparams' in kwargs:
        url += '&viewparams=%s' % kwargs.get('viewparams')

    logger.info("WMS: " + url)

    return url, mapextent


def getmap_url_by_bbox(server_url, layers, bbox, width, height, geom_wkt=None, geom_srid=None, opacity=1, force_local_url=False, **kwargs):
    styles = ''
    if 'styles' in kwargs:
        styles = kwargs.get('styles')

    version = '1.3.0'
    if 'version' in kwargs:
        version = kwargs.get('version')

    format = 'img/png'
    if 'format' in kwargs:
        format = kwargs.get('format')

    transparent = True
    if 'transparent' in kwargs:
        transparent = kwargs.get('transparent')

    if (server_url[:7] == 'http://') or (server_url[:8] == 'https://'):
        url = server_url
    else:
        url = 'http://%s' % server_url

    if '?' not in url:
        url = url + "?"

    if force_local_url:
        url = replace_geoserver_url(url)

    url = url.replace('/gwc/service/', '/')  # for urls using GeoWebCache !

    url += 'service=WMS'
    url += '&version=%s' % version
    url += '&request=GetMap'
    url += '&layers=%s' % layers
    url += '&styles=%s' % styles
    url += '&bbox=%s,%s,%s,%s' % (bbox[0], bbox[1], bbox[2], bbox[3])
    url += '&width=%s' % int(width)
    url += '&height=%s' % int(height)
    url += '&srs=EPSG:%s' % geom_srid
    url += '&transparent=%s' % transparent
    url += '&format=%s' % format
    if 'cql_filter' in kwargs:
        url += '&cql_filter=%s' % urllib.parse.quote_plus(kwargs.get('cql_filter'))
    if 'viewparams' in kwargs:
        url += '&viewparams=%s' % kwargs.get('viewparams')

    logger.info("WMS: " + url)

    return url


def getmap_image(server_url, layers, bbox, width, height, geom_wkt=None, geom_srid=None, scale=None, buffer=None, opacity=1, **kwargs):

    url = getmap_url(server_url, layers, bbox, width, height, geom_wkt, geom_srid, scale, buffer, opacity, **kwargs)

    try:
        #For performance reasons, only change alpha pixel value if opacity is lower than one (changed by user)
        if opacity == 1:
            response = requests.get(url)
            img =response.content
        else:
            img = get_image_with_opacity(url, opacity)

    except Exception as err:
        img = None
        logger.warning(err)
    return img

def get_image_with_opacity(url, opacity):
    output_img = None

    response = requests.get(url)
    imgb = Image.open(BytesIO(response.content))

    if imgb is not None:
        imgb = imgb.convert("RGBA")
        datas = imgb.getdata()
        newData = []
        for item in datas:
            alpha = int(item[3] * opacity)
            newData.append((item[0], item[1], item[2], alpha))

        imgb.putdata(newData)

    return imgb

def center_map(geom_wkt):
    if geom_wkt:
        try:
            geom = wkt.loads(geom_wkt)
            center = geom.centroid
            return [center.x, center.y]
        except Exception as err:
            logger.warning(str(err) + " :: Can't load WKT")

    return None

def calculate_bbox(scale, center_x, center_y, img_w, img_h, units='meter'):
    # INCHES_PER_UNIT_METERS = 39.37

    # pix_to_mm = 0.264583333
    # img_w = img_w * pix_to_mm
    # img_h = img_h * pix_to_mm

    magic = 25.5

    if units == 'meter':
        inch_per_units = 39.37
    elif units == 'degree':
        inch_per_units = 4374754
    else:
        # log not suported
        return None

    res = 1 / ((1 / int(scale)) * inch_per_units * magic)
    half_w = (img_w * res) / 2
    half_h = (img_h * res) / 2
    xmin = center_x - half_w
    ymin = center_y - half_h
    xmax = center_x + half_w
    ymax = center_y + half_h

    logger.debug(("BBox: " + str(xmin) + "," + str(ymin) + " - " + str(xmax) + "," + str(ymax)))

    #self.bbox = [xmin, ymin, xmax, ymax]
    #self.resolution = res
    return [xmin, ymin, xmax, ymax]


def calculate_bbox_geom(geom, img_w, img_h, dpi=90, scale_gap=100, min_scale=None, max_scale=None):
    """Calculate bbox based on geom and image size

    Parameters:
    geom (object): Geom WKT (string) or Shapely Geometry
    img_w (integer): Image width in pixels
    img_h (integer): Image height on pixels
    dpi (integer): Pixel density
    scale_gap (integer)
    min_scale (integer)
    max_scale (integer)

    Returns:
    array: Calculated bounding box

   """
    gm = None
    if isinstance(geom, str):
        try:
            gm = wkt.loads(geom)
        except Exception as err:
            logger.warning(str(err) + " :: Can't load WKT")
    else:
        gm = geom

    bbox = gm.bounds

    DPI = dpi or 90
    INCHES_PER_UNIT_CM = 0.39370
    CM_PER_INCH = 1 / INCHES_PER_UNIT_CM #2.54
    CM_PER_PIXEL = CM_PER_INCH / DPI

    img_w_cm = img_w * CM_PER_PIXEL
    img_h_cm = img_h * CM_PER_PIXEL

    dx = bbox[2] - bbox[0]
    dy = bbox[3] - bbox[1]

    scale = 5000
    res = None
    if dx / img_w_cm > dy / img_h_cm:
        res = dx / img_w_cm
        scale = (dx * 100) / img_w_cm
    else:
        res = dy / img_h_cm
        scale = (dy * 100) / img_h_cm

    scale = math.ceil((scale+ (scale_gap -1)) / scale_gap) * scale_gap

    if min_scale and scale > min_scale:
        scale = min_scale
    if max_scale and scale < max_scale:
        scale = max_scale

    centerx = bbox[0] + (dx / 2)
    centery = bbox[1] + (dy /2)

    dx = (img_w_cm * scale) / 100
    dy = (img_h_cm * scale) / 100

    minx = centerx - (dx / 2)
    miny = centery - (dy / 2)
    maxx = centerx + (dx / 2)
    maxy = centery + (dy / 2)

    return [minx, miny, maxx, maxy], scale


def calculate_scale_geom(geom, size_w, size_h, scale_gap=100, min_scale_denom=None, max_scale_denom=None,
                         geom_buffer=None, paper_buffer=None):
    """Calculate scale based on geom and paper size

    Parameters:
    geom (object): Geom WKT (string) or Shapely Geometry
    size_w (integer): paper width in cm
    size_h (integer): paper height in cm
    dpi (integer): Pixel density
    scale_gap (integer)
    min_scale_denom (integer)
    max_scale_denom (integer)
    geom_buffer (integer): geom units
    paper_buffer (num): in cm, approx.

    Returns:
    scale

   """
    gm = None
    if isinstance(geom, str):
        try:
            gm = wkt.loads(geom)
        except Exception as err:
            logger.warning(str(err) + " :: Can't load WKT")
    else:
        gm = geom

    if geom_buffer:
        gm = gm.buffer(geom_buffer)

    bbox = gm.bounds

    dx = bbox[2] - bbox[0]
    dy = bbox[3] - bbox[1]

    if paper_buffer:
        size_w = size_w - (paper_buffer * 2)
        size_h = size_h - (paper_buffer * 2)

    if dx / size_w > dy / size_h:
        scale = (dx * 100) / size_w
    else:
        scale = (dy * 100) / size_h

    scale = math.ceil((scale + (scale_gap - 1)) / scale_gap) * scale_gap

    if min_scale_denom and scale < min_scale_denom:
        scale = min_scale_denom
    if max_scale_denom and scale > max_scale_denom:
        scale = max_scale_denom

    return scale


def replace_geoserver_url(url):
    new_url = url

    try:
        if isinstance(current_app.config.get('SCALARGIS_ROUTE_GEOSERVER'), list) \
                and len(current_app.config.get('SCALARGIS_ROUTE_GEOSERVER')) > 0:
            if isinstance(current_app.config.get('SCALARGIS_ROUTE_GEOSERVER')[0], list):
                for s in current_app.config.get('SCALARGIS_ROUTE_GEOSERVER'):
                    if len(s) > 2:
                        if s[2] == 'start':
                            if new_url.startswith(s[0]):
                                new_url = new_url.replace(s[0], s[1])
                        else:
                            new_url = new_url.replace(s[0], s[1])
                    else:
                        new_url = new_url.replace(s[0], s[1])
            else:
                s = current_app.config.get('SCALARGIS_ROUTE_GEOSERVER')
                if len(s) > 2:
                    if s[2] == 'start':
                        if new_url.startswith(s[0]):
                            new_url = new_url.replace(s[0], s[1])
                        else:
                            new_url = new_url.replace(s[0], s[1])
                else:
                    new_url = new_url.replace(s[0], s[1])
        logging.info('WMS Url replace: ' + new_url)
    except AttributeError:
        logging.info('WMS Url replace: error')
        pass

    return new_url
