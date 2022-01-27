import uuid
import logging
import datetime
import os.path
from app.database import db
from flask import Blueprint, current_app, make_response, render_template, request, jsonify, url_for
from flask_security import current_user
from sqlalchemy import String as sql_string, Date as sql_date
from sqlalchemy.sql.functions import concat
from sqlalchemy.sql.expression import func, cast
from geoalchemy2 import shape
import geoalchemy2.functions as geo_funcs
from geoalchemy2.elements import WKTElement
from shapely.wkt import loads
from app.utils import pdf_layout, auditoria, records
from app.models.mapas import Planta, PlantaLayout, TipoPlanta, EmissaoPlanta, SistemaCoordenadas
from app.utils import constants, geo
from instance import settings
import json

mod = Blueprint('print',  __name__, template_folder='templates', static_folder='static')


def generate_emissao_number():
    logger = logging.getLogger(__name__)

    numero = None

    try:
        record = db.session.execute('select portal.generate_emissao_planta_number()').first()

        if record:
            numero = record[0]

            db.session.commit()
    except:
        db.session.rollback()

        logger.error(constants.RECORDS_INSERT_ERROR)

    return numero

def save_emissao_planta(planta, tipo, mapa_id, numero, ano, escala, titulo, nif_requerente, nome_requerente,
                       geom_wkt, srid, data_emissao, grupo_emissao, user_id):
    logger = logging.getLogger(__name__)

    log_planta = None

    se = None

    try:
        se = db.session

        record = EmissaoPlanta()

        record.numero = numero
        record.ano = ano
        if planta:
            record.planta_id = planta.id
            record.planta_nome = planta.nome
            record.titulo = titulo or planta.titulo
        else:
            record.titulo = titulo
        if tipo:
            record.tipo_id = tipo.id
            record.tipo_nome = tipo.titulo
        record.mapa_id = mapa_id
        record.escala = escala
        record.nif_requerente = nif_requerente
        record.nome_requerente = nome_requerente
        record.data_emissao = data_emissao

        geom = None
        if geom_wkt and len(geom_wkt) > 0:
            if isinstance(geom_wkt, list):
                ss = geo.transformGeom(geo.getGeometryFromWKT(geom_wkt), 'epsg:{0}'.format(srid),
                                       'epsg:{0}'.format(EmissaoPlanta.geometry_srid))
            else:
                ss = geo.transformGeom(loads(geom_wkt), 'epsg:{0}'.format(srid),
                                       'epsg:{0}'.format(EmissaoPlanta.geometry_srid))
            geom = shape.from_shape(ss, srid=EmissaoPlanta.geometry_srid)
        record.geom = geom

        record.grupo_emissao = grupo_emissao
        record.idUserIns = user_id
        record.dataIns = datetime.datetime.now()

        se.add(record)

        se.commit()

        log_planta = record
    except Exception as e:
        if se is not None:
            se.rollback()

        logger.error(constants.RECORDS_INSERT_ERROR + ': ' + str(e))

    return log_planta

@mod.route('/print')
def pdf_exemples():
    return render_template("/temp/pdfs.html")


