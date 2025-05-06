from flask import current_app
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, A3, A2, A1, A0, landscape
from reportlab.lib.units import mm
from reportlab.lib import utils, colors
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.platypus import Table, TableStyle
from reportlab.lib.enums import TA_JUSTIFY  # , TA_LEFT, TA_CENTER
from reportlab.lib.colors import Color

#from PyPDF2 import PdfFileWriter, PdfFileReader, PdfFileMerger
from PyPDF2 import PdfWriter, PdfReader, PdfMerger

import qrcode

from shapely import wkt, geometry
import pyproj
from sqlalchemy import text
from PIL import Image
from io import BytesIO
import requests
import time
import os
import re
from math import pi, cos, sin, floor, ceil

import copy
import json
from jsonmerge import Merger
import logging
import urllib.parse

from app.database import db
from app import get_db_schema
from app.models.portal import PrintElement
from app.utils import geo
from app.utils.http import replace_geoserver_url

from instance.settings import APP_STATIC, APP_RESOURCES

logger = logging.getLogger(__name__)  # or logging.getLogger()

db_schema = get_db_schema()


def merge_pdf_files(filename, files):
    pdf_writer = PdfWriter()

    # Loop through all the PDF files.
    for f in files:
        pdf_file = open(f, 'rb')
        pdf_reader = PdfReader(pdf_file)
        # Loop through all the pages (except the first) and add them.
        # If first page should be discarded, change firt param of range to 1
        #for page_num in range(0, pdf_reader.numPages):
        for page_num in range(0, len(pdf_reader.pages)):
            #page = pdf_reader.getPage(page_num)
            page = pdf_reader.pages[page_num]
            #pdf_writer.addPage(page)
            pdf_writer.add_page(page)

    # Save the resulting PDF to a file.
    pdf_output = open(filename, 'wb')
    pdf_writer.write(pdf_output)
    pdf_output.close()

    return True

def get_image_with_opacity(url, opacity):
    output_img = None

    response = requests.get(url, verify=False)
    imgb = Image.open(BytesIO(response.content))

    if imgb is not None:
        imgb = imgb.convert("RGBA")
        datas = imgb.getdata()
        newData = []
        for item in datas:
            alpha = int(item[3] * opacity)
            newData.append((item[0], item[1], item[2], alpha))

        imgb.putdata(newData)

        output_img = ImageReader(imgb)

    return output_img

