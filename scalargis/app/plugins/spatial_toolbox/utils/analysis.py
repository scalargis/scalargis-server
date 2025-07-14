import logging
import os
import json
from collections import OrderedDict
import uuid
import base64
import io
from flask import redirect, url_for, send_file, make_response, render_template, render_template_string
from flask_restx import abort
from sqlalchemy import text
from pyexcel_xls import save_data as save_xls
from pyexcel_io import save_data as save_csv
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, inch
from xhtml2pdf import pisa
from PIL import Image as PILImage
import fitz
from shapely import wkt, geometry

from app.database import db
from app.database.schema import db_schema
from instance import settings
from app.utils.settings import get_config_value
from app.utils.geo import getGeometryFromWKT, transformGeom
from app.utils.wms import (replace_geoserver_url, calculate_bbox, calculate_bbox_geom, center_map, getmap_image,
                           get_image_with_opacity, getmap_url, getmap_url_by_bbox)


logger = logging.getLogger(__name__)


def get_intersect_results(config_code, geom_wkt, geom_srid, buffer, buffer_srid, out_srid):

    iewkt = "SRID={0};{1}".format(geom_srid or 4326, geom_wkt)
    outsrid = out_srid or 4326
    ibuffer = buffer or 0
    ibuffer_srid = buffer_srid or 3857

    # get layers def
    sql = "select * from {0}.site_settings where code like '{1}'".format(db_schema, config_code or 'config_intersect')
    result = db.session.execute(text(sql)).fetchall()
    layers = []
    if len(result) > 0:
        layers = result[0].setting_value

    # parse confrontation config to json object
    json_cfg = json.loads(layers)

    sql = "select * from {0}.intersects_layers(:layers, :ewkt, :outsrid, :buffer, :buffer_srid)".format(db_schema)
    params = {"layers": layers, "ewkt": iewkt, "outsrid": outsrid, "buffer": ibuffer, "buffer_srid": ibuffer_srid}
    result = db.session.execute(text(sql), params).fetchall()
    record = None
    if len(result) > 0:
        record = result[0].intersects_layers

    # Filter empty layers
    record_filtered = OrderedDict()
    record_filtered['groups'] = record.get('groups', [])
    record_filtered['layers'] = []
    record_filtered['output_geom'] = record['output_geom']

    for row in record['layers']:
        if len(row['results']):
            record_filtered['layers'].append(row)

    if 'title' in json_cfg:
        record_filtered['title'] = json_cfg['title']

    if 'description' in json_cfg:
        record_filtered['description'] = json_cfg['description']

    if 'pdf_template' in json_cfg:
        record_filtered['pdf_template'] = json_cfg['pdf_template']

    if 'pdf_template_code' in json_cfg:
        record_filtered['pdf_template_code'] = json_cfg['pdf_template_code']

    if 'maps' in json_cfg:
        record_filtered['maps'] = json_cfg['maps']

    return record_filtered


def export_intersect_results(record, out_format):

    # Build tabular data
    data = OrderedDict()

    if 'description' in record:
        data['Descricao'] = []
        data['Descricao'].append([record['description']])

    data['Resultados'] = []
    data['Resultados'].append(['Grupo', 'Título', 'Área', 'Comprimento', '%', 'Campos'])
    for row in record['layers']:
        records = []
        group = row['title_alias'].replace(" ", "") if row.get('title_alias') else row['title'].replace(" ", "")
        column_names = ['Grupo', 'Título']
        column_names.append('Área')
        column_names.append('Comprimento')
        column_names.append('%')

        for field in row['fields']:
            column_names.append(field['alias'])

        records.append(column_names)

        for item in row['results']:
            l = []
            l.append(row['group'])
            l.append(row['title'])
            l.append(round(item['area'], 3))
            l.append(round(item['length'], 3))
            l.append(round(item['percent'], 3))
            for field in row['fields']:
                l.append(item[field['field']])
            records.append(l)

            # Build main result
            rl = []
            rl.append(row['group'])
            rl.append(row['title'])
            rl.append(round(item['area'], 3))
            rl.append(round(item['length'], 3))
            rl.append(round(item['percent'], 3))

            # Build row summary
            summary = []
            joiner = " | "
            if 'fields_report' in row:
                for rfield in row['fields_report']:
                    summary.append(item[rfield])
            else:
                for rfield in row['fields']:
                    summary.append(item[rfield['field']])

            rl.append(joiner.join(str(elem) for elem in summary))
            data['Resultados'].append(rl)

        data[group] = records

    # Default filename
    file_name = "intersect_layers"

    # Send PDF file
    if out_format == 'pdf':
        outfile = file_name + ".pdf"
        file_name = "{0}-{1}.{2}".format(file_name, uuid.uuid4(), out_format)
        filename = os.path.join(settings.APP_TMP_DIR, file_name)
        if os.path.exists(filename):
            os.remove(filename)

        if create_pdf_intersect_results(record, filename):
            return send_file(filename, download_name=outfile)
        else:
            abort(500, custom='value')

    # Send XLS file
    elif out_format == 'xls':
        outfile = file_name + ".xls"
        file_name = "{0}-{1}.{2}".format(file_name, uuid.uuid4(), out_format)
        filename = os.path.join(settings.APP_TMP_DIR, file_name)
        if os.path.exists(filename):
            os.remove(filename)
        save_xls(filename, data)
        return send_file(filename, download_name=outfile)
    # Send CSV file
    else:
        outfile = file_name + ".zip"
        filename = os.path.join(settings.APP_TMP_DIR, file_name + ".csvz")
        if os.path.exists(filename):
            os.remove(filename)
        save_csv(filename, data)
        if os.path.exists(os.path.join(settings.APP_TMP_DIR, outfile)):
            os.remove(os.path.join(settings.APP_TMP_DIR, outfile))

        return send_file(filename, download_name=outfile)

