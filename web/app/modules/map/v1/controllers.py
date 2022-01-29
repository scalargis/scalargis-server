import logging
import uuid
import datetime
import requests
import json
import os
import importlib

from app.main import app
from app.database import db
from app.models.mapas import Mapa, SistemaCoordenadas, TipoPlanta, Planta, ContactoMensagem, \
    SiteSettings, MDTipoServico, MDTipoRecurso, MDTemaInspire, MDCategoria, Widget
from app.models.planos import Plano, TipoPlano
from flask import render_template, render_template_string, request, jsonify, make_response, \
    abort, current_app, redirect, url_for, flash
from flask_security import current_user
import flask_excel
from collections import OrderedDict
from pyexcel_xls import save_data as save_xls
from pyexcel_io import save_data as save_csv
from sqlalchemy import sql, or_
import shapefile
from shapely.wkt import loads
from app.models.viewerForms import TransformForm, IntersectPDMForm, IntersectCFTForm
from app.models.mapasForms import ContactoMensagemForm
from app.utils import geo, auditoria, constants, security as app_security
from app.utils.http import replace_geoserver_url
from instance import settings, strings
from app.utils.mailing import send_mail

from .. import mod


class TransformResult(db.Model):
    codigo = db.Column(db.String(50), primary_key=True)
    srid = db.Column(db.Integer())
    nome = db.Column(db.String(255))
    x = db.Column(db.Float())
    y = db.Column(db.Float())
    z = db.Column(db.Float())

    def serialize(self):
        return dict(codigo=self.codigo,
                    srid=self.srid,
                    nome=self.nome,
                    x=self.x,
                    y=self.y,
                    z=self.z)


class IntersectPDMResult(db.Model):
    rowid = db.Column(db.Integer(), primary_key=True)
    g1 = db.Column(db.Text())
    g2 = db.Column(db.Text())
    g3 = db.Column(db.Text())
    dimensao = db.Column(db.Integer())
    geom_ewkt = db.Column(db.Text())
    area = db.Column(db.Float())
    area_percent = db.Column(db.Float())
    tipo = db.Column(db.Text())

    def serialize(self):
        return dict(g1=self.g1,
                    g2=self.g2,
                    g3=self.g3,
                    geom_ewkt=self.geom_ewkt,
                    area=self.area,
                    area_percent=self.area_percent,
                    tipo=self.tipo)


class IntersectCFTResult(db.Model):
    rowid = db.Column(db.Integer(), primary_key=True)
    g1 = db.Column(db.Text())
    g2 = db.Column(db.Text())
    g3 = db.Column(db.Text())
    dimensao = db.Column(db.Integer())
    geom_ewkt = db.Column(db.Text())
    area = db.Column(db.Float())
    area_percent = db.Column(db.Float())
    tipo = db.Column(db.Text())

    def serialize(self):
        return dict(g1=self.g1,
                    g2=self.g2,
                    g3=self.g3,
                    geom_ewkt=self.geom_ewkt,
                    area=self.area,
                    area_percent=self.area_percent,
                    tipo=self.tipo)


def get_confrontation_results(config_code, iewkt, ibuffer):
    outsrid = 3763
    ibuffer = ibuffer or 0

    # get layers def
    sql_text = "select * from portal.site_settings where code like '{0}'".format(config_code or 'config_confrontation')
    result = db.session.execute(sql_text).fetchall()
    layers = result[0]['setting_value']

    sql_text = "select * from portal.intersects_layers(:layers, :ewkt, :outsrid, :buffer)"
    params = {"layers": layers, "ewkt": iewkt, "outsrid": outsrid, "buffer": ibuffer}
    result = db.session.execute(sql_text, params).fetchall()
    record = result[0]['intersects_layers']

    # Filter empty layers
    record_filtered = OrderedDict()
    record_filtered['layers'] = []
    record_filtered['output_geom'] = record['output_geom']

    for row in record['layers']:
        if len(row['results']):
            record_filtered['layers'].append(row)

    return record_filtered


def get_map_template(map):
    tmpl_file = "map/index_header.html"
    tmpl_header_file = None
    tmpl_container_file = "map/_index_container.html"
    tmpl_credits_file = "map/_credits_html.html"

    template = map.template if map.template else "header"
    if "template" in request.values and request.values.get('template'):
        template = request.values.get('template')

    for f in settings.MAP_TEMPLATES:
        if f.get("name") == template:
            if "file" in f and f.get("file"):
                tmpl_file = f.get("file")
            if "header" in f and f.get("header"):
                tmpl_header_file = f.get("header")
            if "container" in f and f.get("container"):
                tmpl_container_file = f.get("container")
            if "credits" in f and f.get("credits"):
                tmpl_credits_file = f.get("credits")

            break

    return [tmpl_file, tmpl_header_file, tmpl_container_file, tmpl_credits_file]


def get_plugins_script_files():
    files = []

    if 'PLUGINS' in current_app.config.keys():
        for plg in current_app.config['PLUGINS']:
            path = os.path.join(current_app.root_path + os.sep + 'plugins')

            if os.path.isdir(os.path.join(path, plg)) and os.path.exists(
                    os.path.join(path, plg, '__init__.py')):
                module = importlib.import_module('.' + plg, 'app.plugins')
                if hasattr(module, 'script_files'):
                    cfg_files = getattr(module, 'script_files')

                    if current_app.config['BUNDLE_FILES']:
                        if 'bundle' in cfg_files:
                            for file in cfg_files['bundle']:
                                files.append({'plugin': plg, 'blueprint': cfg_files['blueprint'], 'file': file})
                    else:
                        if 'files' in cfg_files:
                            for file in cfg_files['files']:
                                files.append({'plugin': plg, 'blueprint': cfg_files['blueprint'], 'file': file})

    return files


def get_plugin_widget_script_files(bp, widget):
    script_files = []

    try:
        path = os.path.join(current_app.root_path + os.sep + 'plugins')

        if os.path.isdir(os.path.join(path, bp.name)) and os.path.exists(os.path.join(path, bp.name, '__init__.py')):
            module = importlib.import_module('.' + bp.name, 'app.plugins')
            if hasattr(module, 'script_files'):
                cfg_files = getattr(module, 'script_files')

                if current_app.config['BUNDLE_FILES']:
                    for file in cfg_files['bundle']:
                        script_files.append({'plugin': bp.name, 'blueprint': cfg_files['blueprint'], 'file': file})
                else:
                    if 'widgets' in cfg_files:
                        for plg in cfg_files['widgets']:
                            if plg['name'] == widget:
                                if 'files' in plg:
                                    for file in plg['files']:
                                        script_files.append({'plugin': bp.name, 'blueprint': cfg_files['blueprint'],
                                                             'file': file})
    except Exception as e:
        logging.exception("message")

    return script_files


