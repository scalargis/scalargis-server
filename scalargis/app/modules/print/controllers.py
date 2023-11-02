import json
import uuid
import logging
import datetime
import os.path

from flask import Blueprint, current_app, make_response, render_template, request, jsonify, url_for
from flask_security import current_user
from sqlalchemy import text
from geoalchemy2 import shape
from shapely.wkt import loads

from app.database import db
from app.database.schema import get_db_schema
from app.utils import pdf_layout, auditoria
from app.models.portal import Print, PrintLayout, PrintGroup, PrintOutput, CoordinateSystems
from app.utils import constants, geo
from instance import settings


mod = Blueprint('print',  __name__, template_folder='templates', static_folder='static')


def generate_print_output_number():
    logger = logging.getLogger(__name__)

    numero = None

    try:
        sql = 'select {schema}.generate_print_output_number()'.format(schema=get_db_schema())
        record = db.session.execute(text(sql)).first()

        if record:
            numero = record[0]

            db.session.commit()
    except Exception as e:
        db.session.rollback()

        logger.error(constants.RECORDS_INSERT_ERROR)

    return numero


def save_print_output(print, group, viewer_id, output_number, output_year, scale, title,  user_reference_number,
                      user_reference_name, geom_wkt, srid, output_date, user_id):

    logger = logging.getLogger(__name__)

    log_planta = None

    try:
        se = db.session

        record = PrintOutput()

        record.output_number = output_number
        record.output_year = output_year
        if print:
            record.print_id = print.id
            record.print_name = print.name
            record.title = title or print.title
        else:
            record.title = title
        if group:
            record.print_group_id = group.id
            record.print_group_name = group.title
        record.viewer_id = viewer_id
        record.scale = scale
        record.user_reference_number = user_reference_number
        record.user_reference_name = user_reference_name
        record.output_date = output_date

        geom = None
        if geom_wkt and len(geom_wkt) > 0:
            if isinstance(geom_wkt, list):
                ss = geo.transformGeom(geo.getGeometryFromWKT(geom_wkt), 'epsg:{0}'.format(srid),
                                       'epsg:{0}'.format(PrintOutput.geometry_srid))
            else:
                ss = geo.transformGeom(loads(geom_wkt), 'epsg:{0}'.format(srid),
                                       'epsg:{0}'.format(PrintOutput.geometry_srid))
            geom = shape.from_shape(ss, srid=PrintOutput.geometry_srid)
        record.geom = geom

        record.idUserIns = user_id
        record.dataIns = datetime.datetime.now()

        se.add(record)

        se.commit()

        log_planta = record
    except Exception as e:
        se.rollback()

        logger.error(constants.RECORDS_INSERT_ERROR + ': ' + str(e))

    return log_planta


@mod.route('/print')
def pdf_exemples():
    return render_template("/temp/pdfs.html")