@mod.route('/print/debug')
def print_layout_debug():
    # for test and debug
    msg = "<h2>Testing pdf_layout</h2><br>"

    # create class only and kil object
    # p = pdf_layout.Pdf(page_size='A4')
    # msg += "pdf_layout.Pdf(page_size='A4') ------------------> ok" + "<br>"
    # msg += "kill" + "<br>"
    # del p


    # generate json config
    # record = db.session.query(Planta).filter(Planta.codigo=='pdm_ord').first()
    # json_config = record.configuracao
    # p = pdf_layout.Pdf(orientation='portrait')
    # msg += "pdf_layout.Pdf(orientation='portrait') -----------> ok" + "<br>"
    #
    # p.generate(json_config,scale=1111,srid=3333)
    # msg += "p.generate(json_config,scale=1111,srid=3333) -----> ok" + "<br>"
    # pdf_file = p.getpdf()
    # msg += "kill" + "<br>"
    # del p


    # generate json config
    record = db.session.query(Planta).filter(Planta.codigo=='planta_livre').first()
    json_config = record.configuracao
    p = pdf_layout.Pdf(orientation='portrait')
    #msg += "pdf_layout.Pdf(orientation='portrait') -----------> ok" + "<br>"
    #p.add_map('wms', '195.95.237.221/geoserver/', 'cm_faro:equipamentos')

    # esri_rest service
    #p.add_map("esri_rest",
    #   "http://mapas.caminhosdeevora.pt/arcgis/rest/services/SMIGA_AC/SMIGA_Cadastro/MapServer/export"
    #   , None, None, "PNG", quality=100 )

    #msg += "p.add_map(.....)) -----------> ok" + "<br>"

    #geomWKT = 'POLYGON((9976.632312448948 -147250.53776396994,9911.076716908365 -147332.81783632174,9967.41885176867 -147385.05758694923,10036.726124281357 -147302.77186611464,9976.632312448948 -147250.53776396994))'
    #geomWKT = 'MULTIPOLYGON(((9976.632312448948 -147250.53776396994,9911.076716908365 -147332.81783632174,9967.41885176867 -147385.05758694923,10036.726124281357 -147302.77186611464,9976.632312448948 -147250.53776396994)),((9811.359386068714 -147340.3314193695, 9815.506814292279 -147303.3832696704, 9832.865509775704 -147270.5040571164, 9898.421105316287 -147188.2239847646, 9929.159877190452 -147162.5243110742, 9967.519614261317 -147150.9538358905, 10007.34225407475 -147155.3700200367, 10042.23488776886 -147175.063913456, 10102.32869960127 -147227.2980156007, 10126.0434621653 -147257.8006180407, 10136.42494397085 -147295.0165226327, 10131.92339874376 -147333.3901439063, 10113.21081657894 -147367.1930725931, 10043.90354406625 -147449.4787934277, 10012.36783087905 -147474.386133769, 9973.573411296038 -147484.8680142453, 9933.785106167925 -147479.2317402869, 9899.428236617199 -147458.3875007043, 9843.086101756893 -147406.1477500768, 9820.996551865872 -147376.2409161977, 9811.359386068714 -147340.3314193695)))'

    #geomWKT = 'LINESTRING(9976.632312448948 -147250.53776396994,9911.076716908365 -147332.81783632174,9967.41885176867 -147385.05758694923,10036.726124281357 -147302.77186611464)'
    #geomWKT = 'MULTILINESTRING((9976.632312448948 -147250.53776396994,9911.076716908365 -147332.81783632174,9967.41885176867 -147385.05758694923,10036.726124281357 -147302.77186611464),(9811.359386068714 -147340.3314193695, 9815.506814292279 -147303.3832696704, 9832.865509775704 -147270.5040571164, 9898.421105316287 -147188.2239847646, 9929.159877190452 -147162.5243110742))'

    #geomWKT= 'POINT(10000 -147250)'
    geomWKT = 'MULTIPOINT((10000 -147250),(10100 -147250),(10000 -147850))'

    p.set_wkt(geomWKT)
    p.generate(json_config,scale=5000)
    pdf_file = p.getpdf()
    msg += "kill" + "<br>"
    del p



    show_debug_and_not_pdf = False

    if show_debug_and_not_pdf:
        return msg
    else:
        try:
            response = make_response(pdf_file)
            response.headers['Content-Disposition'] = "attachment; filename='planta.pdf"
            response.mimetype = 'application/pdf'
            return response
        except NameError:
            return "Bad url...."