def filter_tipo_planta(tipo, geom_filter, geom_proj, show_all):
    clone = {'id': tipo.id, 'titulo': tipo.titulo, 'descricao': tipo.descricao, 'children': [],
             'seleccaoPlantas': tipo.seleccaoPlantas, 'agruparPlantas': tipo.agruparPlantas,
             'plantas': [], 'geom_wkt': tipo.geometry_wkt}

    for p in sorted(tipo.plantas, key=lambda x: x.ordem):
        planta = p.planta
        if geom_filter is None or planta.geometry_wkt is None:
            layouts = []
            for l in planta.layouts:
                layouts.append({'id': l.id, 'formato': l.formato, 'orientacao': l.orientacao})

            clone.get('plantas').append(
                {'id': planta.id, 'nome': planta.nome, 'titulo': planta.titulo, 'descricao': planta.descricao,
                 'codigo': planta.codigo, 'srid': planta.srid, 'formato': planta.formato,
                 'orientacao': planta.orientacao, 'layouts': layouts})
        elif len(planta.geometry_wkt) > 0:
            geom_print = geo.transformGeom(loads(planta.geometry_wkt), 'epsg:{0}'.format(Planta.geometry_srid),
                                           geom_proj)
            if geom_filter.intersects(geom_print):
                layouts = []
                for l in planta.layouts:
                    layouts.append({'id': l.id, 'formato': l.formato, 'orientacao': l.orientacao})

                clone.get('plantas').append(
                    {'id': planta.id, 'nome': planta.nome, 'titulo': planta.titulo, 'descricao': planta.descricao,
                     'codigo': planta.codigo, 'srid': planta.srid, 'formato': planta.formato,
                     'orientacao': planta.orientacao, 'layouts': layouts})

    # for child in tipo.tipo_planta_child_assoc:
    for child in sorted(tipo.tipo_planta_child_assoc, key=lambda x: x.ordem):
        original_child = child.tipo_planta_child
        clone_child = None
        if geom_filter is None or original_child.geometry_wkt is None:
            clone_child = filter_tipo_planta(original_child, geom_filter, geom_proj, show_all)
        elif len(original_child.geometry_wkt) > 0:
            geom_print = geo.transformGeom(loads(original_child.geometry_wkt),
                                           'epsg:{0}'.format(TipoPlanta.geometry_srid), geom_proj)
            if geom_filter.intersects(geom_print):
                clone_child = filter_tipo_planta(original_child, geom_filter, geom_proj, show_all)

        if clone_child:
            clone.get('children').append(clone_child)

    if len(clone.get('children')) > 0 or len(clone.get('plantas')) > 0 or show_all:
        return clone
    else:
        return None


def get_layouts_from_planta(planta, layouts):
    if (planta.formato, planta.orientacao) not in layouts:
        layouts.append((planta.formato, planta.orientacao))
    for l in planta.layouts:
        if (l.formato, l.orientacao) not in layouts:
            layouts.append((l.formato, l.orientacao))


def get_layouts_from_tipo(tipo, layouts):
    for p in tipo.plantas:
        if (p.planta.formato, p.planta.orientacao) not in layouts:
            layouts.append((p.planta.formato, p.planta.orientacao))
        for l in p.planta.layouts:
            if (l.formato, l.orientacao) not in layouts:
                layouts.append((l.formato, l.orientacao))

    for c in tipo.tipo_planta_child_assoc:
        get_layouts_from_tipo(c.tipo_planta_child, layouts)


def get_widget_config(widget):
    widget_config = None

    logger = logging.getLogger(__name__)

    cfg = widget.config or widget.widget.config or None
    if cfg:
        try:
            widget_config = json.loads(cfg)
        except Exception as e:
            logging.exception("message")
            return None

    return widget_config


def get_widget_roles(widget):
    widget_roles = None

    logger = logging.getLogger(__name__)

    roles = widget.roles or widget.widget.roles or None
    if roles:
        try:
            widget_roles = roles.split(';')
        except Exception as e:
            logging.exception("message")
            return None

    return widget_roles


def get_geom_from_url_params():
    geom = None
    layer = None
    layer_schema = None
    layer_name = None

    if len(request.args) > 0:
        for p in request.args:
            if p == 'layer':
                layer = request.args.get(p)
                layer_schema = layer.split(".")[0]
                layer_name = layer.split(".")[1]

    if len(request.args) > 0 and layer is not None:
        # url_params = request.args.items
        geom_field = "geom"
        geom_field_sql = "select f_geometry_column from public.geometry_columns " \
                         "where f_table_schema ilike '{0!s}' and f_table_name ilike '{1!s}'".format(layer_schema,
                                                                                                    layer_name)
        try:
            geom_field = db.session.execute(geom_field_sql).first()[0]
        except:
            pass

        # fields = {}
        sql_fields = ""
        operator = " and "
        match_type = "="
        for p in request.args:
            lower_p = p.lower()  # ...to avoid headhache with postgres fileds
            if p == 'layer':
                continue
            if p == 'operator':
                operator = " " + request.args.get(p) + " "
                continue
            if p == 'match_type':
                match_type = request.args.get(p)
                continue

            check_field_sql = "Select exists (SELECT 1 FROM information_schema.columns " \
                              "Where table_schema='{0}' And table_name='{1}' " \
                              "And column_name='{2}')".format(layer_schema, layer_name, lower_p).replace(";", "")
            check_field = db.session.execute(check_field_sql).first()
            if not check_field['exists']:
                continue

            # Always do string comparison
            val = str(request.args.get(p)) \
                # For backward compatibility, remove quotes if exists
            try:
                val = val.replace("\'", "")
            except:
                pass

            if len(sql_fields) > 0:
                sql_fields += operator + " {0}::character varying {1} '{2}' ".format(lower_p, match_type, val)
            else:
                sql_fields += " {0}::character varying {1} '{2}' ".format(lower_p, match_type, val)

        try:
            sql_str = 'select st_astext(st_snaptogrid(st_transform(st_union({0!s}),3763),0.1)) geom from {1!s} where {2!s} limit 1' \
                .format(geom_field, layer, sql_fields).replace(";", "")
            url_param_qy = db.session.execute(sql_str).first()
            geom = url_param_qy['geom']

        except:
            geom = None
    else:
        geom = None

    return geom