@mod.route('/print/planta/<code>/generate', methods=['POST'])
def generate_pdf(code):
    print = db.session.query(Print).filter(Print.code == code).first()

    if not print:
        return jsonify(Success=False, Message="A planta solicitada não está configurada.", Data=None)

    if print.scale is not None and print.scale > 0:
        scale = print.scale
    elif 'userScale' in request.values:
        scale = int(request.values['userScale'])
    else:
        scale = int(request.values['escala'])

    viewer_id = None
    if 'mapId' in request.values and request.values['mapId'] != '':
        viewer_id = int(request.values['mapId'])

    layout = None
    if 'layoutId' in request.values and request.values['layoutId'] != '':
        layout = db.session.query(PrintLayout).filter(PrintLayout.id == int(request.values['layoutId'])).first()
    elif 'layout' in request.values and request.values['layout'] != '':
        layout_data = request.values['layout']

        for l in print.layouts:
            if layout_data.lower() == '{0}|{1}'.format(l.format, l.orientation).lower():
                layout = l
                break

    group_id = request.values['grupoId'] if 'grupoId' in request.values else None

    group = None
    if 'tipoId' in request.values and request.values['tipoId'] != '':
        group = db.session.query(PrintGroup).filter(PrintGroup.id == int(request.values['tipoId'])).first()

    title = None
    if print.title is not None and len(print.title) > 0:
        title = print.title
    title = request.values['titulo'] if 'titulo' in request.values else title # replace db titulo

    user_reference_number = request.values['nif'] if 'nif' in request.values else None
    user_reference_name = request.values['nome'] if 'nome' in request.values else None
    address = request.values['morada'] if 'morada' in request.values else None
    postal_code = request.values['codpostal'] if 'codpostal' in request.values else None
    local = request.values['local'] if 'local' in request.values else None

    print_purpose = request.values['finalidade_emissao'] if 'finalidade_emissao' in request.values else None
    payment_reference = request.values['guia_pagamento'] if 'guia_pagamento' in request.values else None
    process_number = request.values['num_processo'] if 'num_processo' in request.values else None

    extentWKT = request.values['extentWKT'] if 'extentWKT' in request.values else None
    geomWKT = request.values['geomWKT'] if 'geomWKT' in request.values else None
    if geomWKT is None:
        geomWKT = request.form.getlist('geomWKT[]')

    coordinate_system = None
    srid = request.values['srid'] if 'srid' in request.values else None
    coord_sys = db.session.query(CoordinateSystems).filter(CoordinateSystems.srid == srid).first()
    if coord_sys is not None:
        coordinate_system = coord_sys.descricao

    output_number = generate_print_output_number()
    output_year = datetime.datetime.now().year

    drawing_features = json.loads(request.values['features']) if 'features' in request.values else None

    username = None

    user_id = None
    if current_user and current_user.is_authenticated:
        user_id = current_user.id
        if group:
            if group.show_author:
                username = current_user.username
        elif print and print.show_author:
                username = current_user.username

    print_output = save_print_output(print, group, viewer_id, output_number, output_year, scale, title,
                                     user_reference_number, user_reference_name,
                                     geomWKT, srid, datetime.datetime.now(), user_id)

    page_size = print.format
    page_orientation = print.orientation

    if layout is not None:
        page_size = layout.format
        page_orientation = layout.orientation

    if page_orientation == 'Paisagem':
        page_orientation = 'landscape'
    if page_orientation == 'Retrato':
        page_orientation = 'portrait'

    json_config = print.config_json

    if layout:
        pagesize = layout.format
        json_config = layout.config

    client_layers = request.form.getlist('layers[]')

    p = pdf_layout.Pdf(page_size=page_size,orientation=page_orientation)

    if drawing_features:
        p.drawing_features = drawing_features

    # widgets for layouts
    widget_layout_list = json.loads(request.values['widget_layout_list']) if 'widget_layout_list' in request.values else None
    if widget_layout_list:
        for widget_layout in widget_layout_list:
            if widget_layout['value']:
                p.add_widget_input(widget_layout)

    if print.free_printing:
        for l in client_layers:
            max_scale = 0
            min_scale = 0
            wms_style = None
            opacity = 1
            if len(l.split(';')) > 4:
                min_scale = float(l.split(';')[4])
                max_scale = float(l.split(';')[5])

            if len(l.split(';')) > 7:
                wms_style = l.split(';')[7]

            if len(l.split(';')) > 3:
                opacity = float(l.split(';')[3])

            if (min_scale == 0 or scale <= min_scale) and (max_scale == 0 or scale >= max_scale):
                p.add_map(l.split(';')[0], l.split(';')[1], l.split(';')[2], page_id=100, cql_filter=l.split(';')[6], style=wms_style, opacity=opacity)

    p.set_wkt_and_center(geomWKT, extentWKT)
    p.populate_string("planta_id", print_output.numero_emissao)

    p.populate_string("nif_val", user_reference_number)
    p.populate_string("requerente_val", user_reference_name)
    p.populate_string("morada_val", address)
    p.populate_string("codpostal_val", postal_code)
    p.populate_string("local_val", local)

    p.populate_string("finalidade_val", print_purpose)
    p.populate_string("guia_val", payment_reference)
    p.populate_string("num_processo_val", process_number)
    p.populate_string("username_val", username)
    p.populate_string("titulo_val", title)
    p.populate_paragraph("titulo_val", title)
    p.populate_paragraph("coords_system_val", coordinate_system)
    p.generate(json_config, scale=scale, srid=srid)
    pdf_file = p.getpdf()
    filename = str(uuid.uuid4()) + ".pdf"

    # Write binary data to a file
    with open(os.path.join(settings.APP_TMP_DIR, filename), 'wb') as f:
        f.write(pdf_file)

    data = {"filename": filename, "url": url_for('file.get', filename=filename), "planta_id": print.id}

    auditoria.log(viewer_id, print_output.id, auditoria.EnumAuditOperation.EmissaoPlanta, None, None, None)

    return jsonify(Success=True, Message=None, Data=data)