@mod.route('/print/planta/<codigo>/generate', methods=['POST'])
def generate_pdf(codigo):
    planta = db.session.query(Planta).filter(Planta.codigo==codigo).first()

    if not planta:
        return jsonify(Success=False, Message="A planta solicitada não está configurada.", Data=None)

    if planta.escala is not None and planta.escala > 0:
        scale = planta.escala
    elif 'userScale' in request.values:
        scale = int(request.values['userScale'])
    else:
        scale = int(request.values['escala'])

    map_id = None
    if 'mapId' in request.values and request.values['mapId'] != '':
        map_id = int(request.values['mapId'])

    layout = None
    if 'layoutId' in request.values and request.values['layoutId'] != '':
        layout = db.session.query(PlantaLayout).filter(PlantaLayout.id == int(request.values['layoutId'])).first()
    elif 'layout' in request.values and request.values['layout'] != '':
        layout_data = request.values['layout']

        for l in planta.layouts:
            if layout_data.lower() == '{0}|{1}'.format(l.formato,l.orientacao).lower():
                layout = l
                break

    grupoId = request.values['grupoId'] if 'grupoId' in request.values else None

    tipo = None
    if 'tipoId' in request.values and request.values['tipoId'] != '':
        tipo = db.session.query(TipoPlanta).filter(TipoPlanta.id == int(request.values['tipoId'])).first()

    titulo = None
    if planta.titulo is not None and len(planta.titulo) > 0:
        titulo = planta.titulo
    titulo = request.values['titulo'] if 'titulo' in request.values else titulo # replace db titulo

    nif = request.values['nif'] if 'nif' in request.values else None
    nome = request.values['nome'] if 'nome' in request.values else None
    morada = request.values['morada'] if 'morada' in request.values else None
    codpostal = request.values['codpostal'] if 'codpostal' in request.values else None
    local = request.values['local'] if 'local' in request.values else None

    finalidade_emissao = request.values['finalidade_emissao'] if 'finalidade_emissao' in request.values else None
    guia_pagamento = request.values['guia_pagamento'] if 'guia_pagamento' in request.values else None
    num_processo = request.values['num_processo'] if 'num_processo' in request.values else None

    extentWKT = request.values['extentWKT'] if 'extentWKT' in request.values else None
    geomWKT = request.values['geomWKT'] if 'geomWKT' in request.values else None
    if geomWKT is None:
        geomWKT = request.form.getlist('geomWKT[]')

    sistema_coordenadas = None
    srid = request.values['srid'] if 'srid' in request.values else None
    coord_sys = db.session.query(SistemaCoordenadas).filter(SistemaCoordenadas.srid==srid).first()
    if coord_sys is not None:
        sistema_coordenadas = coord_sys.descricao

    numero = generate_emissao_number()
    ano = datetime.datetime.now().year

    drawing_features = json.loads(request.values['features']) if 'features' in request.values else None

    username = None

    user_id = None
    if current_user and current_user.is_authenticated:
        user_id = current_user.id
        if tipo:
            if tipo.autorEmissao:
                username = current_user.username
        elif planta and planta.autorEmissao:
                username = current_user.username

    emissao_planta = save_emissao_planta(planta, tipo, map_id, numero, ano, scale, titulo, nif, nome,
                                     geomWKT, srid, datetime.datetime.now(), grupoId, user_id)

    pagesize = planta.formato
    pageorientation = planta.orientacao

    if layout is not None:
        pagesize = layout.formato
        pageorientation = layout.orientacao

    if pageorientation == 'Paisagem':
        pageorientation = 'landscape'
    if pageorientation == 'Retrato':
        pageorientation = 'portrait'

    json_config = planta.configuracao

    if layout:
        pagesize = layout.formato
        json_config = layout.configuracao

    client_layers = request.form.getlist('layers[]')

    p = pdf_layout.Pdf(page_size=pagesize,orientation=pageorientation)

    if drawing_features:
        p.drawing_features = drawing_features

    # widgets for layouts
    widget_layout_list = json.loads(request.values['widget_layout_list']) if 'widget_layout_list' in request.values else None
    if widget_layout_list:
        for widget_layout in widget_layout_list:
            if widget_layout['value']:
                p.add_widget_input(widget_layout)

    if planta.emissaoLivre:
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
    p.populate_string("planta_id", emissao_planta.numero_emissao)

    p.populate_string("nif_val", nif)
    p.populate_string("requerente_val", nome)
    p.populate_string("morada_val", morada)
    p.populate_string("codpostal_val", codpostal)
    p.populate_string("local_val", local)

    p.populate_string("finalidade_val", finalidade_emissao)
    p.populate_string("guia_val", guia_pagamento)
    p.populate_string("num_processo_val", num_processo)
    p.populate_string("username_val", username)
    p.populate_paragraph("titulo_val", titulo)
    p.populate_paragraph("coords_system_val", sistema_coordenadas)
    p.generate(json_config, scale=scale, srid=srid)
    pdf_file = p.getpdf()
    filename = str(uuid.uuid4()) + ".pdf"

    # Write binary data to a file
    with open(os.path.join(settings.APP_TMP_DIR, filename), 'wb') as f:
        f.write(pdf_file)

    data = {"filename": filename, "url": url_for('file.get', filename=filename), "planta_id": planta.id}

    auditoria.log(map_id, emissao_planta.id, auditoria.EnumOperacaoAuditoria.EmissaoPlanta, None, None, None)

    return jsonify(Success=True, Message=None, Data=data)