def send_email_notification(map_id, notification_id, notification_uuid, author_name, author_email, message_text,
                            message_date):
    send_email_notifications_admin = False
    email_notifications_admin = None
    map = None

    # Send email to notification author
    message_html = render_template("map/notification/email_map_issue_user.html",
                                   APP_SITE_ROOT=settings.APP_SITE_ROOT or '',
                                   notification_id=notification_id, notification_uuid=notification_uuid,
                                   message_text=message_text, message_date=message_date)

    # Send email to notification admins
    if 'SEND_EMAIL_NOTIFICATIONS_USER' in current_app.config.keys() and \
            current_app.config['SEND_EMAIL_NOTIFICATIONS_USER']:
        send_mail(app, [author_email], 'Confirmação de Envio de Pedido/Participação', message_html)

    if 'SEND_EMAIL_NOTIFICATIONS_ADMIN' in current_app.config.keys() and \
            current_app.config['SEND_EMAIL_NOTIFICATIONS_ADMIN']:
        send_email_notifications_admin = True

    if 'EMAIL_NOTIFICATIONS_ADMIN' in current_app.config.keys() and \
            current_app.config['EMAIL_NOTIFICATIONS_ADMIN']:
        email_notifications_admin = current_app.config['EMAIL_NOTIFICATIONS_ADMIN']

    if send_email_notifications_admin and map_id:
        map = db.session.query(Mapa).filter(Mapa.id == map_id).first()
        if map and map.send_email_notifications_admin is not None:
            send_email_notifications_admin = map.send_email_notifications_admin
        if map and map.email_notifications_admin is not None:
            email_notifications_admin = map.email_notifications_admin.split(',')

    if send_email_notifications_admin and email_notifications_admin:
        message_html = render_template("map/notification/email_map_issue_admin.html",
                                       APP_SITE_ROOT=settings.APP_SITE_ROOT or '',
                                       notification_id=notification_id, notification_uuid=notification_uuid,
                                       message_text=message_text, message_date=message_date)
        send_mail(app, email_notifications_admin,
                  '{} - {}'.format('Notificação de Receção de Pedido/Participação', map.titulo), message_html)


