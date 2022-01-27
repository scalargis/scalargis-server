import logging
import datetime
import lxml.etree as ET

from app.database import db
from app.models.mapas import CatalogoMetadados, MDTipoServico, MDTipoRecurso, MDTipoRecursoSNIG, \
    MDTemaInspire, MDCategoria
from flask import Blueprint, render_template, Response, request, jsonify, current_app
import app.utils
from app.utils import csw, records
from instance import settings

from app.utils.csw import Service as CSWService

mod = Blueprint('catalog', __name__, template_folder='templates', static_folder='static')


@mod.route('/catalog/show_catalog', methods=['POST'])
def show_catalog():
    html = ''

    id = int(request.values['id'])
    catalog = db.session.query(CatalogoMetadados).filter(CatalogoMetadados.id == id).first()

    if catalog.tipo.lower() == 'geonetwork':
        cat_info = get_catalogo_geonetwork_info()
        html = render_template('map/_catalog_geonetwork.html', md_tipos_servicos=cat_info.get('tipos_servicos'),
                               md_tipos_recursos=cat_info.get('tipos_recursos'),
                               md_categorias=cat_info.get('categorias'),
                               md_temas_inspire=cat_info.get('temas_inspire'))
    else:
        cat_info = get_catalogo_geoportal_info()
        html = render_template("map/_catalog_geoportal.html",
                               md_tipos_recursos_snig=cat_info.get('tipos_recursos_snig'),
                               md_categorias=cat_info.get('categorias'))

    return jsonify(Success=True, Message=html, Data=None)


@mod.route('/catalog/search_catalog', methods=['POST'])
def search_catalog():
    html = ''

    id = int(request.values['catalogo'])
    pesq_avancada = request.values['PesquisaAvancada']

    catalog = db.session.query(CatalogoMetadados).filter(CatalogoMetadados.id == id).first()

    if catalog.tipo.lower() == 'geonetwork':
        html = search_catalog_geonetwork(catalog)
    else:
        html = search_catalog_geoportal(catalog)

    if html:
        return jsonify(Success=True, Message=html, Data=None)
    else:
        return jsonify(Success=False, Message="Ocorreu um erro ao pesquisar o catálogo", Data=None)


@mod.route('/Catalog/Metadata')
@mod.route('/catalog/metadata')
@mod.route('/Catalogo/Metadata')
@mod.route('/catalogo/metadata')
def metadata():
    catalog = request.args.get('catalog')
    uuid = request.args.get('uuid')
    out_format = request.args.get('format')
    mime_type = None

    catalog = db.session.query(CatalogoMetadados).filter(CatalogoMetadados.codigo == catalog).first()

    html = ''

    url = catalog.url_csw
    csw_service = CSWService(url)

    # Authentication
    authenticate = False
    # TODO
    if authenticate:
        if catalog.portal:
            # TODO login
            csw_service.login(catalog.username, catalog.password)
        elif catalog.username and not catalog.username.isspace():
            csw_service.login(catalog.username, catalog.password)
    # End Authentication

    if out_format and out_format.lower() == 'xml':
        html = csw_service.do_show_metadata_xml(uuid)
        mime_type = 'text/xml'
    else:
        xml = csw_service.do_show_metadata_xml(uuid)
        html = get_metadata_html(xml, catalog)
        mime_type = 'text/html'

    if authenticate:
        csw_service.logout()

    r = Response(response=html, mimetype=mime_type)

    return r