def create_pdf_intersect_results(record, filename):
    # enable logging
    pisa.showLogging()

    template_file = record.get('pdf_template', 'intersect_pdf_report.html')

    output_geom = record.get('output_geom', None)

    if output_geom:
        maps = record.get('maps', [])

        for map in maps:
            img_str, img_width, img_height, bbox, scale = create_map_image(output_geom, map)
            if img_str:
                map_id = map.get('id', 'map')
                record[f'{map_id}_source'] = 'data:image/png;base64, {0}'.format(img_str)
                record[f'{map_id}_width'] = img_width
                record[f'{map_id}_height'] = img_height
                record[f'{map_id}_extent'] = bbox
                record[f'{map_id}_scale'] = scale

    if record.get('pdf_template_code'):
        template_html = get_config_value(record.get('pdf_template_code'))
        if template_html:
            html_source = render_template_string(template_html, data=record)
        else:
            html_source = render_template(template_file, data=record)
    else:
        html_source = render_template(template_file, data=record)

    with open(filename, "w+b") as result_file:
        # convert HTML to PDF
        pisa_status = pisa.CreatePDF(
            html_source,  # page data
            dest=result_file,  # destination file
        )

        # Check for errors
        if pisa_status.err:
            print("An error occurred!")
            return False

    return True


def create_map_image(geom_ewkt, map_config):
    img_str = None

    geom_srid = geom_ewkt.split(';')[0].split('=')[1]
    geom_wkt = geom_ewkt.split(';')[1]

    geom = getGeometryFromWKT(geom_wkt)

    out_srid = map_config.get('srid', geom_srid)

    geom = transformGeom(geom, f'EPSG:{geom_srid}', f'EPSG:{out_srid}')

    img_width = map_config.get('width')
    img_height = map_config.get('height')

    width = img_width #* mm
    height = img_height #* mm

    center = geom.centroid

    bbox, scale = calculate_bbox_geom(geom, width, height)

    if map_config.get('scale', None):
        scale = map_config.get('scale')

    bbox = calculate_bbox(scale, center.x, center.y, img_width, img_height)

    geom_wkt = str(geom)

    layers = map_config.get('layers', [])

    if (len(layers)) < 0:
        return None, None, None, None, None

    filename = str(uuid.uuid4()) + ".pdf"

    can = canvas.Canvas(os.path.join(settings.APP_TMP_DIR, filename), pagesize=(width, height))
    #can = canvas.Canvas(os.path.join(settings.APP_TMP_DIR, filename), pagesize=A4)

    map_extent = bbox

    for layer in layers:
        try:
            _url = layer.get('url')
            _version = layer.get('version')
            _layers = layer.get('layers')
            _styles = layer.get('styles')
            _transparent = layer.get('transparent', True)
            _format = layer.get('format')

            url, extent = getmap_url(_url, _layers, bbox, width, height, geom_wkt, out_srid,
                                     scale, version=_version, format=_format, styles=_styles, transparent=_transparent)

            map_extent = extent

            img = ImageReader(url)

            can.drawImage(img, 0, 0, width=width, height=height, mask='auto')
        except Exception as err:
            logger.warning(err)

    #draw_geometry(can, 6000, center.x, center.y, width / mm, height / mm, 0, 0, geom, map_config.get('style', None))
    draw_geometry(can, scale, center.x, center.y, width, height, 0, 0, geom, map_config.get('style', None))

    can.showPage()

    can.save()

    doc = fitz.open(os.path.join(settings.APP_TMP_DIR, filename))
    for page in doc:
        pix = page.get_pixmap()  # render page to an image

        img = PILImage.frombytes("RGB", [pix.width, pix.height], pix.samples)

        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

    if os.path.exists(os.path.join(settings.APP_TMP_DIR, filename)):
        doc.close()
        os.remove(os.path.join(settings.APP_TMP_DIR, filename))

    return img_str, img_width, img_height, map_extent, scale