@mod.route('/map', defaults={'id': None}, methods=['GET'])
@mod.route('/mapa', defaults={'id': None}, methods=['GET'])
@mod.route('/map/<int:id>', methods=['GET'])
@mod.route('/mapa/<int:id>', methods=['GET'])
@mod.route('/map/<string:id>', methods=['GET'])
@mod.route('/mapa/<string:id>', methods=['GET'])
def index(id):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - map')

    map = None
    user_id = None
    auth_token = None
    show_login = True
    user_roles = [constants.ROLE_ANONYMOUS]
    if current_user and current_user.is_authenticated:
        user_id = current_user.id
        auth_token = current_user.get_auth_token()

        for ru in current_user.roles:
            user_roles.append(ru.name)
        user_roles.append(constants.ROLE_AUTHENTICATED)

    if id is None:
        if current_user.is_authenticated and current_user.default_map is not None:
            map = db.session.query(Mapa).filter(Mapa.codigo == current_user.default_map).first()

        if map is None:
            map = db.session.query(Mapa).filter(Mapa.portal == True).first()

        if map is None:
            abort(404)
        else:
            return redirect(url_for('map.index', id=map.codigo), 302)
    elif isinstance(id, int):
        map = db.session.query(Mapa).filter(Mapa.id == id).first()
    else:
        map = db.session.query(Mapa).filter(Mapa.codigo == id).first()

    if map is None:
        # return render_template("map/error.html", message="O mapa indicado não existe.")
        abort(404)

    if map.activo is False:
        return render_template("map/error.html",
                               message="O mapa não está activo. Por favor, contacte o administrador...")

    site_settings = {}
    st = db.session.query(SiteSettings).all()
    for r in st:
        site_settings[r.code] = r.setting_value

    # Get strings resources
    site_settings["strings"] = {}
    if hasattr(strings, 'STRINGS'):
        site_settings['strings'] = strings.STRINGS

    # MAP TEMPLATES
    template_file, template_header, template_container, template_credits = get_map_template(map)

    map_roles = []
    for rm in map.roles:
        map_roles.append(rm.name)

    # Copy query_string parameters
    query_string_args = {'id': id}
    for key, value in request.args.items():
        query_string_args[key] = value

    if len(set(user_roles).intersection(map_roles)) == 0:
        if current_user.is_authenticated:
            return render_template("map/error.html", message="Não tem permissões para aceder a este mapa.")
        else:
            flash("Deverá autenticar-se para ter acesso ao mapa.")
            return redirect(url_for("security.login", next=url_for("map.index", **query_string_args)))

    login_url = url_for('security.login', next=url_for("map.index", **query_string_args))
    logout_url = url_for('security.logout', next=url_for("map.index", **query_string_args))

    if len(map_roles) == 1 and map_roles[0] == constants.ROLE_ANONYMOUS:
        show_login = False

    coordenadas = db.session.query(SistemaCoordenadas).order_by(SistemaCoordenadas.ordem).all()

    catalogos = []
    for c in sorted(map.catalogos, key=lambda x: x.id):
        if c.portal:
            catalogos.insert(0, c)
        else:
            catalogos.append(c)

    tipos_plantas = []
    #for t in sorted(map.tipo_planta_assoc, key=lambda x: x.ordem):
    #    tipos_plantas.append(t.tipo_planta)
    for t in sorted(map.tipos_plantas, key=lambda x: x.ordem):
        tipos_plantas.append(t.tipo_planta)

    plantas = []
    #for p in sorted(map.planta_assoc, key=lambda x: x.ordem):
    #    plantas.append(p.planta)
    for p in sorted(map.plantas, key=lambda x: x.ordem):
        plantas.append(p.planta)

    planta = None
    layouts = []
    if len(tipos_plantas) == 0 and len(plantas) == 1:
        planta = plantas[0]
        get_layouts_from_planta(planta, layouts)

    layout_map_sizes_for_preview = settings.LAYOUT_MAP_SIZES_FOR_PREVIEW

    plugins_script_files = get_plugins_script_files()

    widgets = []
    widgets_script_files = []
    #for w in sorted(map.widget_assoc, key=lambda x: x.ordem):
    for w in sorted(map.widgets, key=lambda x: x.ordem):
        widget_permission = True
        load_widget = False

        widget_roles = get_widget_roles(w)
        # Check if user has permission for widget
        if widget_roles:
            if len(set(user_roles).intersection(widget_roles)) == 0:
                widget_permission = False

        # Load widget if user has permission
        if widget_permission:
            if w.widget.action:
                if w.widget.action.split('.')[0] in current_app.blueprints:
                    load_widget = True
                    widgets_script_files.extend(
                        get_plugin_widget_script_files(current_app.blueprints[w.widget.action.split('.')[0]],
                                                       w.widget.codigo))
            else:
                load_widget = True

        if load_widget:
            wc = {'id': w.widget.id, 'codigo': w.widget.codigo, 'titulo': w.widget.titulo,
                  'action': w.widget.action, 'template': w.widget.template, 'target': w.target or w.widget.target,
                  'parent': None,
                  'icon_css_class': w.widget.icon_css_class,
                  'html_content': w.html_content or w.widget.html_content or None,
                  'config': get_widget_config(w)}

            # Associate parent widget only if it's also in map
            if w.widget.parent:
                #if any(wp.widget_id == w.widget.parent.id for wp in map.widget_assoc):
                if any(wp.widget_id == w.widget.parent.id for wp in map.widgets):
                    wc['parent'] = {'id': w.widget.parent.id, 'codigo': w.widget.parent.codigo}
            widgets.append(wc)

    show_widget = map.show_widget
    if 'panel' in request.args and request.args['panel']:
        show_widget = request.args['panel']

    show_layers = ''
    if 'layers' in request.args and request.args['layers']:
        show_layers = request.args['layers']

    md_tipos_servicos = db.session.query(MDTipoServico).order_by(MDTipoServico.name).all()
    md_tipos_recursos = db.session.query(MDTipoRecurso).order_by(MDTipoRecurso.name).all()
    md_categorias = db.session.query(MDCategoria).order_by(MDCategoria.name).all()
    md_temas_inspire = db.session.query(MDTemaInspire).order_by(MDTemaInspire.t2).order_by(MDTemaInspire.t1).all()

    script_files = []
    for file in plugins_script_files:
        new_file = True
        for sf in script_files:
            if file['plugin'] == sf['plugin'] and file['file'] == sf['file']:
                new_file = False
                break
        if new_file:
            script_files.append(file)

    for file in widgets_script_files:
        new_file = True
        for sf in script_files:
            if file['plugin'] == sf['plugin'] and file['file'] == sf['file']:
                new_file = False
                break
        if new_file:
            script_files.append(file)

    # url params
    if len(request.args) > 0:
        url_actions_data = {'nb_params': len(request.args), 'url_args': request.args,
                            'geom': get_geom_from_url_params()}
        url_actions_data_json = json.dumps(url_actions_data)
    else:
        url_actions_data_json = json.dumps({"nb_params": 0})

    auditoria.log(map.id, None, auditoria.EnumOperacaoAuditoria.VisualizarMapa, None, None, user_id)

    header_html = None
    container_html = None

    if (map.header_html is not None) and len(map.header_html.strip()) > 0:
        try:
            header_html = render_template_string(map.header_html, user=current_user, map=map,
                                                 settings=settings, site_settings=site_settings,
                                                 script_root=request.script_root)
        except:
            header_html = '<div></div>'
            pass
    elif (template_header is not None) and len(template_header.strip()) > 0:
        header_html = render_template(template_header, user=current_user, map=map,
                                      settings=settings, site_settings=site_settings, script_root=request.script_root)
    elif 'header_html' in site_settings and (not site_settings.get('header_html') is None) and len(
            site_settings.get('header_html').strip()) > 0:
        header_html = render_template_string(site_settings.get('header_html'), user=current_user, map=map,
                                             settings=settings, site_settings=site_settings,
                                             script_root=request.script_root)
    else:
        header_html = render_template('map/_index_header.html', user=current_user, map=map,
                                      settings=settings, site_settings=site_settings, script_root=request.script_root)

    return render_template(template_file, user=current_user, settings=settings, site_settings=site_settings,
                           header_template=template_header, container_template=template_container,
                           credits_template=template_credits,
                           header_html=header_html, container_html=container_html,
                           map=map, coordenadas=coordenadas, catalogos=catalogos,
                           tipos_plantas=tipos_plantas, plantas=plantas, planta=planta, layouts=layouts,
                           layout_map_sizes_for_preview=layout_map_sizes_for_preview,
                           widgets=widgets, md_tipos_servicos=md_tipos_servicos, md_tipos_recursos=md_tipos_recursos,
                           md_categorias=md_categorias, md_temas_inspire=md_temas_inspire,
                           show_login=show_login, script_root=request.script_root, script_files=script_files,
                           auth_token=auth_token, url_param_qy=url_actions_data_json, show_widget=show_widget,
                           show_layers=show_layers, login_url=login_url, logout_url=logout_url
                           )


@mod.route('/map/<int:id>/config', methods=['GET'])
@mod.route('/mapa/<int:id>/config', methods=['GET'])
@mod.route('/map/<string:id>/config', methods=['GET'])
@mod.route('/mapa/<string:id>/config', methods=['GET'])
def get_config(id):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - map')

    user_id = None
    user_roles = [constants.ROLE_ANONYMOUS]
    if current_user and current_user.is_authenticated:
        user_id = current_user.id

        for ru in current_user.roles:
            user_roles.append(ru.name)
        user_roles.append(constants.ROLE_AUTHENTICATED)

    if id is None:
        map = db.session.query(Mapa).filter(Mapa.portal == True).first()
    elif isinstance(id, int):
        map = db.session.query(Mapa).filter(Mapa.id == id).first()
    else:
        map = db.session.query(Mapa).filter(Mapa.codigo == id).first()

    if map is None:
        return jsonify(Success=False, Message='O mapa indicado não existe.', Data=None)

    map_roles = []
    for rm in map.roles:
        map_roles.append(rm.name)

    if len(set(user_roles).intersection(map_roles)) == 0:
        return jsonify(Success=False, Message='Não tem permissões para aceder a este mapa.', Data=None)

    widgets = []
    #for w in sorted(map.widget_assoc, key=lambda x: x.ordem):
    for w in sorted(map.widgets, key=lambda x: x.ordem):
        # widgets.append(w.widget.codigo)
        load_widget = False

        if w.widget.action:
            if w.widget.action.split('.')[0] in current_app.blueprints:
                load_widget = True
        else:
            load_widget = True

        if load_widget:
            wc = {'id': w.widget.id, 'codigo': w.widget.codigo, 'titulo': w.widget.titulo,
                  'config': get_widget_config(w)}

            if w.widget.parent:
                wc['parent'] = {'id': w.widget.parent.id, 'codigo': w.widget.parent.codigo}
            widgets.append(wc)

    return jsonify(Success=True, Message=None, Data=map.configuracao.jsonConfig or None, Widgets=widgets or None,
                   Roles=user_roles or None)