class Pdf:
    """" Map pdf layout """

    def __init__(self, page_size='A4', orientation='portrait'):
        # create dynamic pdf object
        self.output = BytesIO()
        self.tmp_output = None
        self.maps = []
        self.strings = []
        self.paragraphs = []
        self.images = []
        self.legends = []
        self.tables = []

        self.config_strings = {}
        self.config_paragraphs = {}
        self.canvas = None
        self.isclosed = None  # no canvas ...
        self.configs = None
        self.geom = None
        self.mapcenter = None
        self.bbox = []
        self.resolution = None
        self.db_vars = {}
        self.widget_inputs = []
        self.drawing_features = None
        self.drawings = None # Scalargis DrawTools features

        page_size_dict = {"A4": A4, "A3": A3, "A2": A2, "A1": A1, "A0": A0}
        try:
            self.pagesize = page_size_dict[page_size]
        except KeyError as err:
            logger.error("Page size is not valid. Exiting...")
            raise err

        if orientation not in ['portrait', 'landscape']:
            err = 'Page orientation is not valid'
            logger.error(err)
            raise Exception(err)

        self.orientation = orientation
        try:
            self.create_canvas(self.pagesize, orientation)
        except Exception as err:
            logger.error("Can't create canvas. Exiting...")
            raise Exception(err)

        logger.debug("Pdf object created: " + orientation + " " + page_size)


    def create_canvas(self, page_size=A4, orientation='portrait'):
        # new canvas with empty io
        self.output = BytesIO()

        if orientation == 'portrait':
            self.canvas = canvas.Canvas(self.output, pagesize=page_size)
        else:
            self.canvas = canvas.Canvas(self.output, pagesize=landscape(page_size))

        self.isclosed = False  # True when canvas.save() .. no more op on page.
        logger.debug("BytesIO opened for new canvas...")


    def close(self):
        # just close io. (to use if no getpdf)
        self.output.close()


    def savepdf(self):
        # closing dynamic pdf, needed before getpdf() if no call to generate()  ...
        self.canvas.save()


    def getpdf(self):
        # close io and return pdf
        self.isclosed = True
        pdf = self.output.getvalue()
        self.output.close()
        return pdf


    def get_io(self):
        # get io stream.
        return self.output


    def add_map(self, serv_type, url, layers, page_id=None, img_format='image/png', quality=2, transparent=True,
                cql_filter=None, style=None, opacity=1, url_params=[]):
        # add map.
        # serv_type: wms or esri_rest supported
        # layers: listof  geoserver url
        # ordered rendering: first added map is back.
        # p.add_map('wms','195.95.237.222/geoserver/cm_faro/wms','cm_faro:municipal_ln,cm_faro:equipamentos')
        # page_id limit to one page. Page_id is an element in json config
        # quality: factor for wms, dpi for esri_rest
        self.maps.append([serv_type, url, layers, page_id, img_format, quality, transparent, cql_filter, style,
                          opacity, url_params])

    def add_legend(self, url, layer, x, y, width, gs_vendor_option="", serv_type="wms", style="", page_id=None):
        # add service legend
        self.legends.append([url, layer, x, y, width, gs_vendor_option, serv_type, style, page_id])

    def add_widget_input(self, widget_input):
        # add widget_inputs to be merged
        self.widget_inputs.append(widget_input)


    def add_string(self, x, y, txt, font="Helvetica", fontsize=10, fontcolor=None, page_id=None):
        # add strings objects to document. If no page_id, strings are inserted in all pages
        if fontcolor is None:
            fontcolor = [0, 0, 0, 1]
        self.strings.append([x, y, txt, font, fontsize, fontcolor, page_id])


    def add_paragraph(self, x, y, width, height, txt, font='Helvetica', fontsize=8, fontcolor=None, leading=9,
                      page_id=None):
        # add paragraphs objects to document. If no page_id, strings are inserted in all pages
        if fontcolor is None:
            fontcolor = [0, 0, 0, 1]
        self.paragraphs.append([x, y, width, height, txt, font, fontsize, fontcolor, leading, page_id])


    def add_image(self, path, x, y, width, page_id=None):
        self.images.append([path, x, y, width, page_id])


    def add_table(self, x, y, width, height, data, table_style=None, page_id=None, table_style_def=None, colWidth=None):
        self.tables.append([x, y, width, height, data, table_style, page_id, table_style_def, colWidth])


    def populate_string(self, string_name, txt, page_id=None):
        # set value of config json string
        self.config_strings[string_name] = [txt, page_id]


    def populate_paragraph(self, string_name, txt, page_id=None):
        # set value of config json paragraph
        self.config_paragraphs[string_name] = [txt, page_id]


    def set_wkt(self, _wkt, is_centered=True):
        try:
            # wkt.loads(_wkt)
            self.geom = geo.getGeometryFromWKT(_wkt)
            center = self.geom.centroid
            self.populate_string("_geometry_center_x", str(round(center.x))) # populate strings if found in config
            self.populate_string("_geometry_center_y", str(round(center.y)))
            if is_centered:
                self.mapcenter = [center.x, center.y]
            logger.debug("WKT to draw: " + self.geom.wkt)
        except Exception as err:
            logger.warning(str(err) + " :: Can't load WKT (set_wkt)")


    def center_map(self, _wkt):
        try:
            geom = wkt.loads(_wkt)
            center = geom.centroid
            self.mapcenter = [center.x, center.y]
            logger.debug("WKT to center: " + _wkt)
        except Exception as err:
            logger.warning(str(err) + " :: Can't load WKT (center_map)")


    def set_wkt_and_center(self, _wkt, _extent_wkt, is_wkt_centered=True):
        # wrapper for set_wkt and center_map with some checks
        # by default, center is draw wkt
        # priority to wkt
        self.center_map(_extent_wkt)
        if is_wkt_centered:
            self.set_wkt(_wkt, True)
        else:
            self.set_wkt(_wkt, False)


    def generate(self, config_file, scale=None, srid=None, mapcenter=None):
        # generate pdf reading json config file....
        logger.debug("Start generating pdf from json config...")

        if self.isclosed:
            logger.warning("Can't generate: object is closed. Exiting...")
            return

        try:
            self.configs = json.loads(config_file) # default, config is a string
            logger.debug("JSON config loaded...")
        except Exception as err:
            logger.debug(str(err) + " :: config file is not a string, using as python dict")
            # allow to pass python dict config in generate
            self.configs = config_file

        need_append = False
        nb_confgis = len(self.configs)
        p_scale = scale
        p_mapcenter = mapcenter
        for i in range(nb_confgis):
            # for config in self.configs:
            config = self.configs[i]

            # sublayouts --------
            layout_schema = {
                "properties": {
                    "strings": {"mergeStrategy": "append"},
                    "paragraphs": {"mergeStrategy": "append"},
                    "images": {"mergeStrategy": "append"},
                    "pdf_files": {"mergeStrategy": "append"},
                    "basemap_layers": {"mergeStrategy": "append"},
                    "top_layers": {"mergeStrategy": "append"},
                    "graphics": {"mergeStrategy": "append"}
                }
            }

            merger = Merger(layout_schema)

            try:
                for sublayout in config["sublayouts"]:
                    if sublayout["active"]:
                        code = sublayout["code"]
                        sublayoutconf = db.session.query(PrintElement).filter(PrintElement.code == code).first()

                        if sublayoutconf:
                            subjson = json.loads(sublayoutconf.config)

                            if sublayout["force"]:  # priority to sublayout
                                config = merger.merge(config, subjson)
                            else:
                                config = merger.merge(subjson, config)
                        else:
                            logger.debug('Sublayout not found... passing')
                            #logger.debug('Sublayout not found: {code}'.format(code=code))

            except KeyError:
                logger.debug('No sublayout defined... passing.')
            except Exception as err:
                logger.error('Error trying to merge sublayout... exit')
                raise Exception(err)

            # plugins inputs ------------------ (typeof sublayout injected by widgets)
            layout_schema = {
                "properties": {
                    "strings": {
                        "type": "array",
                        "mergeStrategy": "arrayMergeById",
                        "mergeOptions": {"idRef": "name"}
                    },
                    "paragraphs": {
                        "type": "array",
                        "mergeStrategy": "arrayMergeById",
                        "mergeOptions": {"idRef": "name"}},
                    "images": {"mergeStrategy": "append"},
                    "pdf_files": {"mergeStrategy": "append"},
                    "basemap_layers": {"mergeStrategy": "append"},
                    "top_layers": {"mergeStrategy": "append"},
                    "graphics": {"mergeStrategy": "append"}
                }
            }

            merger = Merger(layout_schema)

            for wid in self.widget_inputs:
                sqltxt = "Select config from {schema}.widget where code = '%s'".format(schema=db_schema) % wid['codigo']
                input_conf = db.session.execute(sqltxt).first()
                subjson = json.loads(input_conf[0])
                base = None
                base = merger.merge(base, config)
                base = merger.merge(base, subjson)
                config = base

            # srid -----------
            if srid is None:
                srid = config["params"]["default_srid"]

            # mapcenter -----------
            if mapcenter is None:  # priority is: 1 params 2 wkt 3 defaultconfig
                mapcenter = self.mapcenter
                if mapcenter is None:
                    mapcenter = config["params"]["default_mapcenter"]

            try:
                if config["params"]["force_mapcenter"]:
                    mapcenter = config["params"]["default_mapcenter"]
            except KeyError:
                logger.debug('["params"]["force_mapcenter"] Does not exist in config... ')

            # scale ---------------
            if p_scale is None:
                scale = config["params"]["default_scale"]
            else:
                scale = p_scale

            try:  # scale forced by config
                if config["params"]["force_default_scale"]:
                    scale = config["params"]["default_scale"]
            except KeyError:
                logger.debug('["params"]["force_default_scale"] Does not exist in config... ')

            logger.info("Page_id=" + str(config["page_id"]) + " mapcenter=" + str(mapcenter) +
                        " srid=" + str(srid) + " scale=" + str(scale))

            if self.isclosed:  # not first page
                self.tmp_output = copy.deepcopy(self.output)  # save copy for append
                self.create_canvas(self.pagesize, self.orientation)
                need_append = True

            # map position
            if 'map' in config:
                ll_x = config["map"]["ll_x"]
                ll_y = config["map"]["ll_y"]
                width = config["map"]["width"]
                height = config["map"]["height"]

                self.calc_bbox(scale, mapcenter[0], mapcenter[1], width, height)
            else:
                logger.debug('No map on this page config')

            # execute geo db functions (only if wkt exists)
            try:
                if self.geom:
                    srid_for_ewkt = "SRID=%s" % srid
                    ewkt = ";".join([srid_for_ewkt, self.geom.wkt])

                    for db_geo_func in config["db_geo_func"]:
                        if db_geo_func["active"]:
                            func_var = db_geo_func["func_var"]
                            func_txt = db_geo_func["sql_function"].replace('%input_ewkt%', ewkt)
                            qy_result = db.session.execute(text(func_txt)).first()

                            if qy_result and qy_result[0]:
                                self.db_vars[func_var] = qy_result[0][0]

            except KeyError:
                logger.debug('No db_geo_func defined... passing.')
            except Exception as err:
                logger.error('Error in db_geo_func.. exit')
                raise Exception(err)

            # draw map area background
            if 'map' in config:
                try:
                    fill_map_background = config["params"]["fill_map_backgroud"]
                except KeyError:
                    fill_map_background = True  # default if no conf entry
                if fill_map_background:
                    self.canvas.saveState()
                    self.canvas.setFillColor(colors.Color(1, 1, 1, 1))
                    self.canvas.rect(ll_x * mm, ll_y * mm, width * mm, height * mm, stroke=0, fill=1)
                    self.canvas.restoreState()

            # basemap layers

            if 'basemap_layers' in config:
                for item in config["basemap_layers"]:
                    serv_type = item["serv_type"]
                    if serv_type == 'wms':
                        url = item["url"]
                        layers = item["layers"]
                        img_format = item["format"]
                        try:
                            quality = item["quality"]
                        except KeyError:
                            quality = 2
                        try:
                            style = item["style"]
                        except KeyError:
                            style = None
                        try:
                            cql_filter = item["cql_filter"]
                        except KeyError:
                            cql_filter = None

                        try:
                            mindenomscale = item["mindenomscale"]
                        except KeyError:
                            mindenomscale = -1

                        try:
                            maxdenomscale = item["maxdenomscale"]
                        except KeyError:
                            maxdenomscale = 100000000000

                        try:
                            page_formats = item["page_formats"]
                            authorized_format = False
                            page_size_dict = {"A4": A4, "A3": A3, "A2": A2, "A1": A1, "A0": A0}
                            for f in page_formats:
                                psize = page_size_dict[f]
                                if self.pagesize == psize:
                                    authorized_format = True
                        except KeyError:
                            authorized_format = True # no restriction

                        if scale >= mindenomscale and scale <= maxdenomscale and authorized_format:
                            self.insert_map(serv_type, scale, srid, mapcenter[0], mapcenter[1], width, height, img_format,
                                            ll_x, ll_y, url, layers, quality, style=style, cql_filter=cql_filter)
                            try:
                                logo = item["logo"]
                                logo_path = logo["path"]
                                # support absolute paths
                                if os.path.exists(logo_path):
                                    logo_path = logo_path
                                else:
                                    logo_path = os.path.join(APP_RESOURCES, logo_path)
                                logo_x = logo["x"]
                                logo_y = logo["y"]
                                logo_width = logo["width"]
                                self.canvas.saveState()
                                self.insert_img(logo_path, logo_x, logo_y, logo_width)
                                self.canvas.restoreState()
                            except KeyError:
                                logger.debug('No Logo defined for this layer... ')


                    elif serv_type == 'esri_rest':
                        url = item["url"]
                        layers = item["layers"]
                        img_format = item["format"]
                        quality = item["dpi"]
                        transparent = item["transparent"]
                        opacity = item["opacity"]
                        self.insert_map(serv_type, scale, srid, mapcenter[0], mapcenter[1], width, height, img_format,
                                        ll_x, ll_y, url, layers, quality, transparent, None, None, opacity)


            # dynamic map
            for dmap in self.maps:
                insert_on_subpage = False
                try:  # check if sub_id
                    if dmap[3] == config["page_sub_id"]:
                        insert_on_subpage = True
                except KeyError:
                    logger.debug('["page_sub_id"] Does not exist in config... ')

                if (dmap[3] is None) or (dmap[3] == config["page_id"]) or insert_on_subpage:
                    if dmap[0] == 'wms':
                        try:
                            style = dmap[8]
                        except KeyError:
                            style = None
                        try:
                            cql_filter = dmap[7]
                        except KeyError:
                            cql_filter = None
                        try:
                            opacity = dmap[9]
                        except KeyError:
                            opacity = 1

                        mindenomscale = -1
                        maxdenomscale = 100000000000
                        authorized_format = True
                        have_extra_conf = False
                        try:
                            dinamic_layers_definitions = config["dinamic_layers_definitions"]
                            for item in dinamic_layers_definitions:

                                if (dmap[1][:7] == 'http://'):
                                    dmap_url = dmap[1][7:]
                                elif (dmap[1][:8] == 'https://'):
                                    dmap_url = dmap[1][8:]
                                else:
                                    dmap_url = dmap[1]

                                if (item["url"][:7] == 'http://'):
                                    dinamic_serv_url = item["url"][7:]
                                elif (item["url"][:8] == 'https://'):
                                    dinamic_serv_url = item["url"][8:]
                                else:
                                    dinamic_serv_url = item["url"]


                                if dmap_url == dinamic_serv_url and item["layers"] == dmap[2]: # found extra def
                                    have_extra_conf = True
                                    try:
                                        mindenomscale = item["mindenomscale"]
                                    except KeyError:
                                        mindenomscale = -1

                                    try:
                                        maxdenomscale = item["maxdenomscale"]
                                    except KeyError:
                                        maxdenomscale = 100000000000

                                    try:
                                        page_formats = item["page_formats"]
                                        authorized_format = False
                                        page_size_dict = {"A4": A4, "A3": A3, "A2": A2, "A1": A1, "A0": A0}
                                        for f in page_formats:
                                            psize = page_size_dict[f]
                                            if self.pagesize == psize:
                                                authorized_format = True
                                    except KeyError:
                                        authorized_format = True  # no restriction

                        except KeyError:
                            logger.debug('["No dinamic_layers_definitions... ')

                        if scale >= mindenomscale and scale <= maxdenomscale and authorized_format:
                            self.insert_map('wms', scale, srid, mapcenter[0], mapcenter[1], width, height,
                                            dmap[4], ll_x, ll_y, dmap[1], dmap[2], dmap[5], cql_filter=cql_filter,
                                            style=style, opacity=opacity, url_params=dmap[10] if len(dmap) > 10 else [])


                            if have_extra_conf and "strings" in item:
                                try:
                                    layer_strings = item["strings"]
                                    for layer_string in layer_strings:
                                        self.add_string(layer_string["x"],layer_string["y"],layer_string["value"],layer_string["font"],
                                                        layer_string["fontsize"],layer_string["fontcolor"],
                                                        layer_string["page_id"] if "page_id" in layer_string else None)
                                except Exception as err:
                                    logger.warning('Insert layer string error')


                            if have_extra_conf:
                                try:
                                    logo = item["logo"]
                                    logo_path = logo["path"]
                                    # support absolute paths
                                    if os.path.exists(logo_path):
                                        logo_path = logo_path
                                    else:
                                        logo_path = os.path.join(APP_RESOURCES, logo_path)
                                    logo_x = logo["x"]
                                    logo_y = logo["y"]
                                    logo_width = logo["width"]
                                    self.canvas.saveState()
                                    self.insert_img(logo_path, logo_x, logo_y, logo_width)
                                    self.canvas.restoreState()
                                except KeyError:
                                    logger.debug('No Logo defined for this layer... ')


                    elif dmap[0] == 'esri_rest':
                        self.insert_map('esri_rest', scale, srid, mapcenter[0], mapcenter[1], width, height,
                                        dmap[4], ll_x, ll_y, dmap[1], dmap[2], dmap[5], dmap[6], None, None, dmap[9])

            # top layers
            if 'top_layers' in config:
                for item in config["top_layers"]:
                    serv_type = item["serv_type"]
                    if serv_type == 'wms':
                        url = item["url"]
                        layers = item["layers"]
                        img_format = item["format"]
                        try:
                            quality = item["quality"]
                        except KeyError:
                            quality = 2
                        try:
                            style = item["style"]
                        except KeyError:
                            style = None
                        try:
                            cql_filter = item["cql_filter"]
                        except KeyError:
                            cql_filter = None

                        try:
                            mindenomscale = item["mindenomscale"]
                        except KeyError:
                            mindenomscale = -1

                        try:
                            maxdenomscale = item["maxdenomscale"]
                        except KeyError:
                            maxdenomscale = 100000000000

                        try:
                            page_formats = item["page_formats"]
                            authorized_format = False
                            page_size_dict = {"A4": A4, "A3": A3, "A2": A2, "A1": A1, "A0": A0}
                            for f in page_formats:
                                psize = page_size_dict[f]
                                if self.pagesize == psize:
                                    authorized_format = True
                        except KeyError:
                            authorized_format = True # no restriction

                        if scale >= mindenomscale and scale <= maxdenomscale and authorized_format:
                            self.insert_map(serv_type, scale, srid, mapcenter[0], mapcenter[1], width, height, img_format,
                                            ll_x, ll_y, url, layers, quality, style=style, cql_filter=cql_filter)
                            try:
                                logo = item["logo"]
                                logo_path = logo["path"]
                                # support absolute paths
                                if os.path.exists(logo_path):
                                    logo_path = logo_path
                                else:
                                    logo_path = os.path.join(APP_RESOURCES, logo_path)
                                logo_x = logo["x"]
                                logo_y = logo["y"]
                                logo_width = logo["width"]
                                self.canvas.saveState()
                                self.insert_img(logo_path, logo_x, logo_y, logo_width)
                                self.canvas.restoreState()
                            except KeyError:
                                logger.debug('No Logo defined for this layer... ')

                    elif serv_type == 'esri_rest':
                        url = item["url"]
                        img_format = item["format"]
                        quality = item["dpi"]
                        transparent = item["transparent"]
                        self.insert_map(serv_type, scale, srid, mapcenter[0], mapcenter[1], width, height, img_format,
                                        ll_x, ll_y, url, None, quality, transparent)



            # draw wkt feature ------------------------- !
            if 'geom_style' in config:
                if config["geom_style"]["active"]:
                    if self.geom:
                        style = config["geom_style"]

                        try:
                            draw_centroid = config["geom_style"]["draw_centroid"]
                        except KeyError:
                            draw_centroid = False  # default is not reduce to centroid

                        self.draw_geometry(scale, mapcenter[0], mapcenter[1], width, height, ll_x, ll_y, self.geom, style,
                                           draw_centroid)

            # client widget drawing features ----------------------
            if self.drawing_features:
                if 'map' in config :
                    if 'draw_features' in config["map"]:
                        if config["map"]["draw_features"]:
                            self.draw_features(scale, mapcenter[0], mapcenter[1], width, height, ll_x, ll_y,
                                               self.drawing_features)
                    else: # draw if not exists def in config.
                        self.draw_features(scale, mapcenter[0], mapcenter[1], width, height, ll_x, ll_y,
                                           self.drawing_features)

            # Scalargis Drawtools elements --------------------------
            if self.drawings:
                if "draw_scalargis_drawings" in config["params"]:
                    if config["params"]["draw_scalargis_drawings"]:
                        try:
                            self.insert_drawings(srid, scale, mapcenter[0], mapcenter[1], width, height, ll_x, ll_y,
                                                   self.drawings)
                        except:
                            logger.warning('Print Scalargis drawings error')

            # clean feature outside map
            try:
                clean = config["params"]["clean_arround_map"]
            except KeyError:
                clean = True  # default is True

            if 'map' in config and (nb_confgis == 1 or clean):
                # clear arround map only if one page or use json config ["params"]["clean_arround_map"]
                self.canvas.saveState()
                pg_x = self.pagesize[0]
                pg_y = self.pagesize[1]
                self.canvas.setFillColor(colors.Color(1, 1, 1, 1))
                self.canvas.rect(0, 0, pg_x * mm, ll_y * mm, stroke=0, fill=1)
                self.canvas.rect(0, 0, ll_x * mm, pg_y * mm, stroke=0, fill=1)
                self.canvas.rect(0, (ll_y + height) * mm, pg_x * mm, (pg_y - ll_y - height) * mm, stroke=0, fill=1)
                self.canvas.rect((ll_x + width) * mm, 0, (pg_x - ll_x - width) * mm, pg_y * mm, stroke=0, fill=1)
                self.canvas.restoreState()


            # legends
            if 'legends' in config:
                if config["legends"]:
                    for item in config["legends"]:
                        l_serv_type = item["serv_type"]
                        l_url = item["url"]
                        l_layer = item["layer"]
                        l_x = item["x"]
                        l_y = item["y"]
                        l_width = item["width"]
                        if 'gs_vendor_options' in item:
                            gs_vendor_options = item["gs_vendor_options"]
                        else:
                            gs_vendor_options =  ''

                        if 'style' in item:
                            style = item["style"]
                        else:
                            style = ''

                        if l_serv_type == 'wms':
                            self.insert_legend('wms', l_url, l_layer, l_x, l_y, l_width, gs_vendor_options=gs_vendor_options, style=style)
                            pass
            else:
                logger.debug('No Legend defined... passing')

            # dynamic legend  ----------------------------------
            for dlegend in self.legends:
                if dlegend[6] == 'wms' and (dlegend[8] is None or dlegend[8] == config["page_id"]) :
                    self.insert_legend('wms', dlegend[0], dlegend[1], dlegend[2], dlegend[3], dlegend[4],
                                       gs_vendor_options=dlegend[5],
                                       style=dlegend[7])


            # graphics
            if 'graphics' in config:
                for graphic in config["graphics"]:
                    self.draw_graphic(graphic)
            else:
                logger.debug('No Graphic to draw..')

            # scale
            if 'scale' in config:
                if config["scale"]["active"]:
                    x = config["scale"]["x"]
                    y = config["scale"]["y"]

                    try:
                        x = x + config["scale"]["delta_x"]
                    except KeyError:
                        pass  # no delta defined
                    try:
                        y = y + config["scale"]["delta_y"]
                    except KeyError:
                        pass  # no delta defined

                    font = config["scale"]["font"]
                    fontsize = config["scale"]["fontsize"]
                    prefix = config["scale"]["prefix"]
                    string_scale = prefix + str(scale)
                    self.insert_string(x, y, string_scale, font, fontsize)

            # Date
            if 'date' in config:
                if config["date"]["active"]:
                    x = config["date"]["x"]
                    y = config["date"]["y"]

                    try:
                        x = x + config["date"]["delta_x"]
                    except KeyError:
                        pass  # no delta defined
                    try:
                        y = y + config["date"]["delta_y"]
                    except KeyError:
                        pass  # no delta defined

                    font = config["date"]["font"]
                    fontsize = config["date"]["fontsize"]
                    dformat = config["date"]["format"]
                    prefix = config["date"]["prefix"]
                    date = prefix + time.strftime(dformat)
                    self.insert_string(x, y, date, font, fontsize)

            # strings
            for string in self.strings:
                if (string[6] is None) or (string[6] == config["page_id"]):
                    x = string[0]
                    y = string[1]
                    txt = string[2]
                    font = string[3]
                    fontsize = string[4]
                    fontcolor = string[5]
                    self.insert_string(x, y, txt, font, fontsize, fontcolor)

            # json config strings
            if 'strings' in config:
                for string in config["strings"]:

                    if 'active' in string:  # ie visibility can be function of user geom
                        if (string["active"] is False):
                            continue
                        elif (string["active"] == "when_user_geom" and not self.geom):
                            continue
                        elif (string["active"] == "when_not_user_geom" and self.geom):
                            continue

                    str_name = string["name"]
                    x = string["x"]
                    y = string["y"]

                    try:
                        x = x + string["delta_x"]
                    except KeyError:
                        pass  # no delta defined
                    try:
                        y = y + string["delta_y"]
                    except KeyError:
                        pass  # no delta defined

                    if 'rotate' in string:
                        rotation = string["rotate"]
                    else:
                        rotation = 0

                    if 'mode' in string:
                        mode = string["mode"]
                    else:
                        mode = None

                    txt = string["value"]
                    font = string["font"]
                    fontsize = string["fontsize"]
                    fontcolor = string["fontcolor"]
                    if str_name in self.config_strings.keys():
                        page_id = self.config_strings[str_name][1]
                        if (page_id is None) or (page_id == config["page_id"]):
                            txt = self.config_strings[str_name][0]

                    if txt is not None and bool(re.search('%\[.*\]%', txt)):  # find a db_var pattern
                        var_idenf = eval(re.search('%.*%', txt).group()[1:-1])
                        if var_idenf[0] in self.db_vars:
                            dbval = self.db_vars[var_idenf[0]][var_idenf[1]]
                            var_to_rep = re.search('%.*%', txt).group()
                            txt = txt.replace(var_to_rep, dbval)
                        else:
                            txt = None

                    if txt is not None:
                        self.insert_string(x, y, txt, font, fontsize, fontcolor,mode=mode,rotation=rotation)

            # paragraphs
            for paragraph in self.paragraphs:
                if (paragraph[9] is None) or (paragraph[9] == config["page_id"]):
                    x = paragraph[0]
                    y = paragraph[1]
                    width = paragraph[2]
                    height = paragraph[3]
                    txt = paragraph[4]
                    font = paragraph[5]
                    fontsize = paragraph[6]
                    fontcolor = paragraph[7]
                    leading = paragraph[8]
                    self.insert_paragraph(x, y, width, height, txt, font, fontsize, fontcolor, leading)

            # json config paragraphs
            if 'paragraphs' in config:
                for paragraph in config["paragraphs"]:

                    if 'active' in paragraph:  # ie visibility can be function of user geom
                        if (paragraph["active"] is False):
                            continue
                        elif (paragraph["active"] == "when_user_geom" and not self.geom):
                            continue
                        elif (paragraph["active"] == "when_not_user_geom" and self.geom):
                            continue

                    pgp_name = paragraph["name"]
                    x = paragraph["x"]
                    y = paragraph["y"]

                    try:
                        x = x + paragraph["delta_x"]
                    except KeyError:
                        pass  # no delta defined
                    try:
                        y = y + paragraph["delta_y"]
                    except KeyError:
                        pass  # no delta defined

                    width = paragraph["width"]
                    height = paragraph["height"]
                    txt = paragraph["value"]
                    font = paragraph["font"]
                    fontsize = paragraph["fontsize"]
                    fontcolor = paragraph["fontcolor"]
                    try:
                        leading = paragraph["leading"]
                    except KeyError:
                        leading = 9
                    if pgp_name in self.config_paragraphs.keys():
                        page_id = self.config_paragraphs[pgp_name][1]
                        if (page_id is None) or (page_id == config["page_id"]):
                            txt = self.config_paragraphs[pgp_name][0]
                    if txt is not None:
                        self.insert_paragraph(x, y, width, height, txt, font, fontsize, fontcolor, leading)

            # images
            for image in self.images:
                if (image[4] is None) or (image[4] == config["page_id"]):
                    path = os.path.join(APP_RESOURCES, image[0])
                    x = image[1]
                    y = image[2]
                    width = image[3]
                    self.insert_img(path, x, y, width)

            # json config images
            if 'images' in config:
                for image in config["images"]:
                    path = image["path"]
                    # support absolute paths
                    if os.path.exists(path):
                        path = path
                    else:
                        path = os.path.join(APP_RESOURCES, image["path"])
                    x = image["x"]
                    y = image["y"]
                    width = image["width"]
                    self.insert_img(path, x, y, width)

            # table
            for table in self.tables:
                if (table[6] is None) or (table[6] == config["page_id"]):
                    tb_x = table[0]
                    tb_y = table[1]
                    tb_width = table[2]
                    tb_height = table[3]
                    tb_data = table[4]
                    tb_table_style = table[5]
                    table_style_def = table[7]
                    colWidth = table[8]
                    self.insert_table(tb_x, tb_y, tb_width, tb_height, tb_data, tb_table_style, table_style_def, colWidth)

            # coords corner bbox
            if 'map' in config:
                try:
                    show_coords_bbox = config["params"]["show_coords_bbox"]
                except KeyError:
                    show_coords_bbox = True  # default if no conf entry

                if show_coords_bbox:
                    width = config["map"]["width"]
                    height = config["map"]["height"]
                    corners = [ll_x, ll_y, (ll_x + width), (ll_y + height)]
                    self.insert_corner_coords(self.bbox, corners)

            # coords
            if 'map' in config:
                try:
                    show_coords = config["params"]["show_coords"]["active"]
                    show_coords_gridsize = config["params"]["show_coords"]["gridsize"] #priority if gridsize
                    nb_points=0
                except KeyError:
                    show_coords_gridsize = 0
                    show_coords = False

                if not show_coords: # if no gridsize, check for nb_points
                    try:
                        show_coords = config["params"]["show_coords"]["active"]
                        nb_points = config["params"]["show_coords"]["nb_points"]
                    except KeyError:
                        show_coords = False

                try:
                    tic_type = config["params"]["show_coords"]["tic_type"] # none, tic or line
                    tic_color = config["params"]["show_coords"]["tic_color"]
                except KeyError:
                    tic_type = "tic" #default
                    tic_color = [0,0,0,1]

                if show_coords:
                    width = config["map"]["width"]
                    height = config["map"]["height"]
                    corners = [ll_x, ll_y, (ll_x + width), (ll_y + height)]
                    self.insert_coords(self.bbox, corners, scale, mapcenter[0], mapcenter[1], width, height, ll_x, ll_y,
                                       show_coords_gridsize, nb_points, tic_type, tic_color)


            # scalebar
            if 'scalebar' in config:
                scalebar = config["scalebar"]
                if scalebar["active"]:
                    self.scale_bar(scalebar["max_width_mm"], scale, scalebar["x"], scalebar["y"], scalebar["linecolor"],
                                   scalebar["fontcolor"], scalebar["font"], scalebar["fontsize"], scalebar["linewidth"],
                                   scalebar["has_background"], scalebar["backgroundcolor"])
            else:
                logger.debug('No scalebar to draw..')


            # QR Code
            # JSON Params: x, y, width, value
            if 'qrcode' in config:
                qrcode_json = config["qrcode"]
                ll_x = qrcode_json["x"]
                ll_y = qrcode_json["y"]
                box_width = qrcode_json["width"]
                value= qrcode_json["value"]

                # if add_extent = true then add bbox extent to URL params
                if 'add_extent' in qrcode_json:
                    add_extent = qrcode_json['add_extent']
                    if add_extent and self.bbox: # use map bbox for extent
                        round_bbox = [round(v) for v in self.bbox]
                        value += '?urlparams=true&extent=' + ','.join(str(e) for e in round_bbox) + '&extent_srid=' + srid

                # if add_geom = true then add wkt in params TODO
                # if 'add_geom' in qrcode_json:
                #     add_geom = qrcode_json['add_geom']
                #     if add_geom and self.geom:
                #         value += '?geom=' + self.geom.wkt

                logger.info('QRCode URL: ' + value)

                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=2,
                )
                qr.add_data(value)
                qr.make(fit=True)

                pil_img = qr.make_image(fill_color="black", back_color="white") # make pil img
                img = ImageReader(pil_img.get_image()) # need ImageReader for drawImage()

                if img is not None:
                    self.canvas.drawImage(img,
                                          ll_x * mm, ll_y * mm,
                                          width=box_width * mm, height=box_width * mm,
                                          mask='auto')


            # final step -----------------------------------------------------------------------
            if (nb_confgis > i + 1) and (config["page_id"] == self.configs[i + 1]["page_id"]):
                logger.debug('Same page found. Keep working on it...')
                pass
            else:
                # close page -------------------------------- #
                self.canvas.showPage()

                if 'template_pdf' in config and config["template_pdf"]["active"]:
                    try:
                        template_path = os.path.join(APP_RESOURCES, config["template_pdf"]["name"])
                        self.merge_pdf(template_path)
                    except Exception as err:
                        logger.debug(err)
                        self.canvas.save()  # closing dynamic pdf ...
                        self.isclosed = True
                        pass
                else:
                    self.canvas.save()  # closing dynamic pdf ...
                    self.isclosed = True

                # pdf files
                if 'pdf_files' in config:
                    for pdf_file in config["pdf_files"]:
                        path = os.path.join(APP_RESOURCES, pdf_file["path"])
                        io = open(path, mode='rb')
                        if pdf_file["after"]:
                            self.append_pdf(self.output, io)
                        else:
                            self.append_pdf(io, self.output)

                if need_append:
                    self.append_pdf(self.tmp_output, self.output)


    def get_color_from_drawtools_style(self, style_object):
        return [float(style_object['r']) / 255,
                  float(style_object['g']) / 255,
                  float(style_object['b']) / 255,
                  float(style_object['a'])]

    def insert_drawings(self, srid, scale, mapcenter_x, mapcenter_y, width, height, ll_x, ll_y, drawing_features):
        # Scalargis Drawtools elements

        xmin, ymin, xmax, ymax = self.calc_bbox(scale, mapcenter_x, mapcenter_y, width, height)
        xfactor = abs(xmax - xmin) / width
        yfactor = abs(ymax - ymin) / height
        self.canvas.saveState()
        self.canvas.translate(ll_x * mm, ll_y * mm)

        # polygons
        for elt in drawing_features:
            in_crs = pyproj.CRS(elt['crs']['properties']['name'])
            geom_type = elt['geometry']['type']
            coords = elt['geometry']['coordinates']
            style = elt['properties']['state']
            size = int(style['size'])
            fill_color = self.get_color_from_drawtools_style(style['fill'])
            stroke_color = self.get_color_from_drawtools_style(style['stroke'])
            if geom_type == 'Polygon':
                coords_paper = []
                for coord in coords[0]:
                    point = geometry.Point(coord)
                    point_layout_srid = geo.transformGeom2(point, 'epsg:{0}'.format(in_crs.to_epsg()),
                                                          'epsg:{0}'.format(srid))
                    x = (point_layout_srid[0] - xmin) / xfactor
                    y = (point_layout_srid[1] - ymin) / yfactor
                    coords_paper.append([x, y])
                self.draw_path(coords_paper, size, stroke_color, True, fill_color)


        # lines
        for elt in drawing_features:
            in_crs = pyproj.CRS(elt['crs']['properties']['name'])
            geom_type = elt['geometry']['type']
            coords = elt['geometry']['coordinates']
            style = elt['properties']['state']
            size = int(style['size'])
            fill_color = self.get_color_from_drawtools_style(style['fill'])
            stroke_color = self.get_color_from_drawtools_style(style['stroke'])
            if geom_type == 'LineString':
                coords_paper = []
                for coord in coords:
                    point = geometry.Point(coord)
                    point_layout_srid = geo.transformGeom2(point, 'epsg:{0}'.format(in_crs.to_epsg()),
                                                          'epsg:{0}'.format(srid))
                    x = (point_layout_srid[0] - xmin) / xfactor
                    y = (point_layout_srid[1] - ymin) / yfactor
                    coords_paper.append([x, y])
                self.draw_path(coords_paper, size, stroke_color)

        # points
        for elt in drawing_features:
            in_crs = pyproj.CRS(elt['crs']['properties']['name'])
            geom_type = elt['geometry']['type']
            coords = elt['geometry']['coordinates']
            style = elt['properties']['state']
            size = int(style['size'])
            fill_color = self.get_color_from_drawtools_style(style['fill'])
            stroke_color = self.get_color_from_drawtools_style(style['stroke'])
            if geom_type == 'Point':
                point = geometry.Point(coords)
                point_layout_srid = geo.transformGeom2(point, 'epsg:{0}'.format(in_crs.to_epsg()), 'epsg:{0}'.format(srid))
                x = (point_layout_srid[0] - xmin) / xfactor
                y = (point_layout_srid[1] - ymin) / yfactor

                if style['draw_geom']:
                    self.draw_circle(x, y, size / 4, stroke_color, fill=True, fillcolor=fill_color)

                if style['draw_symbol']:
                    if style['symbol_type'] == 'triangle':
                        self.draw_triangle(x, y, size / 4, fill_color, stroke_color, rotate=90)
                    if style['symbol_type'] == 'circle':
                        self.draw_circle(x, y, size / 4, stroke_color, fill=True, fillcolor=fill_color)
                    if style['symbol_type'] == 'star':
                        self.draw_star(x, y, size / 3, fill_color, stroke_color)
                    if style['symbol_type'] == 'square':
                        self.draw_rectangle(x, y,size / 3, size / 3, fill_color, stroke_color)
                    if style['symbol_type'] == 'x':
                        self.draw_cross(x, y,size / 3, stroke_color, rotate=45)
                    if style['symbol_type'] == 'cross':
                        self.draw_cross(x, y, size / 3, stroke_color)

        # text
        for elt in drawing_features:
            in_crs = pyproj.CRS(elt['crs']['properties']['name'])
            geom_type = elt['geometry']['type']
            coords = elt['geometry']['coordinates']
            style = elt['properties']['state']
            size = int(style['size'])

            fill_color = self.get_color_from_drawtools_style(style['fill'])
            del fill_color[-1]  # need remove alfa to work
            stroke_color = self.get_color_from_drawtools_style(style['stroke'])
            stroke_color[3] = 0.4 # fixed transparency for background color

            if style['draw_text']:
                point = geometry.Point(coords)
                point_layout_srid = geo.transformGeom2(point, 'epsg:{0}'.format(in_crs.to_epsg()), 'epsg:{0}'.format(srid))
                x = (point_layout_srid[0] - xmin) / xfactor
                y = (point_layout_srid[1] - ymin) / yfactor
                txt_value = style['text_value']
                txt_size = int(style['text_size'][:-2]) - 1
                txt_style = style['text_style']
                txt_font = style['text_font']
                txt_width = (txt_size / 5.5) * len(str(txt_value))
                txt_options = {"borderColor": stroke_color, "backColor": stroke_color,
                               "borderPadding": (1,2,2+(txt_size - 7),2),
                               "borderRadius": 3, "borderWidth": 1}

                self.insert_paragraph(x, y, txt_width, txt_size * 4, txt_value,
                                      font="Helvetica", fontsize=txt_size, fontcolor=fill_color,
                                      leading=9, style="default", options=txt_options,
                                      paper_shift_x=0, paper_shift_y=0)


        # ending:
        self.canvas.restoreState()



    def draw_features(self,scale, mapcenter_x, mapcenter_y, width, height, ll_x, ll_y,features):
        # draw json drawing_features
        # only from generate
        # srid from config

        xmin, ymin, xmax, ymax = self.calc_bbox(scale, mapcenter_x, mapcenter_y, width, height)
        xfactor = abs(xmax - xmin) / width
        yfactor = abs(ymax - ymin) / height
        self.canvas.saveState()
        self.canvas.translate(ll_x * mm, ll_y * mm)

        for f in features['features']:
            if f['geometry']['type'] == 'Polygon':
                coords = f['geometry']['coordinates'][0]
                coords_paper = []
                for coord in coords:
                    x = (coord[0] - xmin) / xfactor
                    y = (coord[1] - ymin) / yfactor
                    coords_paper.append([x,y])
                fill = f['properties']['_style']['fill']
                fill_color = self.get_color_array_from_rgba_string(fill['color'])
                stroke = f['properties']['_style']['stroke']
                stroke_color = self.get_color_array_from_rgba_string(stroke['color'])
                stroke_width = f['properties']['_style']['stroke']['width']
                self.draw_path(coords_paper,stroke_width,stroke_color,True,fill_color)
            elif f['geometry']['type'] == 'LineString':
                coords = f['geometry']['coordinates']
                coords_paper = []
                for coord in coords:
                    x = (coord[0] - xmin) / xfactor
                    y = (coord[1] - ymin) / yfactor
                    coords_paper.append([x,y])
                stroke = f['properties']['_style']['stroke']
                stroke_color = self.get_color_array_from_rgba_string(stroke['color'])
                stroke_width = f['properties']['_style']['stroke']['width']
                self.draw_path(coords_paper,stroke_width,stroke_color)
            elif f['geometry']['type'] == 'Point':
                coords = f['geometry']['coordinates']
                x = (coords[0] - xmin) / xfactor
                y = (coords[1] - ymin) / yfactor

                paper_shift_x = f['geometry']['paper_shift_x'] if 'paper_shift_x' in f['geometry'] else 0
                paper_shift_y = f['geometry']['paper_shift_y'] if 'paper_shift_y' in f['geometry'] else 0

                if f['properties']['type'] == 'Point':
                    point_radius = f['properties']['_style']['image']['radius']
                    stroke = f['properties']['_style']['image']['stroke']
                    stroke_color = self.get_color_array_from_rgba_string(stroke['color'])
                    fill = f['properties']['_style']['image']['fill']
                    fill_color = self.get_color_array_from_rgba_string(fill['color'])
                    self.draw_circle(x, y, point_radius/4, stroke_color, fill=True, fillcolor=fill_color)


                elif f['properties']['type'] == 'Paragraph':
                    txt = f['properties']['_style']['text']['text']
                    txt_size = f['properties']['_style']['text']['width']
                    color = f['properties']['_style']['text']['stroke']['color']
                    width = f['properties']['_style']['width']
                    height = f['properties']['_style']['height']
                    txt_color = self.get_color_array_from_rgba_string(color)

                    options = f['properties']['_style']['options'] if 'options' in f['properties']['_style'] else {}

                    self.insert_paragraph(x,y,width,height,txt,fontsize=txt_size, fontcolor=txt_color, options=options,
                                          paper_shift_x=paper_shift_x, paper_shift_y=paper_shift_y)

                elif f['properties']['type'] == 'Text':
                    txt = f['properties']['_style']['text']['text']
                    txt_size = f['properties']['_style']['text']['width']
                    color = f['properties']['_style']['text']['stroke']['color']
                    txt_color = self.get_color_array_from_rgba_string(color)

                    if 'mode' in f['properties']['_style']['text']:
                        txt_mode = f['properties']['_style']['text']['mode']
                    else:
                        txt_mode = None

                    self.insert_string(x, y, txt, font="Helvetica", fontsize=txt_size, fontcolor=txt_color, mode=txt_mode, rotation=0)
                elif f['properties']['type'] == 'Symbol':
                    sy_type = f['properties']['_style']['shape']['type']
                    if sy_type == 'circle':
                        graphic = 	{
                            "type": "circle",
                            "fill":True
                            }
                        graphic['line_color'] = self.get_color_array_from_rgba_string(f['properties']['_style']['shape']['stroke']['color'])
                        graphic['fill_color'] = self.get_color_array_from_rgba_string(f['properties']['_style']['shape']['fill']['color'])
                        graphic['x'] = int(x)
                        graphic['y'] = int(y)
                        graphic['size'] = int(f['properties']['_style']['shape']['size']) * 0.5
                        self.draw_graphic(graphic)
                    elif sy_type == 'square':
                        graphic_size = int(f['properties']['_style']['shape']['size'])
                        graphic = 	{
                            "type": "rectangle",
                            "fill":True
                            }
                        graphic['stroke_color'] = self.get_color_array_from_rgba_string(f['properties']['_style']['shape']['stroke']['color'])
                        graphic['fill_color'] = self.get_color_array_from_rgba_string(f['properties']['_style']['shape']['fill']['color'])
                        graphic['x'] = int(x - (graphic_size * 0.5))
                        graphic['y'] = int(y - (graphic_size * 0.5))
                        graphic['width'] = graphic_size
                        graphic['height'] = graphic_size
                        self.draw_graphic(graphic)
                    elif sy_type == 'x':
                        graphic_size = int(f['properties']['_style']['shape']['size'])
                        graphic = 	{
                            "type": "x",
                            "fill":True
                            }
                        graphic['stroke_color'] = self.get_color_array_from_rgba_string(f['properties']['_style']['shape']['stroke']['color'])
                        graphic['x'] = int(x)
                        graphic['y'] = int(y)
                        graphic['width'] = graphic_size
                        self.draw_graphic(graphic)
                    elif sy_type == 'cross':
                        graphic_size = int(f['properties']['_style']['shape']['size'])
                        graphic = 	{
                            "type": "cross",
                            "fill":True
                            }
                        graphic['stroke_color'] = self.get_color_array_from_rgba_string(f['properties']['_style']['shape']['stroke']['color'])
                        graphic['x'] = int(x)
                        graphic['y'] = int(y)
                        graphic['width'] = graphic_size
                        self.draw_graphic(graphic)
                    elif sy_type == 'star':
                        graphic_size = int(f['properties']['_style']['shape']['size'])
                        graphic = 	{
                            "type": "star",
                            "fill":True
                            }
                        graphic['stroke_color'] = self.get_color_array_from_rgba_string(f['properties']['_style']['shape']['stroke']['color'])
                        graphic['fill_color'] = self.get_color_array_from_rgba_string(f['properties']['_style']['shape']['fill']['color'])
                        graphic['x'] = int(x)
                        graphic['y'] = int(y)
                        graphic['width'] = graphic_size
                        self.draw_graphic(graphic)
                    elif sy_type == 'triangle':
                        graphic_size = int(f['properties']['_style']['shape']['size'])
                        graphic = 	{
                            "type": "triangle",
                            "fill":True
                            }
                        graphic['stroke_color'] = self.get_color_array_from_rgba_string(f['properties']['_style']['shape']['stroke']['color'])
                        graphic['fill_color'] = self.get_color_array_from_rgba_string(f['properties']['_style']['shape']['fill']['color'])
                        graphic['x'] = int(x)
                        graphic['y'] = int(y)
                        graphic['width'] = graphic_size
                        self.draw_graphic(graphic)
                else:
                    logger.debug('Invalid Point subtype feature drawing Type')
            else:
                logger.debug('Invalid feature drawing Type')

        self.canvas.restoreState()

    def get_color_array_from_rgba_string(self, rgba_string):
        x = re.search('\((.*)\)', rgba_string)
        x = x.group(1)
        return list(map(float, x.split(',')))

    def draw_geometry(self, scale, mapcenter_x, mapcenter_y, width, height, ll_x, ll_y, geom, style, draw_centroid=False):
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

        xmin, ymin, xmax, ymax = self.calc_bbox(scale, mapcenter_x, mapcenter_y, width, height)
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

            self.canvas.saveState()
            self.canvas.translate(ll_x * mm, ll_y * mm)

            if gm.geom_type == 'Point' or gm.geom_type == 'MultiPoint':
                my_stroke = colors.Color(point_stroke_color[0], point_stroke_color[1], point_stroke_color[2],
                                         point_stroke_color[3])
                self.canvas.setStrokeColor(my_stroke)
                myfill = colors.Color(point_fill_color[0], point_fill_color[1], point_fill_color[2], point_fill_color[3])
                self.canvas.setFillColor(myfill)

                if gm.geom_type == 'Point':
                    gm = geometry.MultiPoint([gm])

                for i in range(len(gm.geoms)):
                    logger.debug(gm.geoms[i])
                    x = (gm.geoms[i].x - xmin) / xfactor
                    y = (gm.geoms[i].y - ymin) / yfactor
                    self.canvas.circle(x * mm, y * mm, point_size * mm, fill=1)

            elif gm.geom_type == 'LineString' or gm.geom_type == 'MultiLineString':
                my_stroke = colors.Color(line_color[0], line_color[1], line_color[2], line_color[3])
                self.canvas.setStrokeColor(my_stroke)

                if gm.geom_type == 'LineString':
                    gm = geometry.MultiLineString([gm])

                for i in range(len(gm.geoms)):
                    logger.debug(gm.geoms[i])
                    path = self.canvas.beginPath()
                    ox = (float(gm.geoms[i].coords[0][0]) - xmin) / xfactor
                    oy = (float(gm.geoms[i].coords[0][1]) - ymin) / yfactor
                    path.moveTo(ox * mm, oy * mm)
                    for p in gm.geoms[i].coords:
                        x = (p[0] - xmin) / xfactor
                        y = (p[1] - ymin) / yfactor
                        if line_vertice:
                            self.canvas.circle(x * mm, y * mm, vertice_size * mm, fill=0)
                        path.lineTo(x * mm, y * mm)
                    self.canvas.setLineWidth(line_width)
                    if line_dash:
                        self.canvas.setDash(6, 3)
                    self.canvas.drawPath(path, stroke=1, fill=0)

            elif gm.geom_type == 'Polygon' or gm.geom_type == 'MultiPolygon':
                my_stroke = colors.Color(polygon_stroke_color[0], polygon_stroke_color[1], polygon_stroke_color[2],
                                         polygon_stroke_color[3])
                self.canvas.setStrokeColor(my_stroke)
                myfill = colors.Color(polygon_fill_color[0], polygon_fill_color[1], polygon_fill_color[2],
                                      polygon_fill_color[3])
                self.canvas.setFillColor(myfill)

                if gm.geom_type == 'Polygon':
                    gm = geometry.MultiPolygon([gm])

                if polygon_stroke_dash:
                    self.canvas.setDash(6, 3)
                self.canvas.setLineWidth(polygon_stroke_width)

                def draw_geom_ring(ring):
                    logger.debug(ring)
                    path = self.canvas.beginPath()
                    start_x = (float(ring.coords[0][0]) - xmin) / xfactor
                    start_y = (float(ring.coords[0][1]) - ymin) / xfactor
                    path.moveTo(start_x * mm, start_y * mm)
                    for p in ring.coords:
                        x = (p[0] - xmin) / xfactor
                        y = (p[1] - ymin) / yfactor
                        if polygon_vertice:
                            self.canvas.circle(x * mm, y * mm, vertice_size * mm, fill=0)
                        path.lineTo(x * mm, y * mm)
                    self.canvas.drawPath(path, stroke=1, fill=1)

                for i in range(len(gm.geoms)): # draw exterior rings
                    draw_geom_ring(gm.geoms[i].exterior)
                    for ii in range(len(gm.geoms[i].interiors)):  # draw interior rings
                        draw_geom_ring(gm.geoms[i].interiors[ii])

            else:
                logger.warning("Bad geom type")

            self.canvas.restoreState()


    def merge_pdf(self, template_pdf_path):
        logger.debug("Pdf Template: " + template_pdf_path)

        # need to be the last method because the canvas is saved before the merge
        # template_pdf goes on top of dynamic pdf
        pdf_file = PdfReader(open(template_pdf_path, mode='rb'))

        self.canvas.save()  # save needed ! Closing dynamic pdf ...
        self.isclosed = True
        dynamic_pdf = PdfReader(self.output)

        writer = PdfWriter()
        page = dynamic_pdf.pages[0]
        page.merge_page(pdf_file.pages[0])
        writer.add_page(dynamic_pdf.pages[0])

        writer.write(self.output)


    def append_pdf(self, first, second):
        # append the second pdf to the first one .....
        first = PdfReader(first)
        second = PdfReader(second)
        merger = PdfMerger()
        merger.append(first)
        merger.append(second)
        merger.write(self.output)


    def insert_map(self, serv_type, scale, srid, mapcenter_x, mapcenter_y, width, height, img_format,
                   ll_x, ll_y, url, layers, quality=2, transparent=True, style=None, cql_filter=None, opacity=1,
                   url_params=[]):
        # insert map to canvas. Need savepdf() if used without generate
        xmin, ymin, xmax, ymax = self.calc_bbox(scale, mapcenter_x, mapcenter_y, width, height)

        if serv_type == 'wms':
            img = self.wms_getmap(url, layers, [xmin, ymin, xmax, ymax],
                                  quality * width * mm, quality * height * mm, srid, img_format, style,
                                  cql_filter=cql_filter, opacity=opacity, url_params=url_params)

        elif serv_type == 'esri_rest':
            img = self.esri_rest_getmap(url, layers, [xmin, ymin, xmax, ymax], width * mm, height * mm, srid,
                                        img_format, transparent, quality, opacity=opacity)
        else:
            logger.warning("Service type not supported.")
            return

        if img is not None:
            self.canvas.drawImage(img, ll_x * mm, ll_y * mm, width=width * mm, height=height * mm,
                                  mask='auto')
            #  mask=[255, 255, 255, 255, 255, 255])


    def insert_legend(self, serv_type, url, layer, x, y, width, gs_vendor_options='', img_format="image/png",
                      version='1.3.0', style=''):
        if serv_type == 'wms':
            img = self.wms_GetLegendGraphic(url, layer, img_format, version,gs_vendor_options, style)
        else:
            logger.warning("Service type not supported.")
            return

        if img is not None:
            if width is not None:
                iw, ih = img.getSize()
                iw *= 0.352778  # convert point to mm
                ih *= 0.352778  # convert point to mm
                aspect = float(ih) / float(iw)
                h = width * aspect
                self.canvas.drawImage(img, x * mm, y * mm, width=width * mm, height=h * mm)
            else:
                self.canvas.drawImage(img, x * mm, y * mm, mask='auto')


    def insert_string(self, x, y, txt, font="Helvetica", fontsize=10, fontcolor=None, mode=None, rotation=0):
        # insert text to canvas. Need savepdf() if used without generate
        # mode: position is left by default or can be center and right
        self.canvas.saveState()

        if fontcolor is None:
            fontcolor = [0, 0, 0, 1]
        self.canvas.setFillColorRGB(fontcolor[0], fontcolor[1], fontcolor[2])
        self.canvas.setFont(font, fontsize)

        self.canvas.translate(x * mm, y * mm)
        self.canvas.rotate(int(rotation))

        if mode == 'center':
            self.canvas.drawCentredString(0, 0, txt)
        elif mode == 'right':
            self.canvas.drawRightString(0, 0, txt)
        else:
            self.canvas.drawString(0, 0, txt)
        self.canvas.setFillColorRGB(0, 0, 0)
        self.canvas.restoreState()


    def insert_corner_coords(self, bbox, corners):
        # insert coords strings at map corner
        ul_x_txt = "x = " + str(int(bbox[0]))
        ul_y_txt = "y = " + str(int(bbox[3]))
        lr_x_txt = "x = " + str(int(bbox[2]))
        lr_y_txt = "y = " + str(int(bbox[1]))

        self.insert_string(corners[0], corners[3] + 0.5, ul_y_txt, fontsize=6)
        self.insert_string(corners[2], corners[1] - 2, lr_y_txt, fontsize=6, mode='right')

        self.canvas.saveState()
        self.canvas.translate((corners[0] - 0.5) * mm, (corners[3]) * mm)
        self.canvas.rotate(90)
        self.insert_string(0, 0, ul_x_txt, fontsize=6, mode='right')
        self.canvas.restoreState()

        self.canvas.saveState()
        self.canvas.translate((corners[2] + 2) * mm, (corners[1]) * mm)
        self.canvas.rotate(90)
        self.insert_string(0, 0, lr_x_txt, fontsize=6)
        self.canvas.restoreState()

    def insert_coords(self, bbox, corners, scale, mapcenter_x, mapcenter_y, width, height, ll_x, ll_y, gridsize,
                      nb_points,tic_type, tic_color):
        # insert coords and tics
        min_x = int(bbox[0])
        max_x = int(bbox[2])
        min_y = int(bbox[1])
        max_y = int(bbox[3])

        if (gridsize>0):
            x_coords = self.GridCoordsBySize(min_x, max_x, gridsize, 5)
            y_coords = self.GridCoordsBySize(min_y, max_y, gridsize, 5)
        else:
            # begin with y and get interval for x
            y_coords,y_interval  = self.gridCoordsByNumOfPoints(min_y, max_y, nb_points)
            x_coords = self.GridCoordsBySize(min_x, max_x, y_interval, 5)

        xmin, ymin, xmax, ymax = self.calc_bbox(scale, mapcenter_x, mapcenter_y, width, height)
        xfactor = abs(xmax - xmin) / width
        yfactor = abs(ymax - ymin) / height

        self.canvas.saveState()
        self.canvas.translate(ll_x * mm, ll_y * mm)

        for yc in y_coords:
            self.insert_string(-2, ((yc - ymin) / yfactor) - 0.5, str(yc), fontsize=6, mode='right')
            self.draw_cross(0, (yc - ymin) / yfactor, 2, [0, 0, 0, 0.7])
            self.insert_string(width + 2, ((yc - ymin) / yfactor) - 0.5, str(yc), fontsize=6, mode='left')
            self.draw_cross(width, (yc - ymin) / yfactor, 2, [0, 0, 0, 0.7])


        for xc in x_coords:
            self.insert_string((xc- xmin)/xfactor, -3, str(xc), fontsize=6, mode='center')
            self.draw_cross((xc - xmin) / xfactor, 0 , 2, [0, 0, 0, 0.7])
            self.insert_string((xc - xmin) / xfactor, height + 3, str(xc), fontsize=6, mode='center')
            self.draw_cross((xc - xmin) / xfactor, height, 2, [0, 0, 0, 0.7])
            for yc in y_coords:
                if tic_type == 'tic':
                    self.draw_cross((xc- xmin)/xfactor, (yc-ymin)/yfactor, 2, tic_color) # tic marks
                elif tic_type == 'line':
                    x_line = [[(xc - xmin) / xfactor, 0],[(xc - xmin) / xfactor, height]]
                    self.draw_path(x_line,1,tic_color)
                    y_line = [[0, (yc-ymin)/yfactor],[width, (yc-ymin)/yfactor]]
                    self.draw_path(y_line,1,tic_color)

        self.canvas.restoreState()


    def insert_paragraph(self, x, y, width, height, txt, font="Helvetica", fontsize=8, fontcolor=None, leading=9,
                         style="default",options={}, paper_shift_x=0, paper_shift_y=0):
        # paper_shift: shift x and y in mm

        x = x + paper_shift_x
        y = y + paper_shift_y

        if fontcolor is None:
            fontcolor = [0, 0, 0, 1]

        styles = {
            'default': ParagraphStyle(
                'default',
                fontName= options['fontName'] if 'fontName' in options else font,
                fontSize=options['fontSize'] if 'fontSize' in options else fontsize,
                leading=options['leading'] if 'leading' in options else leading,  # =9,
                leftIndent=options['leftIndent'] if 'leftIndent' in options else 0,
                rightIndent=options['rightIndent'] if 'rightIndent' in options else 0,
                firstLineIndent=options['firstLineIndent'] if 'firstLineIndent' in options else 0,
                alignment=options['alignment'] if 'alignment' in options else TA_JUSTIFY,
                spaceBefore=options['spaceBefore'] if 'spaceBefore' in options else 0,
                spaceAfter=options['spaceAfter'] if 'spaceAfter' in options else 0,
                bulletFontName=options['bulletFontName'] if 'bulletFontName' in options else 'Times-Roman',
                bulletFontSize=options['bulletFontSize'] if 'bulletFontSize' in options else 10,
                bulletIndent=options['bulletIndent'] if 'bulletIndent' in options else 0,
                textColor=options['textColor'] if 'textColor' in options else fontcolor,
                wordWrap=options['wordWrap'] if 'wordWrap' in options else None,
                borderWidth=options['borderWidth'] if 'borderWidth' in options else 0,
                borderPadding=options['borderPadding'] if 'borderPadding' in options else 0,
                borderRadius=options['borderRadius'] if 'borderRadius' in options else None,
                allowWidows=options['allowWidows'] if 'allowWidows' in options else 1,
                allowOrphans=options['allowOrphans'] if 'allowOrphans' in options else 0,
                textTransform=options['textTransform'] if 'textTransform' in options else None,  # 'uppercase' | 'lowercase' | None
                endDots=options['endDots'] if 'endDots' in options else None,
                splitLongWords=options['splitLongWords'] if 'splitLongWords' in options else 1,

                #borderColor=options['borderColor'] if 'borderColor' in options else None,
                borderColor=Color(options['borderColor'][0], options['borderColor'][1],
                                options['borderColor'][2],
                                alpha=options['borderColor'][3] if len(options['borderColor']) == 4 else 1) if 'borderColor' in options else None,
                backColor=Color(options['backColor'][0], options['backColor'][1],
                                options['backColor'][2],
                                alpha=options['backColor'][3] if len(options['backColor']) == 4 else 1) if 'backColor' in options else None
            ),
        }

        styles['title'] = ParagraphStyle(
            'title',
            parent=styles['default'],
            fontName='Helvetica-Bold',
            fontSize=24,
            leading=42
        )

        p = Paragraph(txt, styles[style])
        p.wrap(width * mm, height * mm)
        p.drawOn(self.canvas, x * mm, y * mm)


    def insert_img(self, path, x, y, width):
        # insert image in current page
        # img_path = os.path.join(APP_RESOURCES, path)
        try:
            w, h = self.get_image_size(path, width)
            self.canvas.drawImage(path, x * mm, y * mm, w * mm, h * mm, mask='auto')
        except Exception as err:
            logger.error('Cannot insert image %s' % path)
            return


    @staticmethod
    def get_image_size(path, width=None, height=None, factor=None):
        try:
            img = utils.ImageReader(path)
        except Exception as err:
            logger.error('Cannot open resource %s' % path)
            return

        iw, ih = img.getSize()
        iw *= 0.352778  # convert point to mm
        ih *= 0.352778  # convert point to mm
        aspect = float(ih) / float(iw)

        if width is not None:
            w = width
            h = w * aspect
            return w, h
        elif height is not None:
            h = height
            w = h / aspect
            return w, h
        elif factor is not None:
            w = iw * float(factor)
            h = w * aspect
            return w, h
        else:
            return iw, ih


    def calc_bbox(self, scale_denom, center_x, center_y, img_w, img_h, units='meter'):
        # INCHES_PER_UNIT_METERS = 39.37

        # pix_to_mm = 0.26458333
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

        res = 1 / ((1 / int(scale_denom)) * inch_per_units * magic)
        half_w = (img_w * res) / 2
        half_h = (img_h * res) / 2
        xmin = center_x - half_w
        ymin = center_y - half_h
        xmax = center_x + half_w
        ymax = center_y + half_h

        logger.debug(("BBox: " + str(xmin) + "," + str(ymin) + " - " + str(xmax) + "," + str(ymax)))

        self.bbox = [xmin, ymin, xmax, ymax]
        self.resolution = res
        return xmin, ymin, xmax, ymax


    @staticmethod
    def wms_getmap(server_url, layers, bbox, width, height, srs, img_format, styles=None, version='1.1.1',
                   cql_filter=None, opacity=1, url_params=[]):
        if styles is None:
            styles = ''

        url = replace_geoserver_url(server_url)

        if (url[:7] == 'http://') or (url[:8] == 'https://'):
            url = url + "?"
        else:
            url = 'http://%s?' % url

        url = url.replace('/gwc/service/', '/')  # for urls using GeoWebCache !

        url += 'service=WMS'
        url += '&version=%s' % version
        url += '&request=GetMap'
        url += '&layers=%s' % urllib.parse.quote(layers)  # cm_faro:municipal_ln
        url += '&styles=%s' % styles
        url += '&bbox=%s,%s,%s,%s' % (bbox[0], bbox[1], bbox[2], bbox[3])
        url += '&width=%s' % int(width)  # 658
        url += '&height=%s' % int(height)  # 768
        url += '&srs=EPSG:%s' % srs  # 27493
        url += '&transparent=true'
        url += '&format=%s' % img_format  # image/jpeg
        if (cql_filter):
            url += '&cql_filter=%s' % urllib.parse.quote_plus(cql_filter)
        if url_params and len(url_params) > 0:
            for p in url_params:
                url += '&{0}={1}'.format(p[0], p[1])

        logger.info("WMS: " + url)
        try:
            #For performance reasons, only change alpha pixel value if opacity is lower than one (changed by user)
            if opacity == 1:
                img = ImageReader(url)
            else:
                img = get_image_with_opacity(url, opacity)

        except Exception as err:
            img = None
            logger.warning(err)
        return img


    @staticmethod
    def wms_GetLegendGraphic(server_url, layer, img_format="image/png", version='1.1.1',gs_vendor_options='', style=''):
        '''
        if (server_url[:7] == 'http://') or (server_url[:8] == 'https://'):
            url = server_url + "?"
        else:
            url = 'http://%s?' % server_url

        url = replace_geoserver_url(url)
        '''
        url = replace_geoserver_url(server_url)

        if (url[:7] == 'http://') or (url[:8] == 'https://'):
            url = url + "?"
        else:
            url = 'http://%s?' % url

        url += 'service=WMS'
        url += '&request=GetLegendGraphic'
        url += '&version=%s' % version
        url += '&layer=%s' % urllib.parse.quote(layer)
        url += '&format=%s' % img_format  # image/jpeg

        if style:
            url += '&style=' + style

        if gs_vendor_options:
            url += '&legend_options=' + gs_vendor_options
        else: # default
            url += '&legend_options=fontAntiAliasing:true;fontColor:0x000000;fontSize:10;bgColor:0xEEEEEE;dpi:180'

        logger.info("WMS: " + url)
        try:
            img = ImageReader(url)
        except Exception as err:
            img = None
            logger.warning(err)
        return img


    @staticmethod
    def esri_rest_getmap(server_url, layers, bbox, width, height, srs, imgformat='PNG32', transparent=True, dpi=90, opacity=1):
        if (server_url[:7] == 'http://') or (server_url[:8] == 'https://'):
            url = server_url
        else:
            url = 'http://%s?' % server_url

        if 'export' not in url:
            url += '/export?'

        if '?' not in url:
            url += '?'

        url += 'F=image'
        url += '&FORMAT=%s' % imgformat
        url += '&TRANSPARENT=%s' % transparent
        url += '&SIZE=%s,%s' % (width, height)
        url += '&BBOX=%s,%s,%s,%s' % (bbox[0], bbox[1], bbox[2], bbox[3])
        url += '&BBOXSR=%s&IMAGESR=%s' % (srs, srs)
        url += '&dpi=%s' % dpi

        if (layers):
            url += '&layers=%s' % layers

        logger.info("ESRI REST: " + url)
        try:
            #For performance reasons, only change alpha pixel value if opacity is lower than one (changed by user)
            if opacity == 1:
                img = ImageReader(url)
            else:
                img = get_image_with_opacity(url, opacity)
        except Exception as err:
            img = None
            logger.warning(err)
        return img


    def draw_circle(self, x1, y1, point_size, stroke_color, fill=False, fillcolor=None):
        #self.canvas.saveState()

        line_color = colors.Color(stroke_color[0], stroke_color[1], stroke_color[2], stroke_color[3])
        self.canvas.setStrokeColor(line_color)
        if fill:
            if fillcolor is not None:
                bckcol = colors.Color(fillcolor[0], fillcolor[1], fillcolor[2],
                                      fillcolor[3])
                self.canvas.setFillColor(bckcol)

        self.canvas.circle(x1 * mm, y1 * mm, point_size * mm, fill=1)
        #self.canvas.restoreState()

    def draw_rectangle(self, x, y, width, height, fillcolor, strokecolor=None):
        # draw rectangle
        # config exemple: {"type":"rectangle", "x":50,"y":50,"width":50,"height":50,"fill_color":[0.2,0.5,0.9,0.5]}
        # {"type":"rectangle", "x":50,"y":50,"width":50,"height":50,"fill_color":[0.2,0.5,0.9,0.5], "stroke_color": [1,0.5,0.9,0.5]}

        self.canvas.saveState()
        fill_color = colors.Color(fillcolor[0], fillcolor[1], fillcolor[2], fillcolor[3])
        if strokecolor is not None:
            stroke_color = colors.Color(strokecolor[0], strokecolor[1], strokecolor[2], strokecolor[3])
            self.canvas.setStrokeColor(stroke_color)
        self.canvas.setFillColor(fill_color)

        self.canvas.rect(x * mm, y * mm, width * mm, height * mm, fill=1)
        self.canvas.restoreState()

    def draw_line(self, x1, y1, x2, y2):
        self.canvas.line(x1 * mm, y1 * mm, x2 * mm, y2 * mm)

    def draw_star(self, xcenter, ycenter, radius, fillcolor, strokecolor):

        p = self.canvas.beginPath()
        radius = radius / 2  # scaling
        p.moveTo(xcenter * mm, (ycenter + radius) * mm)

        angle = (2 * pi) * 2 / 5.0
        startangle = pi / 2.0
        for vertex in range(4):
            nextangle = angle*(vertex+1)+startangle
            x = xcenter + radius*cos(nextangle)
            y = ycenter + radius*sin(nextangle)
            p.lineTo(x * mm, y * mm)
        self.canvas.setStrokeColor(colors.Color(strokecolor[0],strokecolor[1],strokecolor[2],strokecolor[3]))
        self.canvas.setFillColor(colors.Color(fillcolor[0],fillcolor[1],fillcolor[2],fillcolor[3]))
        p.close()
        self.canvas.drawPath(p, fill=1)

    def draw_cross(self, xcenter, ycenter, radius, strokecolor, rotate=0):
        # rotate angle in degree
        p = self.canvas.beginPath()
        p.moveTo(xcenter * mm, ycenter * mm)

        radius = radius / 2 # scaling
        angle = pi / 2.0
        startangle = 0 + (rotate*2*pi/360)
        for vertex in range(4):
            nextangle = angle*(vertex+1)+startangle
            x = xcenter + radius*cos(nextangle)
            y = ycenter + radius*sin(nextangle)
            p.lineTo(x * mm, y * mm)
            p.moveTo(xcenter * mm, ycenter * mm)
        self.canvas.setStrokeColor(colors.Color(strokecolor[0],strokecolor[1],strokecolor[2],strokecolor[3]))
        p.close()
        self.canvas.drawPath(p)

    def draw_triangle(self, xcenter, ycenter, radius, fillcolor, strokecolor, rotate=0):
        # rotate angle in degree

        p = self.canvas.beginPath()
        radius = radius / 2  # scaling
        p.moveTo((xcenter + radius*cos(rotate*2*pi/360)) * mm, ((ycenter + radius*sin(rotate*2*pi/360))) * mm)

        angle = (2 * pi) / 3
        startangle = rotate*2*pi/360
        for vertex in range(2):
            nextangle = angle*(vertex+1)+startangle
            x = xcenter + radius*cos(nextangle)
            y = ycenter + radius*sin(nextangle)
            p.lineTo(x * mm, y * mm)
        self.canvas.setStrokeColor(colors.Color(strokecolor[0],strokecolor[1],strokecolor[2],strokecolor[3]))
        self.canvas.setFillColor(colors.Color(fillcolor[0],fillcolor[1],fillcolor[2],fillcolor[3]))
        p.close()
        self.canvas.drawPath(p, fill=1)

    def draw_path(self, coords, line_width, color, fill=False, fillcolor=None):
        # Draw path

        nb_coords = len(coords)
        if nb_coords < 2:
            logger.warning('Coords array does not have at least 2 points')
            return

        self.canvas.saveState()
        line_color = colors.Color(color[0], color[1], color[2], color[3])
        if fill:
            if fillcolor is not None:
                bckcol = colors.Color(fillcolor[0], fillcolor[1], fillcolor[2],
                                      fillcolor[3])
        self.canvas.setStrokeColor(line_color)
        self.canvas.setLineWidth(line_width)

        p = self.canvas.beginPath()
        p.moveTo(coords[0][0] * mm, coords[0][1] * mm)
        for i in range(1, nb_coords):
            p.lineTo(coords[i][0] * mm, coords[i][1] * mm)

        if fill:
            if fillcolor is not None:
                self.canvas.setFillColor(bckcol)
                p.close()

        if fill:
            self.canvas.drawPath(p, stroke=1, fill=1)
        else:
            self.canvas.drawPath(p)
        self.canvas.restoreState()


    def draw_graphic(self, graphic):
        try:
            fill = graphic["fill"]
            fillcolor = graphic["fill_color"]
        except KeyError:
            fill = False
            fillcolor = None

        try:
            stroke_color = graphic["stroke_color"]
        except KeyError:
            stroke_color = None

        if graphic["type"] == 'line':
            self.draw_path(graphic["coords"], graphic["line_width"], graphic["line_color"], fill, fillcolor)
        elif graphic["type"] == 'circle':
            self.draw_circle(graphic["x"], graphic["y"], graphic["size"], graphic["line_color"], fill, fillcolor)
        elif graphic["type"] == 'rectangle':
            self.draw_rectangle(graphic["x"], graphic["y"], graphic["width"],graphic["height"],graphic["fill_color"],stroke_color)
        elif graphic["type"] == 'star':
            self.draw_star(graphic["x"], graphic["y"], graphic["width"],graphic["fill_color"],stroke_color)
        elif graphic["type"] == 'triangle':
            self.draw_triangle(graphic["x"], graphic["y"], graphic["width"],graphic["fill_color"],stroke_color,rotate=40)
        elif graphic["type"] == 'cross':
            self.draw_cross(graphic["x"], graphic["y"], graphic["width"],stroke_color)
        elif graphic["type"] == 'x':
            self.draw_cross(graphic["x"], graphic["y"], graphic["width"],stroke_color, rotate=45)
        else:
            # compatibilty old configs?
            self.draw_path(graphic["coords"], graphic["line_width"], graphic["line_color"], fill, fillcolor)


    def scale_bar(self, max_width_mm, scale_denom, x_pos, y_pos, linecolor, fontcolor, font="Helvetica",
                  fontsize=8, linewidth=2, has_background=False, backgroundcolor=None):
        # compute and draw graphic scale

        if self.resolution is None:
            logger.warning("No BBox and resolution calculated yet !")
            return False

        vals = [5000000, 2000000, 1000000, 500000, 200000, 100000, 50000, 20000, 10000, 5000,
                2000, 1000, 500, 200, 100, 50, 20, 10, 5, 2, 1, 0.5, 0.1]
        vals_str = ['5000 km', '2000 km', '1000 km', '500 km', '200 km', '100 km', '50 km', '20 km', '10 km', '5 km',
                    '2 km', '1000 m', '500 m', '200 m', '100 m', '50 m', '20 m', '10 m', '5 m', '2 m', '1 m', '0.5 m',
                    '0.1 m']

        f = scale_denom * max_width_mm / 1000

        for v in range(len(vals)):
            if f >= vals[v]:
                scaleline_width = vals[v] * 1000 / scale_denom

                if has_background:
                    self.draw_path(
                        [[x_pos - 1, y_pos + 4], [x_pos - 1, y_pos - 1], [x_pos + scaleline_width + 1, y_pos - 1],
                         [x_pos + scaleline_width + 1, y_pos + 4]], linewidth, backgroundcolor, True, backgroundcolor)

                self.draw_path([[x_pos, y_pos + 3], [x_pos, y_pos], [x_pos + scaleline_width, y_pos],
                                [x_pos + scaleline_width, y_pos + 3]], linewidth, linecolor)
                self.insert_string(x_pos + (scaleline_width / 2), y_pos + 1, vals_str[v], font, fontsize,
                                   fontcolor, mode='center')
                break


    def insert_table(self, x, y, width, height, data, table_style, table_style_def=None, colWidth=None):
        # ----------------  named styles
        # grided, first row merged title, second row with fields gray bck.
        tab_style_generic1 = TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LINEABOVE', (0, 1), (-1, 1), 1, colors.blue),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('SPAN', (0, 0), (-1, 0)),  # merge first row
            ('BACKGROUND', (0, 1), (-1, 1), colors.lightgrey)
        ])

        # simple light gray grid all txt centered
        tab_style_all_txt_middle = TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('FONTSIZE',(0, 0), (-1, -1), 8)
        ])

        # simple green with middle txt algin
        tab_style_simple_green = TableStyle([
            ('BOX', (0, 0), (-1, -1), 2, colors.black),
            ('BACKGROUND', (0, 0), (-1, -1), colors.palegreen)
        ])

        # simple red with middle txt algin
        tab_style_simple_red = TableStyle([
            ('BOX', (0, 0), (-1, -1), 2, colors.black),
            ('BACKGROUND', (0, 0), (-1, -1), colors.red)
        ])

        # simple gray with middle txt algin
        tab_style_simple_gray = TableStyle([
            ('BOX', (0, 0), (-1, -1), 2, colors.black),
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey)
        ])
        # ----------------

        # data sample
        # [['Prédio a fracionar  30 ha', '', '', ''],
        # ['Cultura', 'UC (ha)', 'Área (ha)', 'Viável'],
        # ['Floresta', '11', '12', '13'],
        # ['Regadio', '21', '22', '23'],
        # ['Sequeiro', '31', '32', '33']]

        if colWidth:
            t = Table(data, colWidth)
        else:
            t = Table(data)


        if table_style_def:
            t.setStyle(TableStyle(table_style_def))
        else:
            if table_style == "tab_style_generic1":
                t.setStyle(tab_style_generic1)
            if table_style == "tab_style_simple_green":
                t.setStyle(tab_style_simple_green)
            if table_style == "tab_style_simple_red":
                t.setStyle(tab_style_simple_red)
            if table_style == "tab_style_simple_gray":
                t.setStyle(tab_style_simple_gray)
            if table_style == "tab_style_all_txt_middle":
                t.setStyle(tab_style_all_txt_middle)

        t.wrap(width * mm, height * mm)
        t.drawOn(self.canvas, x * mm, y * mm)


    def create_template(self, pagesize="A4_portrait", path_logo=None, north_arrow=False):
        # all in mm

        # default A4 portrait
        left_margin = 25
        right_margin = 10
        top_margin = 10
        bottom_margin = 20
        page_width = 210
        page_height = 297
        page_width_nomargin = page_width - right_margin - left_margin
        page_height_nomargin = page_height - top_margin - bottom_margin

        if pagesize == 'A3_portrait':
            left_margin = 25
            right_margin = 10
            top_margin = 10
            bottom_margin = 20
            page_width = 297
            page_height = 420
            page_width_nomargin = page_width - right_margin - left_margin
            page_height_nomargin = page_height - top_margin - bottom_margin

        # top rect
        self.canvas.rect(left_margin * mm, (page_height - top_margin - 40) * mm,
                         page_width_nomargin * mm, 40 * mm, stroke=1, fill=0)
        # top_rect divisions
        self.canvas.line((left_margin + 40) * mm, (page_height - top_margin - 39) * mm,
                         (left_margin + 40) * mm, (page_height - top_margin - 21) * mm)
        self.canvas.line((left_margin + 40) * mm, (page_height - top_margin - 19) * mm,
                         (left_margin + 40) * mm, (page_height - top_margin - 1) * mm)
        self.canvas.line((page_width - right_margin - 40) * mm, (page_height - top_margin - 39) * mm,
                         (page_width - right_margin - 40) * mm, (page_height - top_margin - 21) * mm)
        self.canvas.line((page_width - right_margin - 40) * mm, (page_height - top_margin - 19) * mm,
                         (page_width - right_margin - 40) * mm, (page_height - top_margin - 1) * mm)

        self.canvas.line((left_margin + 41) * mm, (page_height - top_margin - 20) * mm,
                         (page_width - right_margin - 41) * mm, (page_height - top_margin - 20) * mm)
        self.canvas.line((page_width - right_margin - 39) * mm, (page_height - top_margin - 20) * mm,
                         (page_width - right_margin - 1) * mm, (page_height - top_margin - 20) * mm)

        # north img
        if north_arrow:
            arrow_path = os.path.join(APP_STATIC, 'img/arrow.jpg')
            w, h = self.get_image_size(arrow_path, 6.7)
            self.canvas.drawImage(arrow_path, (page_width - right_margin - 10) * mm, (page_height - top_margin - 19) * mm,
                                  w * mm,
                                  h * mm)

        # Logo
        if path_logo is not None:
            logo = os.path.join(APP_STATIC, 'img/%s' % path_logo)
            w, h = self.get_image_size(logo, 35)
            self.canvas.drawImage(logo, (left_margin + 3) * mm, (page_height - top_margin - 38) * mm,
                                  w * mm, h * mm)

        # # map rect
        self.canvas.rect(left_margin * mm, bottom_margin * mm, page_width_nomargin * mm,
                         (page_height_nomargin - 45) * mm, stroke=1, fill=0)

        #  --------------------------------------------- stop here.
        if True:
            self.canvas.showPage()
            self.canvas.save()
            return


    def GridCoordsBySize(self, min, max, gridSize, percentage):
        # by João L
        min = floor(min)
        max = ceil(max)
        gridSize = round(gridSize)

        interval = abs(max - min)
        if interval < gridSize or gridSize < 0:
            return -1
        elif max <= min:
            return -1

        # check min's power
        minTest = abs(gridSize)

        i = 0
        while minTest >= 10:
            minTest = minTest / 10
            i = i + 1

        minAlt = round(min, -i - 1)

        if minAlt >= min:
            minAlt = minAlt - 10 ** (i + 1)

        startingPoint = minAlt

        while startingPoint <= min:
            startingPoint = startingPoint + gridSize
            if startingPoint >= minAlt + 10 ** (i + 1):
                startingPoint = minAlt + 10 ** (i + 1)  # can be altered // + gridsize
                break
        gridValues = []

        while startingPoint < max:
            gridValues.append(startingPoint)
            startingPoint = startingPoint + gridSize

        index = []

        for x in gridValues:
            if x <= min + interval * percentage / 100 or x >= max - interval * percentage / 100:
                index.append(x)

        for i in index:
            gridValues.remove(i)

        return gridValues

    def gridCoordsByNumOfPoints (self, min, max, numInt):
        # by João L
        interval = max-min

        interval=abs(interval)
        i= interval/numInt

        u=0
        while i>10:
            i=i/10
            u=u+1

        numInt = floor(i)*(10**u)
        return(self.GridCoordsBySize(min, max, numInt, 0),numInt)