def viewer_generate_pdf(codigo, user):
    logger = logging.getLogger(__name__)

    planta = db.session.query(Planta).filter(Planta.codigo==codigo).first()

    orientacao = 'Portrait'

    if not planta:
        return jsonify(Success=False, Message="A planta solicitada não está configurada.", Data=None)

    if planta.escala is not None and planta.escala > 0:
        scale = planta.escala
    elif 'userScale' in request.values:
        scale = int(request.values['userScale'])
    else:
        scale = int(request.values['scale'])

    viewer_id = None
    if 'viewerId' in request.values and request.values['viewerId'] != '':
        viewer_id = int(request.values['viewerId'])

    layout = None
    if 'layoutId' in request.values and request.values['layoutId'] != '':
        layout = db.session.query(PlantaLayout).filter(PlantaLayout.id == int(request.values['layoutId'])).first()
    elif 'layout' in request.values and request.values['layout'] != '':
        layout_data = request.values['layout']

        if layout_data:
            layout_data = layout_data.replace("Retrato", "Portrait")
            layout_data = layout_data.replace("Paisagem", "Landscape")

        for l in planta.layouts:
            if l.orientacao == 'Retrato':
                orientacao = 'Portrait'
            elif l.orientacao == 'Paisagem':
                orientacao = 'Landscape'

            if layout_data.lower() == '{0}|{1}'.format(l.formato, orientacao).lower():
                layout = l
                break

    groupId = request.values['groupId'] if 'groupId' in request.values else None
    tipo = None
    if 'groupId' in request.values and request.values['groupId'] != '':
        tipo = db.session.query(TipoPlanta).filter(TipoPlanta.id == int(request.values['groupId'])).first()

    titulo = None
    if planta.titulo is not None and len(planta.titulo) > 0:
        titulo = planta.titulo
    titulo = request.values['title'] if 'title' in request.values else titulo # replace db title

    nif = request.values['identificationNIF'] if 'identificationNIF' in request.values else None
    nome = request.values['identificationName'] if 'identificationName' in request.values else None
    morada = request.values['identificationAddress'] if 'identificationAddress' in request.values else None
    codpostal = request.values['identificationPostalCode'] if 'identificationPostalCode' in request.values else None
    local = request.values['identificationPlace'] if 'identificationPlace' in request.values else None

    finalidade_emissao = request.values['printPurpose'] if 'printPurpose' in request.values else None
    guia_pagamento = request.values['paymentReference'] if 'paymentReference' in request.values else None
    num_processo = request.values['processNumber'] if 'processNumber' in request.values else None

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

    sistema_coordenadas = None
    srid = request.values['srid'] if 'srid' in request.values else None
    coord_sys = db.session.query(SistemaCoordenadas).filter(SistemaCoordenadas.srid==srid).first()
    if coord_sys is not None:
        sistema_coordenadas = coord_sys.descricao

    numero = generate_emissao_number()
    ano = datetime.datetime.now().year

    drawing_features = json.loads(request.values['features']) if 'features' in request.values else None

    username = None

    user_id = None
    if current_user and current_user.is_authenticated:
        user_id = current_user.id
        if tipo:
            if tipo.autorEmissao:
                username = current_user.username
        elif planta and planta.autorEmissao:
                username = current_user.username
    elif user:
        user_id = user.id
        if tipo:
            if tipo.autorEmissao:
                username = user.username
        elif planta and planta.autorEmissao:
                username = user.username

    emissao_planta = save_emissao_planta(planta, tipo, viewer_id, numero, ano, scale, titulo, nif, nome,
                                     geomWKT, srid, datetime.datetime.now(), groupId, user_id)

    pagesize = planta.formato
    pageorientation = planta.orientacao.lower() if planta.orientacao else None

    if layout is not None:
        pagesize = layout.formato
        pageorientation = layout.orientacao.lower()  if layout.orientacao else None

    if pageorientation == 'paisagem':
        pageorientation = 'landscape'
    if pageorientation == 'retrato':
        pageorientation = 'portrait'

    json_config = planta.configuracao

    if layout:
        pagesize = layout.formato
        json_config = layout.configuracao

    client_layers = request.form.getlist('layers[]')

    p = pdf_layout.Pdf(page_size=pagesize,orientation=pageorientation)

    if drawing_features:
        p.drawing_features = drawing_features

    # widgets for layouts
    widget_layout_list = json.loads(request.values['widget_layout_list']) if 'widget_layout_list' in request.values else None
    if widget_layout_list:
        for widget_layout in widget_layout_list:
            if widget_layout['value']:
                p.add_widget_input(widget_layout)

    if planta.emissaoLivre:
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
    p.populate_string("planta_id", emissao_planta.numero_emissao)

    p.populate_string("nif_val", nif)
    p.populate_string("requerente_val", nome)
    p.populate_string("morada_val", morada)
    p.populate_string("codpostal_val", codpostal)
    p.populate_string("local_val", local)

    p.populate_string("finalidade_val", finalidade_emissao)
    p.populate_string("guia_val", guia_pagamento)
    p.populate_string("num_processo_val", num_processo)
    p.populate_string("username_val", username)
    p.populate_paragraph("titulo_val", titulo)
    p.populate_paragraph("coords_system_val", sistema_coordenadas)

    if form_fields:
        for key in form_fields:
            p.populate_string(key, form_fields[key])

    p.generate(json_config, scale=scale, srid=srid)
    pdf_file = p.getpdf()
    filename = str(uuid.uuid4()) + ".pdf"

    # Write binary data to a file
    with open(os.path.join(settings.APP_TMP_DIR, filename), 'wb') as f:
        f.write(pdf_file)

    data = {"filename": filename, "url": url_for('file.get', filename=filename), "planta_id": planta.id}

    auditoria.log_viewer_async(current_app._get_current_object(), viewer_id, planta.id,
                               auditoria.EnumOperacaoAuditoria.EmissaoPlanta, None, None, user.id if user else None)

    return { "Success": True, "Message": None, "Data": data}