@mod.route('/map/transform', methods=['POST'])
def transform():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - map')

    form = TransformForm()

    srid = form.srid.data
    x = form.x.data
    y = form.y.data
    z = form.z.data if form.z.data else 0
    map_srid = form.mapSrid.data

    sistemas = db.session.query(SistemaCoordenadas).all()

    records = db.session.query(TransformResult).from_statement(
        sql.text("select srid, codigo, nome, x, y, z from  portal.transform_coordinates(:srid, :x, :y, :z)")). \
        params(srid=srid, x=x, y=y, z=z).all()

    recs = []
    for r in records:
        sistema = next((x for x in sistemas if x.codigo == r.codigo), None)

        if sistema.unidades == 'dm':
            latlon = geo.dd2dm(r.x, r.y)

            recs.append({"srid": r.srid, "codigo": r.codigo, "unidades": "dm",
                         "nome": r.nome, "x": r.x, "y": r.y, "z": z,
                         "latlon": True, "lon": latlon['lon'], "lat": latlon['lat']})
        elif "+proj=longlat" in sistema.proj4text:
            latlon = geo.dd2dms(r.x, r.y)

            recs.append({"srid": r.srid, "codigo": r.codigo, "unidades": "d",
                         "nome": r.nome, "x": r.x, "y": r.y, "z": z,
                         "latlon": True, "lon": latlon['lon'], "lat": latlon['lat']})
        else:
            recs.append({"srid": r.srid, "codigo": r.codigo, "unidades": "m",
                         "nome": r.nome, "x": r.x, "y": r.y, "z": z,
                         "latlon": False, "lon": None, "lat": None})

    html = render_template("map/transform_results.html", records=recs)

    data = {"x": str(x), "y": str(y)}

    if srid != map_srid:
        s = next((x for x in records if x.srid == map_srid), None)
        data = {"x": str(s.x), "y": str(s.y)}

    return jsonify(Success=True, Message=html, Data=data)


@mod.route('/map/pdm/index', methods=['POST'])
def pdm_index():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - map')

    map = None
    widget = None
    widgets = []

    widget = db.session.query(Widget).filter(Widget.codigo == 'pdm').first()

    site_settings = {}
    st = db.session.query(SiteSettings).all()
    for r in st:
        site_settings[r.code] = r.setting_value

    if request.form.get('map_id') is not None:
        map_id = int(request.form.get("map_id"))
        map = db.session.query(Mapa).filter(Mapa.id == map_id).first()

        #for w in sorted(map.widget_assoc, key=lambda x: x.ordem):
        for w in sorted(map.widgets, key=lambda x: x.ordem):
            # widgets.append(w.widget.codigo)
            load_widget = False

            if w.widget.action:
                if w.widget.action.split('.')[0] in current_app.blueprints:
                    load_widget = True
            else:
                load_widget = True

            if load_widget:
                wc = {'id': w.widget.id, 'codigo': w.widget.codigo, 'titulo': w.widget.titulo,
                      'action': w.widget.action, 'target': w.widget.target, 'parent': None,
                      'icon_css_class': w.widget.icon_css_class,
                      'html_content': w.html_content or w.widget.html_content or None,
                      'config': get_widget_config(w)}

                if w.widget.parent:
                    wc['parent'] = {'id': w.widget.parent.id, 'codigo': w.widget.parent.codigo}
                widgets.append(wc)

    plans = get_planos_list()

    template = 'map/_pdm.html'
    if widget and widget.template:
        template = widget.template

    html = render_template(template, settings=settings, site_settings=site_settings, planos=plans,
                           widgets=widgets)

    return jsonify(Success=True, Message=html, Data=None)


@mod.route('/map/intersect_pdm', methods=['POST'])
def intersect_pdm():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - map')

    form = IntersectPDMForm()

    user_id = None
    if current_user and current_user.is_authenticated:
        user_id = current_user.id

    widget = None
    widget = db.session.query(Widget).filter(Widget.codigo == 'pdm_intersect').first()

    map_id = None
    if form.mapId is not None:
        map_id = form.mapId.data

    records = db.session.query(IntersectPDMResult).from_statement(
        sql.text("select * from portal.intersect_igt(:geom_ewkt, :out_srid)")). \
        params(geom_ewkt=form.geomEWKT.data, out_srid=form.srid.data).all()

    ord_list = [item for item in records if item.tipo == 'ord']
    cond_list = [item for item in records if item.tipo == 'cond']
    eem_list = [item for item in records if item.tipo == 'eem']
    serv_list = [item for item in records if item.tipo == 'serv']
    ran_list = [item for item in records if item.tipo == 'ran']
    perigosidade_list = [item for item in records if item.tipo == 'perigosidade']

    template = 'map/intersect_pdm_results.html'
    if widget and widget.template:
        template = widget.template

    html = render_template(template, records_ord=ord_list,
                           records_cond=cond_list, records_eem=eem_list, records_serv=serv_list, records_ran=ran_list,
                           records_perigosidade=perigosidade_list, geom_ewkt=form.geomEWKT.data)

    auditoria.log(map_id, None, auditoria.EnumOperacaoAuditoria.AnalisePlano, None, None, user_id)

    return jsonify(Success=True, Message=html, Data=None)


@mod.route('/map/intersect_pdm/export', methods=['GET'])
def intersect_pdm_export():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - map')

    srid = request.values['srid']
    geom_ewkt = request.values['geomEWKT']
    out_format = request.values['format']

    if out_format == 'shapefile':
        url = current_app.config["INTERSECT_PDM_URL"]
        url += "&_geom_ewkt='" + geom_ewkt + "'"
        url += "&_out_srid=" + srid

        r = requests.get(url)

        response = make_response(r.content)
        response.headers['Content-Type'] = 'application/zip'
        response.headers['Content-Disposition'] = 'attachment; filename=shapfile.zip'

        return response

    records = db.session.query(IntersectPDMResult).from_statement(
        sql.text("select * from portal.intersect_igt(:geom_ewkt, :out_srid)")). \
        params(geom_ewkt=geom_ewkt, out_srid=srid).all()

    # ord_list = [item for item in records if item.tipo == 'ord']
    # cond_list = [item for item in records if item.tipo == 'cond']
    # eem_list = [item for item in records if item.tipo == 'eem']

    # g1 = db.Column(db.Text())
    # g2 = db.Column(db.Text())
    # g3 = db.Column(db.Text())
    # dimensao = db.Column(db.Integer())
    # geom_ewkt = db.Column(db.Text())
    # area = db.Column(db.Float())
    # area_percent = db.Column(db.Float())
    # tipo = db.Column(db.Text())

    # output = io.StringIO()
    # csvdata = [1, 2, 'a', 'He said "what do you mean?"', "Whoa!\nNewlines!"]
    # writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
    # writer.writerow(csvdata)

    # data = output.getvalue()

    # response = make_response(data)

    # response.headers["Content-Disposition"] = "attachment; filename=books.csv"
    # return response

    column_names = ['g1', 'g2', 'g3', 'area', 'area_percent', 'tipo']

    file_name = "analise_pdm"

    return flask_excel.make_response_from_query_sets(records, column_names, out_format, file_name=file_name)