def search_catalog_geonetwork(catalog):
    pesquisa_avancada = False

    codigo = None

    any_text = None
    keyword = None
    resource_type = None
    service_type = None
    category = None
    themes = None
    begin_date = None
    end_date = None
    mode = csw.EnumElementSetName.full

    spatial_filter = None
    geom_extent = None

    xml = None
    html = ''

    page = 1
    max_records = settings.RECORDS_PER_PAGE

    if request.form.get('page') is not None:
        page = int(request.form.get("page"))

    start = 1 if page < 2 else (page - 1) * max_records

    if 'TextoLivre' in request.form.keys():
        any_text = request.form.get('TextoLivre')

    if 'PalavraChave' in request.form.keys():
        keyword = request.form.get('PalavraChave')

    if 'RestricaoEspacial' in request.form.keys():
        if request.form.get('RestricaoEspacial') != '0':
            if request.form.get('RestricaoEspacial') == '1':
                spatial_filter = csw.EnumSpatialOperator.Intersects
            if request.form.get('RestricaoEspacial') == '2':
                spatial_filter = csw.EnumSpatialOperator.Within

            geom_extent = request.form.get('MapExtent').replace(',', ' ')

    if request.form.get('PesquisaAvancada') is not None:
        pesquisa_avancada = app.utils.to_bool(request.form.get('PesquisaAvancada'))

    if pesquisa_avancada:
        if request.form.get('TipoRecurso') is not None:
            resource_type = request.form.get('TipoRecurso')
        if request.form.get('TipoServico') is not None:
            service_type = request.form.get('TipoServico')
        if request.form.get('Categoria') is not None:
            category = request.form.get('Categoria')
        if request.form.get('Temas') is not None:
            md_temas_inspire = db.session.query(MDTemaInspire).all()
            for t in request.form.getlist('Temas'):
                for obj in md_temas_inspire:
                    if t == obj.code:
                        if themes:
                            themes += ";"
                        # themes = (themes or '') + obj.name.lower()
                        themes = (themes or '') + obj.name
                        break
        if request.form.get('DataRefInicio'):
            begin_date = datetime.datetime.strptime(request.form.get('DataRefInicio'), '%d/%m/%Y').date()
        if request.form.get('DataRefFim'):
            end_date = datetime.datetime.strptime(request.form.get('DataRefFim'), '%d/%m/%Y').date()

    url = catalog.url_csw
    csw_service = CSWService(url)

    # Authentication
    authenticate = False
    # TODO
    if authenticate:
        if catalog.portal:
            # TODO login
            csw_service.login(catalog.username, catalog.password)
        elif catalog.username and not catalog.username.isspace():
            csw_service.login(catalog.username, catalog.password)
    # End Authentication

    out = csw_service.search_metadata(codigo, any_text, keyword, resource_type,
                                      service_type, category, themes, begin_date, end_date, spatial_filter,
                                      geom_extent, mode, start, max_records, 'dfsd')

    xslt_file = app.utils.get_file_path(current_app.root_path, 'xslt', catalog.xslt_results_file)

    xml = ET.fromstring(out[0].encode('utf8'))
    total = out[1]
    next = out[2]

    xsl = None

    if catalog.xslt_results:
        xsl = ET.XML(catalog.xslt_results)
    elif xslt_file:
        xsl = ET.parse(xslt_file)
    else:
        logging.error('Não foi possível localizar o ficheiro xslt: {0}'.format(catalog.xslt_results_file))
        return None

    if xsl:
        ET.register_namespace('csw', 'http://www.opengis.net/cat/csw/2.0.2')

        transform_xml = ET.XSLT(xsl)

        url_base = request.script_root + '/catalogo/metadata'
        if catalog.url_base and catalog.url_base.strip():
            url_base = catalog.url_base

        arg_catalog = ET.XSLT.strparam(catalog.codigo)
        arg_url_base = ET.XSLT.strparam(url_base)
        arg_results_title = ET.XSLT.strparam('Resultados')
        arg_label_metadados = ET.XSLT.strparam('Metadados')
        arg_label_xml = ET.XSLT.strparam('XML')  # ("labelXML", "", "XML")
        arg_label_addservice = ET.XSLT.strparam('Abrir')  # ("labelAddService", "", "Abrir");

        html = transform_xml(xml, catalog=arg_catalog, urlBase=arg_url_base, resultsTitle=arg_results_title,
                             labelMetadados=arg_label_metadados, labelXML=arg_label_xml,
                             labelAddService=arg_label_addservice)

        pagination = records.Pagination(page, max_records, total, 1, 2, 1, 2)

        return render_template('map/_catalog_results.html', html_list=str(html), pagination=pagination)
    else:
        logging.error('Não foi possível obter ou processar xslt')

        return None


