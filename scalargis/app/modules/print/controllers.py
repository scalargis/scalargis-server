import json
import uuid
import logging
import os.path

from flask import current_app, request, jsonify, url_for
from flask_security import current_user
from sqlalchemy import text, func
from geoalchemy2 import shape
from shapely import force_2d
from shapely.wkt import loads

from app.database import db
from app.database.schema import PRINT_NUMBER_LOCK_KEY
from app.utils import pdf_layout, auditoria
from app.utils.print_layers import client_layer_url_params
from app.models.portal import Print, PrintLayout, PrintGroup, PrintOutput, PrintOutputNumber, CoordinateSystems
from app.utils import constants, geo, utc_now, local_now
from app.utils.files import contained_path
from instance import settings


PRINT_STARTED = 'started'
PRINT_DONE = 'done'
PRINT_FAILED = 'failed'


def take_print_number(year=None):
    """Take the next print number of the year in the open transaction, under a lock that the commit releases."""
    year = year or local_now().year
    if db.session.get_bind().dialect.name == 'postgresql':
        db.session.execute(text('SELECT pg_advisory_xact_lock(:k)'), {'k': PRINT_NUMBER_LOCK_KEY})
    last = db.session.query(func.max(PrintOutputNumber.output_number)).filter(
        PrintOutputNumber.output_year == year).scalar()
    number = (last or 0) + 1
    db.session.add(PrintOutputNumber(output_number=number, output_year=year))
    db.session.flush()
    return number, year


def generate_print_output_number():
    """Take and commit the next print number of the current year."""
    try:
        number, _ = take_print_number()
        db.session.commit()
    except Exception:
        db.session.rollback()
        logging.getLogger(__name__).exception(constants.RECORDS_INSERT_ERROR)
        raise
    return number


def save_print_output(print, group, viewer_id, scale, title, user_reference_number, user_reference_name, geom_wkt,
                      srid, output_date, user_id):
    """Take a print number and save its output row as started, in one transaction."""
    record = PrintOutput()
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
    record.status = PRINT_STARTED

    geom = None
    if geom_wkt and len(geom_wkt) > 0:
        source = geo.getGeometryFromWKT(geom_wkt) if isinstance(geom_wkt, list) else loads(geom_wkt)
        ss = geo.transformGeom(force_2d(source), 'epsg:{0}'.format(srid),
                               'epsg:{0}'.format(PrintOutput.geometry_srid))
        geom = shape.from_shape(ss, srid=PrintOutput.geometry_srid)
    record.geom = geom

    record.idUserIns = user_id
    record.dataIns = utc_now()

    try:
        record.output_number, record.output_year = take_print_number()
        db.session.add(record)
        db.session.commit()
    except Exception:
        db.session.rollback()
        logging.getLogger(__name__).exception(constants.RECORDS_INSERT_ERROR)
        raise
    return record


def set_print_output_status(output_id, status):
    """Write the status of a print output row and commit."""
    db.session.rollback()
    db.session.query(PrintOutput).filter(PrintOutput.id == output_id).update({PrintOutput.status: status})
    db.session.commit()


def output_title(title, form_fields):
    """The title of a print output row: the non-empty titulo_val of the form, else the given title."""
    user_title = (form_fields or {}).get('titulo_val') if isinstance(form_fields, dict) else None
    if isinstance(user_title, str) and user_title.strip():
        return user_title.strip()
    return title


def client_layer_attributions(request, layer_count):
    """The text of each layers[] entry from layersAttributions, or no text when the param does not pair with them."""
    logger = logging.getLogger(__name__)
    no_texts = [None] * layer_count

    if layer_count == 0:
        return no_texts

    try:
        attributions = json.loads(request.values['layersAttributions'])
    except (KeyError, TypeError, ValueError) as err:
        logger.warning('layersAttributions is missing or not valid, the print has no attribution: {0}'.format(err))
        return no_texts

    if not isinstance(attributions, list) or len(attributions) != layer_count:
        logger.warning('layersAttributions does not pair with layers[], the print has no attribution')
        return no_texts

    return [item if isinstance(item, str) else None for item in attributions]