@mod.route('/map/intersect_pdm/export2', methods=['GET'])
def intersect_pdm_export2():
    srid = 3857
    # geom_ewkt = request.values['geomEWKT']
    # out_format = request.values['format']

    geom_ewkt = "SRID=3857;POLYGON((-896377.0307002619 4630516.955001834,-899052.3266902431 4628453.155238134,-898135.082350821 4626542.229531005,-894848.2901345583 4626389.355474435,-893166.6755122845 4628529.592266419,-893931.0457951362 4630822.703114974,-896377.0307002619 4630516.955001834))"

    records = db.session.query(IntersectPDMResult).from_statement(
        sql.text("select * from portal.intersect_igt(:geom_ewkt, :out_srid)")). \
        params(geom_ewkt=geom_ewkt, out_srid=srid).all()

    records_point = [item for item in records if item.dimensao == 0]
    records_line = [item for item in records if item.dimensao == 1]
    records_polygon = [item for item in records if item.dimensao == 2]

    # rec = records_polygon[0]
    # wkt = rec.geom_ewkt.split(';')[1]
    # geom = loads(wkt)

    # WRITE TO SHAPEFILE USING PYSHP
    shapewriter = shapefile.Writer()
    shapewriter.field("field1")

    for rec in records_polygon:
        wkt = rec.geom_ewkt.split(';')[1]
        geom = loads(wkt)

        # step1: convert shapely to pyshp using the function above
        converted_shape = geo.shapely_to_pyshp(geom)
        # step2: tell the writer to add the converted shape
        shapewriter._shapes.append(converted_shape)
        # add a list of attributes to go along with the shape
        shapewriter.record(["empty record"])

    # save it
    shapewriter.save("d:/tmp/tests4.shp")

    return "teste"


@mod.route('/map/confrontation/index', methods=['POST'])
def confrontation_index():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - map')

    map = None
    widgets = []
    config_list = None

    site_settings = {}
    st = db.session.query(SiteSettings).all()
    for r in st:
        site_settings[r.code] = r.setting_value

    if request.form.get('map_id') is not None:
        map_id = int(request.form.get("map_id"))
        map = db.session.query(Mapa).filter(Mapa.id == map_id).first()

        config_list = []
        #widget = next((w for w in map.widget_assoc if w.widget.codigo == 'confrontation'), None)
        widget = next((w for w in map.widgets if w.widget.codigo == 'confrontation'), None)
        if widget:
            widget_config = get_widget_config(widget)
            if widget_config:
                config_list = widget_config if isinstance(widget_config, list) else [widget_config]

        #for w in sorted(map.widget_assoc, key=lambda x: x.ordem):
        for w in sorted(map.widgets, key=lambda x: x.ordem):
            load_widget = False

            if w.widget.action:
                if w.widget.action.split('.')[0] in current_app.blueprints:
                    load_widget = True
            else:
                load_widget = True

            if load_widget:
                wc = {'id': w.widget.id, 'codigo': w.widget.codigo, 'titulo': w.widget.titulo,
                      'action': w.widget.action, 'target': w.widget.target, 'parent': None,
                      'icon_css_class': w.widget.icon_css_class,
                      'html_content': w.html_content or w.widget.html_content or None,
                      'config': get_widget_config(w)}

                if w.widget.parent:
                    wc['parent'] = {'id': w.widget.parent.id, 'codigo': w.widget.parent.codigo}
                widgets.append(wc)

    html = render_template("map/widget/_confrontation.html", settings=settings, site_settings=site_settings,
                           widgets=widgets, config_list=config_list)

    data = {
        "script": "Portal.Viewer.Confrontation.Load('.menu-bar-widget.confrontation'); Portal.Viewer.Confrontation.setMap(map);"
    }

    return jsonify(Success=True, Message=html, Data=data)


@mod.route('/map/intersect_cft', methods=['POST'])
def intersect_cft():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - map')

    form = IntersectCFTForm()

    user_id = None
    if current_user and current_user.is_authenticated:
        user_id = current_user.id

    config_code = 'config_confrontation'
    map_id = None
    if form.mapId is not None:
        map_id = form.mapId.data
        map = db.session.query(Mapa).filter(Mapa.id == map_id).first()

        if form.config is not None and form.config.data:
            config_code = form.config.data
        else:
            #widget = next((w for w in map.widget_assoc if w.widget.codigo == 'confrontation'), None)
            widget = next((w for w in map.widgets if w.widget.codigo == 'confrontation'), None)
            if widget:
                widget_config = get_widget_config(widget)
                if widget_config and widget_config['code']:
                    config_code = widget_config['code']

    record = get_confrontation_results(config_code, form.geomEWKT.data, form.buffer.data)
    html = render_template("map/intersect_cft_results.html", record=record, geom_ewkt=form.geomEWKT.data,
                           config_code=config_code)
    auditoria.log(map_id, None, auditoria.EnumOperacaoAuditoria.AnalisePlano, None, None, user_id)
    return jsonify(Success=True, Message=html, Data=record, geom_ewkt=form.geomEWKT.data)