def draw_geometry(canvas, scale, mapcenter_x, mapcenter_y, width, height, ll_x, ll_y, geom, style,
                  draw_centroid=False, unit_factor=1):
    vertice_size = style["vertice_size"]
    point_size = style["point_size"]
    point_stroke_color = style["point_stroke_color"]
    point_fill_color = style["point_fill_color"]
    line_width = style["line_width"]
    line_color = style["line_color"]
    line_dash = style["line_dash"]
    line_vertice = style["line_vertice"]
    polygon_stroke_width = style["polygon_stroke_width"]
    polygon_stroke_color = style["polygon_stroke_color"]
    polygon_stroke_dash = style["polygon_stroke_dash"]
    polygon_vertice = style["polygon_vertice"]
    polygon_fill_color = style["polygon_fill_color"]

    mm = unit_factor

    xmin, ymin, xmax, ymax = calculate_bbox(scale, mapcenter_x, mapcenter_y, width, height)
    xfactor = abs(xmax - xmin) / width
    yfactor = abs(ymax - ymin) / height

    geoms = []
    if geom.geom_type == 'GeometryCollection':
        for gm in geom.geoms:
            geoms.append(gm)
    else:
        geoms.append(geom)

    for gm in geoms:
        if draw_centroid:
            gm = gm.centroid

        canvas.saveState()
        canvas.translate(ll_x * mm, ll_y * mm)

        if gm.geom_type == 'Point' or gm.geom_type == 'MultiPoint':
            my_stroke = colors.Color(point_stroke_color[0], point_stroke_color[1], point_stroke_color[2],
                                     point_stroke_color[3])
            canvas.setStrokeColor(my_stroke)
            myfill = colors.Color(point_fill_color[0], point_fill_color[1], point_fill_color[2], point_fill_color[3])
            canvas.setFillColor(myfill)

            if gm.geom_type == 'Point':
                gm = geometry.MultiPoint([gm])

            for i in range(len(gm.geoms)):
                logger.debug(gm.geoms[i])
                x = (gm.geoms[i].x - xmin) / xfactor
                y = (gm.geoms[i].y - ymin) / yfactor
                canvas.circle(x * mm, y * mm, point_size * mm, fill=1)

        elif gm.geom_type == 'LineString' or gm.geom_type == 'MultiLineString':
            my_stroke = colors.Color(line_color[0], line_color[1], line_color[2], line_color[3])
            canvas.setStrokeColor(my_stroke)

            if gm.geom_type == 'LineString':
                gm = geometry.MultiLineString([gm])

            for i in range(len(gm.geoms)):
                logger.debug(gm.geoms[i])
                path = canvas.beginPath()
                ox = (float(gm.geoms[i].coords[0][0]) - xmin) / xfactor
                oy = (float(gm.geoms[i].coords[0][1]) - ymin) / yfactor
                path.moveTo(ox * mm, oy * mm)
                for p in gm.geoms[i].coords:
                    x = (p[0] - xmin) / xfactor
                    y = (p[1] - ymin) / yfactor
                    if line_vertice:
                        canvas.circle(x * mm, y * mm, vertice_size * mm, fill=0)
                    path.lineTo(x * mm, y * mm)
                canvas.setLineWidth(line_width)
                if line_dash:
                    canvas.setDash(6, 3)
                canvas.drawPath(path, stroke=1, fill=0)

        elif gm.geom_type == 'Polygon' or gm.geom_type == 'MultiPolygon':
            my_stroke = colors.Color(polygon_stroke_color[0], polygon_stroke_color[1], polygon_stroke_color[2],
                                     polygon_stroke_color[3])
            canvas.setStrokeColor(my_stroke)
            myfill = colors.Color(polygon_fill_color[0], polygon_fill_color[1], polygon_fill_color[2],
                                  polygon_fill_color[3])
            canvas.setFillColor(myfill)

            if gm.geom_type == 'Polygon':
                gm = geometry.MultiPolygon([gm])

            if polygon_stroke_dash:
                canvas.setDash(6, 3)
            canvas.setLineWidth(polygon_stroke_width)

            def draw_geom_ring(ring):
                logger.debug(ring)
                path = canvas.beginPath()
                start_x = (float(ring.coords[0][0]) - xmin) / xfactor
                start_y = (float(ring.coords[0][1]) - ymin) / xfactor
                path.moveTo(start_x * mm, start_y * mm)
                for p in ring.coords:
                    x = (p[0] - xmin) / xfactor
                    y = (p[1] - ymin) / yfactor
                    if polygon_vertice:
                        canvas.circle(x * mm, y * mm, vertice_size * mm, fill=0)
                    path.lineTo(x * mm, y * mm)
                canvas.drawPath(path, stroke=1, fill=1)

            for i in range(len(gm.geoms)): # draw exterior rings
                draw_geom_ring(gm.geoms[i].exterior)
                for ii in range(len(gm.geoms[i].interiors)):  # draw interior rings
                    draw_geom_ring(gm.geoms[i].interiors[ii])

        else:
            logger.warning("Bad geom type")

        canvas.restoreState()