def search_catalog_geoportal(catalog):
    pesquisa_avancada = False

    codigo = None

    any_text = None
    resource_type = None
    category = None
    begin_date = None
    end_date = None
    mode = csw.EnumElementSetName.full

    spatial_filter = None
    geom_extent = None

    xml = None
    html = ''

    page = 1
    max_records = settings.RECORDS_PER_PAGE

    if request.form.get('page') is not None:
        page = int(request.form.get("page"))

    start = 1 if page < 2 else (page - 1) * max_records

    if 'TextoLivre' in request.form.keys():
        any_text = request.form.get('TextoLivre')

    if 'RestricaoEspacial' in request.form.keys():
        if request.form.get('RestricaoEspacial') != '0':
            if request.form.get('RestricaoEspacial') == '1':
                spatial_filter = csw.EnumSpatialOperator.Intersects
            if request.form.get('RestricaoEspacial') == '2':
                spatial_filter = csw.EnumSpatialOperator.Within

            geom_extent = request.form.get('MapExtent').replace(',', ' ')

    if request.form.get('PesquisaAvancada') is not None:
        pesquisa_avancada = app.utils.to_bool(request.form.get('PesquisaAvancada'))

    if pesquisa_avancada:
        if request.form.get('TipoRecurso') is not None:
            resource_type = request.form.get('TipoRecurso')
        if request.form.get('Categoria') is not None:
            category = request.form.get('Categoria')
        if request.form.get('DataRefInicio'):
            begin_date = datetime.datetime.strptime(request.form.get('DataRefInicio'), '%d/%m/%Y').date()
        if request.form.get('DataRefFim'):
            end_date = datetime.datetime.strptime(request.form.get('DataRefFim'), '%d/%m/%Y').date()

    url = catalog.url_csw
    csw_service = CSWService(url)

    # Authentication
    authenticate = False
    # TODO
    if authenticate:
        if catalog.portal:
            # TODO login
            csw_service.login(catalog.username, catalog.password)
        elif catalog.username and not catalog.username.isspace():
            csw_service.login(catalog.username, catalog.password)
    # End Authentication

    out = csw_service.search_geoportal_metadata(codigo, any_text, resource_type,
                                                category, begin_date, end_date, spatial_filter,
                                                geom_extent, mode, start, max_records, 'dfsd')

    xslt_file = app.utils.get_file_path(current_app.root_path, 'xslt', catalog.xslt_results_file)

    xml = ET.fromstring(out[0].encode('utf8'))
    total = out[1]
    next = out[2]

    xsl = None

    if catalog.xslt_results:
        xsl = ET.XML(catalog.xslt_results)
    elif xslt_file:
        xsl = ET.parse(xslt_file)
    else:
        logging.error('Não foi possível localizar o ficheiro xslt: {0}'.format(catalog.xslt_results_file))
        return None

    if xsl:
        ET.register_namespace('csw', 'http://www.opengis.net/cat/csw/2.0.2')

        transform_xml = ET.XSLT(xsl)

        url_base = request.script_root + '/catalogo/metadata'
        if catalog.url_base and catalog.url_base.strip():
            url_base = catalog.url_base

        arg_catalog = ET.XSLT.strparam(catalog.codigo)
        arg_url_base = ET.XSLT.strparam(url_base)
        arg_results_title = ET.XSLT.strparam('Resultados')
        arg_label_metadados = ET.XSLT.strparam('Metadados')
        arg_label_xml = ET.XSLT.strparam('XML')  # ("labelXML", "", "XML")
        arg_label_addservice = ET.XSLT.strparam('Abrir')  # ("labelAddService", "", "Abrir");

        html = transform_xml(xml, catalog=arg_catalog, urlBase=arg_url_base, resultsTitle=arg_results_title,
                             labelMetadados=arg_label_metadados, labelXML=arg_label_xml,
                             labelAddService=arg_label_addservice)

        pagination = records.Pagination(page, max_records, total, 1, 2, 1, 2)

        return render_template('map/_catalog_results.html', html_list=str(html), pagination=pagination)
    else:
        logging.error('Não foi possível obter ou processar xslt')

        return None


def get_metadata_html(xml, catalog):
    # set default xslt file
    xslt_file = app.utils.get_file_path(current_app.root_path, 'xslt', 'MetadataDetails.xsl')

    if catalog and catalog.xslt_metadata_file:
        xslt_file = app.utils.get_file_path(current_app.root_path, 'xslt', catalog.xslt_metadata_file)

    xml = ET.fromstring(xml.encode('utf8'))

    xsl = None

    if catalog and catalog.xslt_metadata:
        xsl = ET.XML(catalog.xslt_metadata)
    elif xslt_file:
        xsl = ET.parse(xslt_file)
    else:
        logging.error('Não foi possível localizar o ficheiro xslt: {0}'.format(xslt_file))
        return None

    # xsl = ET.parse(r'D:\Projectos_app\WKT-SI\WKT\WKTApp\web\wktapp\xslt\MetadataDetails.xsl')
    # # ET.register_namespace('csw', 'http://www.opengis.net/cat/csw/2.0.2')

    transform_xml = ET.XSLT(xsl)

    args_site_root = ET.XSLT.strparam(request.script_root)

    html = transform_xml(xml, siteRoot=args_site_root)

    return str(html)


def get_catalogo_geonetwork_info():
    md_tipos_servicos = db.session.query(MDTipoServico).order_by(MDTipoServico.name).all()
    md_tipos_recursos = db.session.query(MDTipoRecurso).order_by(MDTipoRecurso.name).all()
    md_categorias = db.session.query(MDCategoria).order_by(MDCategoria.name).all()
    md_temas_inspire = db.session.query(MDTemaInspire).order_by(MDTemaInspire.t2).order_by(MDTemaInspire.t1).all()

    cat_info = {"tipos_servicos": md_tipos_servicos, "tipos_recursos": md_tipos_recursos,
                "categorias": md_categorias, "temas_inspire": md_temas_inspire}

    return cat_info


def get_catalogo_geoportal_info():
    md_categorias = db.session.query(MDCategoria).order_by(MDCategoria.name).all()
    md_tipos_recursos_snig = db.session.query(MDTipoRecursoSNIG).order_by(MDTipoRecursoSNIG.name).all()

    cat_info = {"tipos_recursos_snig": md_tipos_recursos_snig, "categorias": md_categorias}

    return cat_info