@mod.route('/map/intersect_cft_export', methods=['GET'])
def intersect_cft_export():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - map')

    # Get query params
    ibuffer = request.values['buffer'] or 0
    iewkt = request.values['geomEWKT']
    iconfig = request.values['config'] or 'config_confrontation'
    out_format = request.values['format']

    # Get results
    record = get_confrontation_results(iconfig, iewkt, ibuffer)

    # Build tabular data
    data = OrderedDict()
    data['Resultados'] = []
    data['Resultados'].append(['Grupo', 'Título', 'Área', '%', 'Campos'])
    for row in record['layers']:
        records = []
        group = row['title_alias'].replace(" ", "") if row.get('title_alias') else row['title'].replace(" ", "")
        column_names = ['Grupo', 'Título', 'Área', '%']

        for field in row['fields']:
            column_names.append(field['alias'])

        records.append(column_names)

        for item in row['results']:
            l = [row['group'], row['title'], round(item['area'], 3), round(item['percent'], 3)]
            for field in row['fields']:
                l.append(item[field['field']])
            records.append(l)

            # Build main result
            rl = [row['group'], row['title'], round(item['area'], 3), round(item['percent'], 3)]

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
    file_name = "confrontacao"

    # Send XLS file
    if out_format == 'xls':
        file_name = file_name + "." + out_format
        filename = os.path.join(settings.APP_TMP_DIR, file_name)
        if os.path.exists(filename):
            os.remove(filename)
        save_xls(filename, data)
        return redirect(url_for('file.get', filename=file_name, t=uuid.uuid4()), code=302)

    # Send CSV file
    else:
        outfile = file_name + ".zip"
        filename = os.path.join(settings.APP_TMP_DIR, file_name + ".csvz")
        if os.path.exists(filename):
            os.remove(filename)
        save_csv(filename, data)
        if os.path.exists(os.path.join(settings.APP_TMP_DIR, outfile)):
            os.remove(os.path.join(settings.APP_TMP_DIR, outfile))
        os.rename(filename, os.path.join(settings.APP_TMP_DIR, outfile))
        return redirect(url_for('file.get', filename=outfile, t=uuid.uuid4()), code=302)


@mod.route('/map.drawtools_index', methods=['POST'])
def drawtools_index():
    logger = logging.getLogger(__name__)
    logger.debug('Open DrawTools widget')

    map = None
    widgets = []

    site_settings = {}
    st = db.session.query(SiteSettings).all()
    for r in st:
        site_settings[r.code] = r.setting_value

    if request.form.get('map_id') is not None:
        map_id = int(request.form.get("map_id"))
        map = db.session.query(Mapa).filter(Mapa.id == map_id).first()

        #for w in sorted(map.widget_assoc, key=lambda x: x.ordem):
        for w in sorted(map.widgets, key=lambda x: x.ordem):
            load_widget = False

            if w.widget.action:
                if w.widget.action.split('.')[0] in current_app.blueprints:
                    load_widget = True
            else:
                load_widget = True

            if load_widget:
                wc = {'id': w.widget.id, 'codigo': w.widget.codigo, 'titulo': w.widget.titulo,
                      'action': w.widget.action, 'target': w.widget.target, 'parent': None,
                      'icon_css_class': w.widget.icon_css_class,
                      'html_content': w.html_content or w.widget.html_content or None,
                      'config': get_widget_config(w)}

                if w.widget.parent:
                    wc['parent'] = {'id': w.widget.parent.id, 'codigo': w.widget.parent.codigo}
                widgets.append(wc)

    html = render_template("map/widget/_drawtools.html", settings=settings, site_settings=site_settings,
                           widgets=widgets)

    data = {
        "script": "Portal.Viewer.DrawTools.Load('.menu-bar.drawtools'); Portal.Viewer.DrawTools.setMap(map);"
    }

    return jsonify(Success=True, Message=html, Data=data)


@mod.route('/map.drawtools_export', methods=['POST'])
def drawtools_export():
    logger = logging.getLogger(__name__)
    logger.debug('Export drawings')

    # upload = request.values['upload']
    # ext = request.values['ext']
    # format = request.values['format']
    return jsonify(Success=True, Message='ok', Data=None)


@mod.route('/map/print/grupo', methods=['POST'])
def print_grupo():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - map')

    widgets = None

    id = int(request.values['id'])
    mapa_id = request.values['mapa_id']

    if mapa_id:
        map = db.session.query(Mapa).filter(Mapa.id == mapa_id).first()
        #widgets = map.widget_assoc
        widgets = map.widgets

    tipo = db.session.query(TipoPlanta).filter(TipoPlanta.id == id).first()

    layouts = []
    get_layouts_from_tipo(tipo, layouts)

    html = render_template("map/print/print_step_grupo.html", tipo=tipo, layouts=layouts, widgets=widgets)

    return jsonify(Success=True, Message=html, Data=None)


@mod.route('/map/print/planta', methods=['POST'])
def print_planta():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - map')

    map = None

    id = int(request.values['id'])
    mapa_id = request.values['mapa_id']

    if mapa_id:
        map = db.session.query(Mapa).filter(Mapa.id == mapa_id).first()

    widgets = []
    #for w in map.widget_assoc:
    for w in map.widgets:
        if w.widget.target == 'layouts':
            wc = {'id': w.widget.id, 'codigo': w.widget.codigo, 'titulo': w.widget.titulo,
                  'action': w.widget.action, 'target': w.widget.target, 'parent': None,
                  'icon_css_class': w.widget.icon_css_class,
                  'html_content': w.html_content or w.widget.html_content or None,
                  'config': get_widget_config(w)}
            widgets.append(wc)

    planta = db.session.query(Planta).filter(Planta.id == id).first()

    layouts = []
    get_layouts_from_planta(planta, layouts)

    layout_map_sizes_for_preview = settings.LAYOUT_MAP_SIZES_FOR_PREVIEW

    html = render_template("map/print/print_step_planta.html", showBack=True, planta=planta, layouts=layouts,
                           widgets_layout=widgets, layout_map_sizes_for_preview=layout_map_sizes_for_preview)

    return jsonify(Success=True, Message=html, Data=None)