def viewer_generate_pdf(code, user):
    logger = logging.getLogger(__name__)

    print = db.session.query(Print).filter(Print.code == code).first()

    if not print:
        return jsonify(Success=False, Message="A planta solicitada não está configurada.", Data=None)

    if print.scale is not None and print.scale > 0:
        scale = print.scale
    elif 'userScale' in request.values:
        scale = int(request.values['userScale'])
    else:
        scale = int(request.values['scale'])

    viewer_id = None
    if 'viewerId' in request.values and request.values['viewerId'] != '':
        viewer_id = int(request.values['viewerId'])

    layout = None
    if 'layoutId' in request.values and request.values['layoutId'] != '':
        layout = db.session.query(PrintLayout).filter(PrintLayout.id == int(request.values['layoutId'])).first()
    elif 'layout' in request.values and request.values['layout'] != '':
        layout_data = request.values['layout']

        if layout_data:
            layout_data = layout_data.replace("Retrato", "Portrait")
            layout_data = layout_data.replace("Paisagem", "Landscape")

        for l in print.layouts:
            if l.orientation == 'Retrato':
                orientation = 'Portrait'
            elif l.orientation == 'Paisagem':
                orientation = 'Landscape'
            else:
                orientation = l.orientation

            if layout_data.lower() == '{0}|{1}'.format(l.format, orientation).lower():
                layout = l
                break

    group_id = request.values['groupId'] if 'groupId' in request.values else None
    group = None
    if 'groupId' in request.values and request.values['groupId'] != '':
        group = db.session.query(PrintGroup).filter(PrintGroup.id == int(request.values['groupId'])).first()

    title = None
    if print.title is not None and len(print.title) > 0:
        title = print.title
    title = request.values['title'] if 'title' in request.values else title # replace db title

    user_reference_number = request.values['identificationNIF'] if 'identificationNIF' in request.values else None
    user_reference_name = request.values['identificationName'] if 'identificationName' in request.values else None
    address = request.values['identificationAddress'] if 'identificationAddress' in request.values else None
    postal_code = request.values['identificationPostalCode'] if 'identificationPostalCode' in request.values else None
    local = request.values['identificationPlace'] if 'identificationPlace' in request.values else None

    print_purpose = request.values['printPurpose'] if 'printPurpose' in request.values else None
    payment_reference = request.values['paymentReference'] if 'paymentReference' in request.values else None
    process_number = request.values['processNumber'] if 'processNumber' in request.values else None

    form_fields = None
    if 'formFields' in request.values:
        try:
            form_fields = json.loads(request.values['formFields'])
        except Exception as e:
            logger.debug('Form fields: ' + str(e))

    extentWKT = request.values['extentWKT'] if 'extentWKT' in request.values else None
    geomWKT = request.values['geomWKT'] if 'geomWKT' in request.values else None
    if geomWKT is None:
        geomWKT = request.form.getlist('geomWKT[]')

    coordinate_system = None
    srid = request.values['srid'] if 'srid' in request.values else None
    coord_sys = db.session.query(CoordinateSystems).filter(CoordinateSystems.srid==srid).first()
    if coord_sys is not None:
        coordinate_system = coord_sys.description

    output_number = generate_print_output_number()
    output_year = datetime.datetime.now().year

    drawing_features = json.loads(request.values['features']) if 'features' in request.values else None

    username = None

    user_id = None
    if current_user and current_user.is_authenticated:
        user_id = current_user.id
        if group:
            if group.show_author:
                username = current_user.username
        elif print and print.show_author:
                username = current_user.username
    elif user:
        user_id = user.id
        if group:
            if group.show_author:
                username = user.username
        elif print and print.show_author:
                username = user.username

    print_output = save_print_output(print, group, viewer_id, output_number, output_year, scale, title,
                                     user_reference_number, user_reference_name, geomWKT, srid,
                                     datetime.datetime.now(), user_id)

    page_size = print.format
    page_orientation = print.orientation.lower() if print.orientation else None

    if layout is not None:
        page_size = layout.format
        page_orientation = layout.orientation.lower() if layout.orientation else None

    if page_orientation == 'paisagem':
        page_orientation = 'landscape'
    if page_orientation == 'retrato':
        page_orientation = 'portrait'

    json_config = print.config_json

    if layout:
        pagesize = layout.format
        json_config = layout.config

    client_layers = request.form.getlist('layers[]')

    p = pdf_layout.Pdf(page_size=page_size, orientation=page_orientation)

    if drawing_features:
        p.drawing_features = drawing_features

    # widgets for layouts
    widget_layout_list = json.loads(request.values['widget_layout_list']) if 'widget_layout_list' in request.values else None
    if widget_layout_list:
        for widget_layout in widget_layout_list:
            if widget_layout['value']:
                p.add_widget_input(widget_layout)

    if print.free_printing:
        for l in client_layers:
            max_scale = 0
            min_scale = 0
            wms_style = None
            wms_format = None
            opacity = 1
            if len(l.split(';')) > 4:
                min_scale = float(l.split(';')[4])
                max_scale = float(l.split(';')[5])

            if len(l.split(';')) > 7:
                wms_style = l.split(';')[7]

            if len(l.split(';')) > 8:
                wms_format = l.split(';')[8]

            if len(l.split(';')) > 3:
                opacity = float(l.split(';')[3])

            if (min_scale == 0 or scale <= min_scale) and (max_scale == 0 or scale >= max_scale):
                p.add_map(l.split(';')[0], l.split(';')[1], l.split(';')[2], page_id=100, cql_filter=l.split(';')[6],
                          style=wms_style, img_format=wms_format, opacity=opacity)

    p.set_wkt_and_center(geomWKT, extentWKT)
    p.populate_string("planta_id", print_output.print_output_number)

    p.populate_string("nif_val", user_reference_number)
    p.populate_string("requerente_val", user_reference_name)
    p.populate_string("morada_val", address)
    p.populate_string("codpostal_val", postal_code)
    p.populate_string("local_val", local)

    p.populate_string("finalidade_val", print_purpose)
    p.populate_string("guia_val", payment_reference)
    p.populate_string("num_processo_val", process_number)
    p.populate_string("username_val", username)
    p.populate_string("titulo_val", title)
    p.populate_paragraph("titulo_val", title)
    p.populate_paragraph("coords_system_val", coordinate_system)

    if form_fields:
        for key in form_fields:
            p.populate_string(key, form_fields[key])

    if form_fields:
        for key in form_fields:
            p.populate_paragraph(key, form_fields[key])

    p.generate(json_config, scale=scale, srid=srid)
    pdf_file = p.getpdf()
    filename = str(uuid.uuid4()) + ".pdf"

    # Write binary data to a file
    with open(os.path.join(settings.APP_TMP_DIR, filename), 'wb') as f:
        f.write(pdf_file)

    data = {"filename": filename, "url": url_for('file.get', filename=filename), "planta_id": print.id}

    auditoria.log_viewer_async(current_app._get_current_object(), viewer_id, print.id,
                               auditoria.EnumAuditOperation.EmissaoPlanta, None, None, user.id if user else None)

    return { "Success": True, "Message": None, "Data": data}