@mod.route('/print/planta/<codigo>')
def pdf_db(codigo):


    record = db.session.query(Planta).filter(Planta.codigo==codigo).first()

    pagesize = record.formato
    json_config = record.configuracao

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

        auditoria.log(map_id, 0, auditoria.EnumOperacaoAuditoria.EmissaoPlantaMerge, None, None, None)

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
                                   auditoria.EnumOperacaoAuditoria.EmissaoPlantaMerge, None, None, user.id if user else None)

        return {"Success": True, "Message": None, "Data": data}
    else:
        return {"Success": False, "Message": None, "Data": None}


@mod.route('/print/create_faro_template')
# def get_pdf(example):
def get_pdf():
    if True:
        # create A3 portrait template
        # p = pdf_layout.Pdf(page_size=A3)
        p = pdf_layout.Pdf()
        p.create_template()  # "A3_portrait","viana_brasao.jpg"
        pdf_file = p.getpdf()


# TO UPDATE ..........    PLEASE DON'T REMOVE.
#
#@mod.route('/print/<example>')
#def get_pdf(example):
#
#     txt = '''Well-known text (WKT) is a text markup language for representing vector geometry
#     objects on a map, spatial reference systems of spatial objects and transformations between
#     spatial reference systems.
#     <br/>
#     <br/><a href="http://www.wkt.pt" color="blue">WKT is import __future__</a>
#     '''
#
#
#     #example = "o"
#     if True:
#         # create A3 portrait template
#         #p = pdf_layout.Pdf(page_size=A3)
#         p = pdf_layout.Pdf()
#         p.create_template()  # "A3_portrait","viana_brasao.jpg"
#         pdf_file = p.getpdf()
#
#
#
#     if example == 'A3_portrait':
#         # A3 Portrait
#         p = pdf_layout.Pdf(page_size=A3)
#         p.add_map('195.95.237.222/geoserver/cm_faro/wms', 'cm_faro:equipamentos')
#         p.populate_paragraph("description",txt)
#         p.generate("pdf/a3_portrait.json", scale=50000, mapcenter=[17800,-295000])
#         #p.generate("pdf/config1.json", scale=50000, mapcenter=[17800,-295000])
#         pdf_file = p.getpdf()
#
#
#     if example == 'test_minimal_json':
#         # minimal
#         p = pdf_layout.Pdf(page_size='A4')
#         p.add_map('wms', 'www.kt.pt/geoserver/wkt/wms', 'wkt:caop_freg')
#         p.generate("pdf/minimal.json", scale=50000, mapcenter=[17800,-295000])
#         pdf_file = p.getpdf()
#
#     if example == 'ex1':
#         p = pdf_layout.Pdf(page_size='A4')
#         p.generate("pdf/config1.json")
#         pdf_file = p.getpdf()
#
#
#
#     if example == 'ex2':
#         # tipical map from json
#         p = pdf_layout.Pdf(page_size=A4)
#         p.add_image("pdf/pdm/img_pdm_vda.jpg", 30, 50, 120)
#         p.generate("pdf/config1.json", scale=50000, mapcenter=[17800,-295000])
#         pdf_file = p.getpdf()
#
#
#
#     if example == 'ex3':
#         # insert image + populate
#         p = pdf_layout.Pdf(page_size=A4)
#         # p.insert_img("pdf/pdm/img_pdm_vda.jpg", 50, 50, 100)
#
#         p.populate_string("layout_number_id", "xxx - vvv - yyyyyyyyyy - nº 123", page_id=1)
#         p.populate_paragraph("description","A preencher a descrição...")
#
#         p.generate("pdf/config1.json",srid=27493, scale=50000, mapcenter=[17800,-295000])
#         pdf_file = p.getpdf()
#
#     if False:
#
#         p = pdf_layout.Pdf(page_size=A4)
#         p.add_map('195.95.237.222/geoserver/cm_faro/wms', 'cm_faro:equipamentos')
#         # p.add_map('195.95.237.222/geoserver/cm_faro/wms','cm_faro:municipal_ln,cm_faro:equipamentos')
#         # p.add_map('195.95.237.222/geoserver/cm_faro/wms','cm_faro:equipamentos',page_id=1)
#         # p.add_map('195.95.237.221:8080/geoserver/conservacao_natureza_arq/wms',
#         #          'conservacao_natureza_arq:reserva_natural_ria_formosa')
#         # p.add_map('195.95.237.221:8080/geoserver/ren/wms','ren:ren_algarve')
#
#         p.add_string(2, 2, "WKT-Sistemas de Informação", fontsize=7, fontcolor=[0.5, 0.5, 0.5])
#         # p.add_string(70,245,"x",fontsize=7,fontcolor=[1,0.5,0.5])
#         txt = '''Well-known text (WKT) is a text markup language for representing vector geometry
#         objects on a map, spatial reference systems of spatial objects and transformations between
#         spatial reference systems.
#         <br/>
#         <br/><a href="http://www.wkt.pt" color="blue">WKT is import __future__</a>
#         '''
#         p.add_paragraph(67, 249, 91, 16, txt, page_id=1)
#
#         p.populate_string("layout_number_id", "xxx - vvv - yyyyyyyyyy - nº 123", page_id=1)
#
#         p.generate("config1.json", 50000, 27493, 17800, -295000)
#         pdf_file = p.getpdf()
#
#
#
#     if example == 'ex4':
#         # PDF From scratch with "paragraph" object type
#         # note that "inserts" are independents with json configfile and only at page level.
#         # check difference with add_paragraph()
#         p = pdf_layout.Pdf(page_size='A4')
#         txt = '''Well-known text (WKT) is a text markup language for representing vector geometry
#         objects on a map, spatial reference systems of spatial objects and transformations between
#         spatial reference systems.
#         <br/>
#         <br/><a href="http://www.wkt.pt" color="blue">WKT is import __future__</a>
#         '''
#         p.insert_paragraph(67,249,91,16,txt)
#         p.insert_img("pdf/pdm/img_pdm_vda.jpg", 30, 50, 120)
#         p.savepdf() # needed when generate() not used (no config json used)
#         p_io = p.get_io()
#
#
#         p2 = pdf_layout.Pdf(page_size='A4')
#
#         # p2.insert_map(50000,27493,17800, -295000,210,298,"image/png",0,0,
#         #               "195.95.237.222/geoserver/cm_faro/wms",'cm_faro:municipal_ln,cm_faro:equipamentos')
#         # p2.insert_map(50000,27493,17800, -295000,210,298,"image/png",0,0,
#         #               "195.95.237.221:8080/geoserver/ren/wms",'ren:ren_algarve')
#
#         p2.savepdf() # needed when generate() not used (no config json used)
#
#         p2.append_pdf(p2.get_io(),p_io)
#         p.getpdf() # close the fisrt page
#         pdf_file = p2.getpdf() # close and get the doc
#
#
#
#
    try:
        response = make_response(pdf_file)
        response.headers['Content-Disposition'] = "attachment; filename='planta.pdf"
        response.mimetype = 'application/pdf'
        return response
    except NameError:
        return "Bad url...."