def viewer_generate_pdf(code, user, request=request, output_id=None, on_output=None):
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

    drawings = None # scalargis drawtools elements
    if 'userDrawings' in request.values:
        try:
            drawings = json.loads(request.values['userDrawings'])
        except Exception as e:
            logger.debug('User Drawings: ' + str(e))

    extentWKT = request.values['extentWKT'] if 'extentWKT' in request.values else None
    geomWKT = request.values['geomWKT'] if 'geomWKT' in request.values else None
    if geomWKT is None:
        geomWKT = request.form.getlist('geomWKT[]')

    coordinate_system = None
    srid = request.values['srid'] if 'srid' in request.values else None
    coord_sys = db.session.query(CoordinateSystems).filter(CoordinateSystems.srid==srid).first()
    if coord_sys is not None:
        coordinate_system = coord_sys.description

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

    print_output = db.session.get(PrintOutput, output_id) if output_id else None
    if print_output is None:
        print_output = save_print_output(print, group, viewer_id, scale, output_title(title, form_fields),
                                         user_reference_number, user_reference_name, geomWKT, srid, utc_now(),
                                         user_id)
        if on_output is not None:
            on_output(print_output.id)
    output_id = print_output.id

    try:
        data = draw_print_pdf(request, print, layout, scale, srid, geomWKT, extentWKT, drawing_features, drawings,
                              print_output.print_output_number, title, form_fields, username, coordinate_system,
                              user_reference_number, user_reference_name, address, postal_code, local,
                              print_purpose, payment_reference, process_number)
    except Exception:
        set_print_output_status(output_id, PRINT_FAILED)
        raise
    set_print_output_status(output_id, PRINT_DONE)

    auditoria.log_viewer_async(current_app._get_current_object(), viewer_id, print.id,
                               auditoria.EnumAuditOperation.EmissaoPlanta, None, None, user.id if user else None)

    return { "Success": True, "Message": None, "Data": data}


def draw_print_pdf(request, print, layout, scale, srid, geomWKT, extentWKT, drawing_features, drawings,
                   print_number, title, form_fields, username, coordinate_system, user_reference_number,
                   user_reference_name, address, postal_code, local, print_purpose, payment_reference,
                   process_number):
    """Draw the PDF of a viewer print into APP_TMP_DIR. Returns the file data of the response."""

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

    if drawings:
        p.drawings = drawings

    # widgets for layouts
    widget_layout_list = json.loads(request.values['widget_layout_list']) if 'widget_layout_list' in request.values else None
    if widget_layout_list:
        for widget_layout in widget_layout_list:
            if widget_layout['value']:
                p.add_widget_input(widget_layout)

    if print.free_printing:
        attributions = client_layer_attributions(request, len(client_layers))
        for l, attribution in zip(client_layers, attributions):
            max_scale = 0
            min_scale = 0
            wms_style = None
            wms_format = None
            opacity = 1
            url_params = client_layer_url_params(l)
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
                          style=wms_style, img_format=wms_format, opacity=opacity, url_params=url_params,
                          attribution=attribution)

    p.set_wkt_and_center(geomWKT, extentWKT)
    p.populate_string("planta_id", print_number)

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

    return {"filename": filename, "url": url_for('file.get', filename=filename), "planta_id": print.id}


def viewer_merge_pdf(user, request=request, trusted_paths=False):
    data = request.get_json()

    viewer_id = None
    if 'viewerId' in data and data.get('viewerId') != '':
        viewer_id = data.get('viewerId')

    files = []
    if 'files' in data:
        for f in data.get('files'):
            if trusted_paths:
                filepath = os.path.join(settings.APP_TMP_DIR, f)
            else:
                filepath = contained_path(settings.APP_TMP_DIR, f)
            if filepath is None:
                return {"Success": False, "Message": None, "Data": None}
            files.append(filepath)

    filename = str(uuid.uuid4()) + ".pdf"

    if pdf_layout.merge_pdf_files(os.path.join(settings.APP_TMP_DIR, filename), files):
        data = {"filename": filename, "url": url_for('file.get', filename=filename)}

        auditoria.log_viewer_async(current_app._get_current_object(), viewer_id, None,
                                   auditoria.EnumAuditOperation.EmissaoPlantaMerge, None, None, user.id if user else None)

        return {"Success": True, "Message": None, "Data": data}
    else:
        return {"Success": False, "Message": None, "Data": None}