@mod.route('/print/planta/<code>')
def pdf_db(code):

    record = db.session.query(Print).filter(Print.code == code).first()

    pagesize = record.format
    json_config = record.config_json

    p = pdf_layout.Pdf(page_size=pagesize)
    p.generate(json_config)
    pdf_file = p.getpdf()

    try:
        response = make_response(pdf_file)
        response.headers['Content-Disposition'] = "attachment; filename='planta.pdf"
        response.mimetype = 'application/pdf'
        return response
    except NameError:
        return "Bad url...."

@mod.route('/print/planta/merge', methods=['POST'])
def merge_pdf():

    # Write binary data to a file
    #with open(os.path.join(settings.APP_TMP_DIR, filename), 'wb') as f:
    #    f.write(pdf_file)

    data = request.get_json()

    map_id = None
    if 'mapId' in data and data.get('mapId') != '':
        map_id = data.get('mapId')

    files = []
    if 'files' in data:
        for f in data.get('files'):
            files.append(os.path.join(settings.APP_TMP_DIR, f))

    filename = str(uuid.uuid4()) + ".pdf"

    if pdf_layout.merge_pdf_files(os.path.join(settings.APP_TMP_DIR, filename), files):
        data = {"filename": filename, "url": url_for('file.get', filename=filename)}

        auditoria.log(map_id, 0, auditoria.EnumAuditOperation.EmissaoPlantaMerge, None, None, None)

        return jsonify(Success=True, Message=None, Data=data)
    else:
        return jsonify(Success=False, Message=None, Data=None)


def viewer_merge_pdf(user):
    data = request.get_json()

    viewer_id = None
    if 'viewerId' in data and data.get('viewerId') != '':
        viewer_id = data.get('viewerId')

    files = []
    if 'files' in data:
        for f in data.get('files'):
            files.append(os.path.join(settings.APP_TMP_DIR, f))

    filename = str(uuid.uuid4()) + ".pdf"

    if pdf_layout.merge_pdf_files(os.path.join(settings.APP_TMP_DIR, filename), files):
        data = {"filename": filename, "url": url_for('file.get', filename=filename)}

        auditoria.log_viewer_async(current_app._get_current_object(), viewer_id, None,
                                   auditoria.EnumAuditOperation.EmissaoPlantaMerge, None, None, user.id if user else None)

        return {"Success": True, "Message": None, "Data": data}
    else:
        return {"Success": False, "Message": None, "Data": None}