@mod.route('/map/print/grupo/details', methods=['POST'])
def print_step_grupo_details():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - map')

    map = None

    id = int(request.values['id'])
    tipo = db.session.query(TipoPlanta).filter(TipoPlanta.id == id).first()
    grupo_id = uuid.uuid4()

    mapa_id = request.values['mapa_id']
    if mapa_id:
        map = db.session.query(Mapa).filter(Mapa.id == mapa_id).first()
    widgets = []
    #for w in map.widget_assoc:
    for w in map.widgets:
        if w.widget.target == 'layouts':
            wc = {'id': w.widget.id, 'codigo': w.widget.codigo, 'titulo': w.widget.titulo,
                  'action': w.widget.action, 'target': w.widget.target, 'parent': None,
                  'icon_css_class': w.widget.icon_css_class,
                  'html_content': w.html_content or w.widget.html_content or None,
                  'config': get_widget_config(w)}
            widgets.append(wc)

    layout = None
    if 'layout' in request.values and len(request.values['layout']) > 0:
        layout = request.values['layout']

    geom_filter = None
    geom_proj = None
    if 'geom_filter' in request.values and len(request.values['geom_filter']) > 0:
        geom_filter = loads(request.values['geom_filter'])
        if tipo.tolerancia is not None:
            geom_filter = geom_filter.buffer(tipo.tolerancia)
    else:
        geoms = request.form.getlist('geom_filter[]')
        geoms_out = []
        if len(geoms) > 0:
            for gm in geoms:
                gm = loads(gm)
                if tipo.tolerancia is not None:
                    gm = gm.buffer(tipo.tolerancia)
                geoms_out.append(gm.wkt)
            geom_filter = geo.getGeometryFromWKT(geoms_out)

    if geom_filter:
        geom_proj = 'epsg:{0}'.format(request.values['geom_srid'])

    layouts = []
    get_layouts_from_tipo(tipo, layouts)

    tipo_root = filter_tipo_planta(tipo, geom_filter, geom_proj, tipo.showAll or False)

    layout_map_sizes_for_preview = settings.LAYOUT_MAP_SIZES_FOR_PREVIEW

    html = render_template("map/print/print_step_grupo_details.html", tipo=tipo_root, grupo_id=grupo_id,
                           layouts=layouts, layout=layout, group=tipo, widgets=widgets,
                           layout_map_sizes_for_preview=layout_map_sizes_for_preview)

    return jsonify(Success=True, Message=html, Data=None)


@mod.route('/map/print/print_batch', methods=['POST'])
def print_step_batch():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - map')

    html = ''

    # prints = request.form.getlist('prints')
    agrupar_plantas = request.get_json().get('agruparPlantas') or False
    data = request.get_json().get('prints')

    # prints = []
    # for d in data:
    #    p = {'id': d.get('id'), 'name': d.get('name'), 'tipo_id': d.get('tipo_id')}
    #    prints.append(p)

    html = render_template("map/print/print_step_processing.html",
                           agrupar_plantas=agrupar_plantas, prints=data)

    return jsonify(Success=True, Message=html, Data={"prints": data})


@mod.route('/map/proxy', methods=['OPTIONS', 'GET', 'POST'])
def proxy():
    if request.method == 'OPTIONS':
        resp = make_response('', 200)
        resp.headers.add("Access-Control-Allow-Origin", "*")
        resp.headers.add("Access-Control-Allow-Methods", "GET, POST")
        resp.headers.add("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept")
        return resp

    url = request.args.get('url')
    if not ("getcapabilities" in url.lower()):
        url = replace_geoserver_url(url)

    s = requests.Session()

    r = None

    cookies = {}
    if 'session' in request.cookies:
        cookies['session'] = request.cookies.get('session')

    for h in request.headers.environ:
        if h.lower() == 'http_referer':
            s.headers.update({'referer': request.headers.environ.get(h)})

    if request.method == 'POST':
        r = s.post(url, data=request.data, cookies=cookies, verify=False)
    else:
        r = s.get(url, cookies=cookies, verify=False)

    resp = make_response(r.content, r.status_code)
    for h in r.headers:
        if h.lower() == 'content-type':
            resp.headers.set(h, r.headers.get(h))

    resp.headers.add("Access-Control-Allow-Origin", "*")

    return resp


def get_planos_list():
    query_planos = db.session.query(Plano)
    records = None

    if 'PLANOS_FILTER' in current_app.config.keys():
        query_planos = query_planos.outerjoin(Plano.tipo_plano).filter(
            TipoPlano.codigo.in_(current_app.config['PLANOS_FILTER']))

    query_planos = query_planos.filter(or_(Plano.anulado == None, Plano.anulado == False))

    records = query_planos.order_by(Plano.ordem).all()

    return records


@mod.route('/map/<int:map_id>/send_message', methods=['POST'])
def send_message(map_id):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - map')

    form = ContactoMensagemForm()

    user_id = None
    if current_user and current_user.is_authenticated:
        user_id = current_user.id

    record = ContactoMensagem()

    record.mapa_id = map_id
    if current_user and current_user.is_authenticated:
        record.nome = current_user.name or current_user.username or current_user.email
        record.email = current_user.email
    else:
        record.nome = form.name.data
        record.email = form.email.data
    record.mensagem = form.message.data

    record.user_id = user_id
    record.data_mensagem = datetime.datetime.now()
    record.mensagem_uuid = str(uuid.uuid4().hex)

    db.session.add(record)

    db.session.commit()

    html = 'Mensagem enviada com sucesso.'

    send_email_notification(map_id=map_id, notification_id=record.id, notification_uuid=record.mensagem_uuid,
                            author_name=record.nome,
                            author_email=record.email, message_text=record.mensagem, message_date=record.data_mensagem)

    auditoria.log(map_id, None, auditoria.EnumOperacaoAuditoria.ContactoMensagem, None, None, user_id)

    return jsonify(Success=True, Message=html, Data=None)


@mod.route('/map/show_message/<string:msg_uuid>', methods=['GET'])
def show_message(msg_uuid):
    message = db.session.query(ContactoMensagem).filter(ContactoMensagem.mensagem_uuid == msg_uuid).first()

    return render_template('map/notification/show_issue_user.html', record=message)


@mod.route('/security/login', methods=['POST'])
def login():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - map')

    token = None

    if request.is_json:
        username = request.json.get('username')
        password = request.json.get('password')
    else:
        username = ""
        password = ""

    token = app_security.get_user_token(username, password)

    user = {
        'token': token or ''
    }

    # auditoria.log(map_id, None, auditoria.EnumOperacaoAuditoria.ContactoMensagem, None, None, user_id)

    return jsonify(user=user)


@mod.route('/home', methods=['GET'])
def home():
    maps = db.session.query(Mapa).filter(Mapa.show_homepage > 0).order_by(Mapa.show_homepage)

    options = db.session.query(SiteSettings)
    homepage_template = "map/home.html"
    homepage_header = ""

    if options.filter(SiteSettings.code == 'HOMEPAGE_TEMPLATE').first() is not None:
        homepage_template = options.filter(SiteSettings.code == 'HOMEPAGE_TEMPLATE').first().setting_value

    if options.filter(SiteSettings.code == 'HOMEPAGE_HEADER').first() is not None:
        homepage_header = options.filter(SiteSettings.code == 'HOMEPAGE_HEADER').first().setting_value

    return render_template(homepage_template, maps=maps, homepage_header=homepage_header)