@mod.route('/print/search/plantas/index', methods=['POST'])
def search_plantas_index():

    html = render_template("map/print/search/search_plantas_index.html")

    return jsonify(Success=True, Message=html, Data=None)


@mod.route('/search/plantas/', methods=['POST'])
def search_plantas():
    html = ''

    recs = None
    pagination = None

    recs, pagination = do_search_plantas()

    html = render_template('map/print/search/search_plantas_results.html', records=recs, pagination=pagination)

    return jsonify(Success=True, Message=html, Data=recs)


def do_search_plantas():
    page = 1
    max_records = settings.RECORDS_PER_PAGE

    if request.form.get('page') is not None:
        page = int(request.form.get("page"))

    start = 1 if page < 2 else (page - 1) * max_records

    order_ano = getattr(getattr(EmissaoPlanta, 'ano'), 'desc')()
    order_numero = getattr(func.right(concat('00000', getattr(EmissaoPlanta, 'numero')), 5), 'desc')()

    numero = None
    ano = None
    nif = None
    requerente = None
    data_emissao = None
    geom_extent = None

    if 'Numero' in request.form.keys():
        numero = request.form.get('Numero')

    if 'Ano' in request.form.keys():
        ano = request.form.get('Ano')

    if 'NIF' in request.form.keys():
        nif = request.form.get('NIF')

    if 'Requerente' in request.form.keys():
        requerente = request.form.get('Requerente')

    if 'DataEmissao' in request.form.keys():
        data_emissao = request.form.get('DataEmissao')

    if 'RestricaoEspacial' in request.form.keys():
        geom_extent = request.form.get('MapExtent')

    query = EmissaoPlanta.query

    if numero:
        query = query.filter(cast(EmissaoPlanta.numero, sql_string).ilike(numero))
    if ano:
        query = query.filter(EmissaoPlanta.ano == int(ano))
    if nif:
        query = query.filter(EmissaoPlanta.nif_requerente.ilike(nif))
    if requerente:
        query = query.filter(EmissaoPlanta.nome_requerente.ilike('%' + requerente + '%'))
    if data_emissao:
        query = query.filter(cast(EmissaoPlanta.data_emissao, sql_date) == data_emissao)

    if geom_extent:
        geom = WKTElement(geom_extent, srid=4326)
        query = query.filter(EmissaoPlanta.geometry.ST_Intersects(geo_funcs.ST_Transform(geom, EmissaoPlanta.table_srid)))

    total = query.count()
    list = query.order_by(order_ano, order_numero). \
        paginate(page, max_records, False).items

    pagination = records.Pagination(page, max_records, total, 1, 2, 1, 2)

    recs = []

    for rec in list:
        r = {"id": rec.id, "numero": rec.numero, "ano": rec.ano, "numero_emissao": rec.numero_emissao,
             "data_emissao": rec.data_emissao, "nif": rec.nif_requerente, "requerente": rec.nome_requerente,
             "planta": rec.planta_nome, "tipo": rec.tipo_nome, "escala": rec.escala,
             "geom_wkt": rec.geometry_wkt, "geom_srid": rec.geometry_srid}

        recs.append(r)

    return recs, pagination