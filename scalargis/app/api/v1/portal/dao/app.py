import logging
import os
import json
import re
import base64
import uuid
import requests
from datetime import datetime

from flask import request, current_app, url_for, render_template
from flask_security import current_user
from sqlalchemy import func
from flask_restx import marshal
from shapely.wkt import loads

from app.utils import geo
from app.utils import constants
from app.utils.constants import ROLE_ANONYMOUS
from app.utils.settings import get_site_settings, get_config_value
from app.utils.security import get_roles_names, get_user_roles, is_admin_or_manager
from app.utils.mailing import send_mail
from app.utils.http import get_host_url, get_script_root, get_base_url
from app.utils import auditoria
from instance import settings
from ..serializers import generic_api_model, viewer_api_model
from ..serializers.print import print_api_model, print_group_api_model
from app.models.portal import *
from ...endpoints import get_user
from . import get_record_by_id
from.notification import get_new_notifications


logger = logging.getLogger(__name__)

def get_viewer_record(viewer_id_or_slug):
    record = None

    if viewer_id_or_slug and viewer_id_or_slug.isdigit():
        #By Id
        record = get_record_by_id(Viewer, int(viewer_id_or_slug))
    elif isinstance(viewer_id_or_slug, str):
        #By slug
        record = Viewer.query.filter(func.lower(Viewer.slug)==viewer_id_or_slug.lower()).one_or_none()
        if not record:
            #By UUID
            record = Viewer.query.filter(func.lower(Viewer.uuid)==viewer_id_or_slug.lower()).one_or_none()
        if not record:
            #By Name
            record = Viewer.query.filter(func.lower(Viewer.name)==viewer_id_or_slug.lower()).one_or_none()

    return record


def get_app_default_viewer():
    user = get_user(request)

    record = None
    viewer_cfg = None
    status = 200

    if user and user.default_viewer:
        record = Viewer.query.filter(func.lower(Viewer.name) == user.default_viewer.lower()).one_or_none()
    if not record:
        record = Viewer.query.filter(Viewer.is_portal == True).one_or_none()
    if not record:
        return {}, 404

    has_permission = False
    viewer_roles = []
    user_roles = []

    has_permission, status, viewer_roles, user_roles = check_viewer_permissions(record, user)

    if not has_permission:
        return {}, status

    viewer_cfg = build_viewer_config(record, user_roles)

    auditoria.log_viewer_async(current_app._get_current_object(), record.id, None,
                               auditoria.EnumAuditOperation.VisualizarMapa, None, None, user.id if user else None)

    return viewer_cfg, status

def get_app_viewer(viewer_id_or_slug, session=False):
    user = get_user(request)

    record = None
    viewer_cfg = None
    status = 200

    user_session = session
    if 'session' in request.args:
        user_session=True

    record = get_viewer_record(viewer_id_or_slug)
    if not record:
        return {}, 404

    #Check if viewer is active. Only owner has access to an inactive owner
    if record.is_active == False and (not user or record.owner_id != user.id):
        return {}, 404

    has_permission = False
    viewer_roles = []
    user_roles = []

    has_permission, status, viewer_roles, user_roles = check_viewer_permissions(record, user)

    if not has_permission:
        return {}, status

    viewer_cfg = build_viewer_config(record, user_roles, user, user_session)

    auditoria.log_viewer_async(current_app._get_current_object(), record.id, None,
                               auditoria.EnumAuditOperation.VisualizarMapa, None, None, user.id if user else None)

    return viewer_cfg, status


def get_viewer_session_record(viewer_id, user_id):
    status = 200
    record = UserViewerSession.query.\
        filter(UserViewerSession.viewer_id == viewer_id, UserViewerSession.user_id == user_id).one_or_none()

    if not record:
        return None, 404

    return record, status


def save_viewer_session(viewer_id_or_slug, data):
    status = 200

    response = {
        "id": None, "viewer_uuid": None, "success": False
    }

    viewer = get_viewer_record(viewer_id_or_slug)
    if not viewer:
        return response, 404

    user = get_user(request)
    if not user or not user.is_authenticated or not user.is_active:
        return response, 401

    record, status = get_viewer_session_record(viewer.id, user.id)

    date_session = datetime.now()
    if not record:
        record = UserViewerSession()
        record.user_id = user.id
        record.viewer_id = viewer.id
        record.created_at = date_session
        record.id_user_create = user.id
        status = 201
    else:
        record.id_user_update = user.id
        record.updated_at = date_session
        status = 200

    record.config_version = '1.0'
    config_json = json.loads(data['config_json']) if isinstance(data['config_json'], str) else data['config_json']
    record.config_json = json.dumps(config_json)

    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)

    response = {
            "id": record.id,
            "viewer_uuid": viewer.uuid,
            "session": {"id": record.id, "date": date_session.isoformat()},
            "success": True
        }

    return  response, status


def send_viewer_contact_message(viewer_id, data):
    status = 200

    response = {
        "id": None, "viewer_uuid": None, "success": False
    }

    viewer = get_viewer_record(viewer_id)
    if not viewer:
        return response, 404

    user_id = None
    user = get_user(request)
    if user and user.is_authenticated and user.is_active:
        user_id = user.id

    # CAPTCHA validation
    if user_id is None and get_config_value('CAPTCHA_SECRET_KEY'):
        captcha_url = 'https://www.google.com/recaptcha/api/siteverify'
        captcha_url = get_config_value('CAPTCHA_URL') if get_config_value('CAPTCHA_URL') else captcha_url
        pdata = {
            'secret': get_config_value('CAPTCHA_SECRET_KEY'),
            'response': data['captcha']
            }
        captcha_error_response = {
            "success": False,
            "message": 'Envio da mensagem não autorizado'
        }
        presp = requests.post(captcha_url, data=pdata)
        if presp.status_code == 200:
            if presp.json()['success'] is not True:
                return captcha_error_response, 403
        else:
            return captcha_error_response, 403

    attachments = []

    message_uuid = str(uuid.uuid4().hex)

    record = ContactMessage()

    record.viewer_id = viewer_id
    if user and user.is_authenticated:
        record.name = user.name or user.username or user.email
        record.email = user.email
    else:
        record.name =  data['name'] if 'name' in data else None
        record.email = data['email'] if 'email' in data else None
    # GET message text from message or description field
    record.message = data['message'] if 'message' in data else None
    record.message = data['description'] if 'description' in data else None

    record.message_json = json.dumps(data, indent = 4)

    record.user_id = user_id
    record.message_date = datetime.now()
    record.message_uuid = message_uuid

    #------ Files -------------------------------
    if 'files' in data:
        folder_path = None

        if os.path.exists(get_config_value('EMAIL_NOTIFICATIONS_FOLDER')):
            folder_path = get_config_value('EMAIL_NOTIFICATIONS_FOLDER')
        elif os.path.exists(get_config_value('APP_UPLOADS')):
            folder_path = os.path.join(get_config_value('APP_UPLOADS'), 'notifications')
        elif os.path.exists(get_config_value('APP_TMP_DIR')):
            folder_path = os.path.join(get_config_value('APP_TMP_DIR'), 'notifications')

        if folder_path:
            folder_path = os.path.join(folder_path, message_uuid)
            for f in data.get('files'):
                original_filename = f.get('filename')
                name, extension = os.path.splitext(original_filename)
                filename = str(uuid.uuid4().hex)
                if extension:
                    filename = '{}{}'.format(str(uuid.uuid4().hex), extension)

                # Reference: https://www.codestudyblog.com/sfb2002b1/0225213558.html
                file_dict = re.match("data:(?P<type>.*?);(?P<encoding>.*?),(?P<data>.*)",
                                     f.get('data')).groupdict()

                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)

                filepath = os.path.join(folder_path, original_filename)

                output = open(filepath, 'wb')
                output.write(base64.b64decode(file_dict['data']))
                output.close()

                file_stats = os.stat(filepath)

                attachments.append({ "filename": original_filename, "filepath": filepath})
    #------ End Files ---------------------------

    db.session.add(record)

    db.session.commit()

    html = 'Mensagem submetida com sucesso. Obrigado pela sua participação.'

    send_email_notification(viewer_id=viewer_id, notification_id=record.id, notification_uuid=record.message_uuid,
                            author_name=record.name, author_email=record.email,
                            message_text=record.message, message_date=record.message_date,
                            attachments=attachments)

    auditoria.log_viewer(viewer_id, None, auditoria.EnumAuditOperation.ContactoMensagem, None, None, user_id)

    response = {
        "success": True,
        "message": html
        }

    return response, status


def get_app_viewer_print_group_details(viewer_id, group_id):
    user = get_user(request)

    status = 200

    viewer = db.session.query(Viewer).filter(Viewer.id == viewer_id).one_or_none()
    if viewer is None:
        return {}, 404

    has_permission, status, viewer_roles, user_roles = check_viewer_permissions(viewer, user)
    if not has_permission:
        return {}, status

    group = db.session.query(PrintGroup).filter(PrintGroup.id == group_id).one_or_none()
    if group is None:
        return {}, 404

    group_cfg = {}
    group_uuid = uuid.uuid4()

    geom_filter = None
    geom_proj = None

    if 'geom_filter' in request.json:
        geoms = request.json['geom_filter']
        geoms_out = []
        if len(geoms)>0:
            for gm in geoms:
                gm = loads(gm)
                if group.tolerance_filter is not None and group.tolerance_filter != 0:
                    gm = gm.buffer(group.tolerance_filter)
                geoms_out.append(gm.wkt)
            geom_filter = geo.getGeometryFromWKT(geoms_out)

    if geom_filter:
        geom_proj = 'epsg:{0}'.format(request.json['geom_srid'])

    group_cfg = filter_print_group(viewer, group, geom_filter, geom_proj, user_roles, group.show_all_prints or False)

    if not group_cfg:
        return {}, 404

    #-- Layouts --#
    groups_layouts = []
    for l in group.layouts:
        groups_layouts.append({'id': l.id, 'format': l.format, 'orientation': l.orientation})

    prints_layouts = []
    fill_layouts_from_print_group(group, prints_layouts)

    group_cfg['layouts'] = { 'group': groups_layouts, 'prints': prints_layouts }
    # -- End Layouts --#

    return group_cfg, status

#-----------------------------------------------------------------------


def check_viewer_permissions(viewer, user):
    has_permission = True
    status = 200

    viewer_roles = get_roles_names(viewer.roles, False)
    user_roles = get_user_roles(user)

    if len(viewer_roles) > 0 and constants.ROLE_ADMIN not in user_roles and \
                    len(set(user_roles).intersection(viewer_roles)) == 0:
        has_permission = False
        if user and user.is_authenticated:
            status = 403
        else:
            status = 401

    if user and user.is_authenticated and viewer.owner_id == user.id:
        has_permission = True
        status = 200

    return has_permission, status, viewer_roles, user_roles


def filter_print_group(viewer, group, geom_filter, geom_proj, user_roles, show_all):

    group_roles = get_roles_names(group.roles, False)

    # Check roles permissions
    if not (len(group_roles) == 0 or constants.ROLE_ADMIN in user_roles or len(set(user_roles).intersection(group_roles)) > 0):
        return None

    # Check geom filter
    if geom_filter is not None and group.geometry_wkt is not None:
        geom_print = geo.transformGeom(loads(group.geometry_wkt), 'epsg:{0}'.format(PrintGroup.geometry_srid),
                                       geom_proj)
        if not geom_filter.intersects(geom_print):
            return None

    clone = {'id': group.id, 'title': group.title, 'description': group.description, 'children': [],
                 'allow_selection': group.select_prints, 'merge_prints': group.group_prints,
                 'prints': [], 'geom_wkt': group.geometry_wkt,
                 'resource_url': url_for('api.app_app_print_group_details', viewer_id=viewer.id,
                                         group_id=group.id)}

    for p in sorted(group.print_assoc, key=lambda x: x.order or 1):
        print = p.print

        print_roles = get_roles_names(print.roles,False)

        if len(print_roles) == 0 or constants.ROLE_ADMIN in user_roles or \
                        len(set(user_roles).intersection(print_roles)) > 0:
            if geom_filter is None or print.geometry_wkt is None:
                layouts = []
                for l in print.layouts:
                    layouts.append({'id': l.id, 'format': l.format, 'orientation': l.orientation })

                clone.get('prints').append({'id': print.id, 'name': print.name, 'title': print.title,
                                                'description': print.description,
                                                'code': print.code, 'srid': print.srid, 'format': print.format,
                                                'orientation': print.orientation, 'layouts': layouts})
            elif len(print.geometry_wkt) > 0:
                geom_print = geo.transformGeom(loads(print.geometry_wkt), 'epsg:{0}'.format(Print.geometry_srid), geom_proj)
                if geom_filter.intersects(geom_print):
                    layouts = []
                    for l in print.layouts:
                        layouts.append({'id': l.id, 'format': l.format, 'orientation': l.orientation})

                    clone.get('prints').append({'id': print.id, 'name': print.name, 'title': print.title,
                        'description': print.description,
                        'code': print.code, 'srid': print.srid, 'format': print.format,
                        'orientation': print.orientation, 'layouts': layouts})

    for child in sorted(group.print_group_child_assoc, key=lambda x: x.order or 1):
        original_child = child.print_group_child

        clone_child = filter_print_group(viewer, original_child, geom_filter, geom_proj, user_roles, show_all)

        if clone_child:
            clone_child['order'] = child.order
            clone.get('children').append(clone_child)

    if len(clone.get('children')) > 0 or len(clone.get('prints')) > 0 or show_all:
        return clone
    else:
        return None


def fill_layouts_from_print_group(group, layouts):
    for prt in group.print_assoc:
        p = prt.print
        if all([p.format, p.orientation]) and {'format': p.format, 'orientation': p.orientation} not in layouts:
            layouts.append({'format': p.format, 'orientation': p.orientation})
        for l in p.layouts:
            if all([l.format, l.orientation]) and {'format': l.format, 'orientation': l.orientation} not in layouts:
                layouts.append({'format': l.format, 'orientation': l.orientation})

    for c in group.print_group_child_assoc:
        fill_layouts_from_print_group(c.print_group_child, layouts)


def build_viewer_config(record, user_roles, user=None, session=False):
    viewer_cfg = marshal(record, viewer_api_model)
    viewer_cfg['is_session'] = False

    site_settings_db = get_site_settings()

    #Load User Session (only if allowed and user is authenticated)
    if record and record.allow_user_session and user:
        viewer_session = UserViewerSession.query.\
            filter(UserViewerSession.viewer_id == record.id, UserViewerSession.user_id == user.id).one_or_none()

        if viewer_session:
            date_session = viewer_session.created_at
            if viewer_session.updated_at:
                date_session = viewer_session.updated_at
            viewer_cfg['session'] = { "id": viewer_session.id, "date": date_session.isoformat() }

            if session:
                session_cfg = json.loads(viewer_session.config_json)
                viewer_cfg['config_json'] = session_cfg
                viewer_cfg['is_session'] = True

    '''
     Apply components permissions
     '''
    if 'config_json' in viewer_cfg and 'components' in viewer_cfg['config_json']:
        cmps = []
        for cmp in viewer_cfg['config_json']['components']:
            cmp_roles = cmp['roles'] if 'roles' in cmp else []
            if len(cmp_roles) == 0 or constants.ROLE_ADMIN in user_roles or \
                            len(set(user_roles).intersection(cmp_roles)) > 0:
                cmps.append(cmp)

        viewer_cfg['config_json']['components'] = cmps


    viewer_cfg['printing'] = {}

    viewer_cfg['printing']['prints'] = []
    for prt in sorted(record.print_assoc, key=lambda x: x.order or 1):
        print_roles = get_roles_names(prt.print.roles, False)
        if len(print_roles) == 0 or constants.ROLE_ADMIN in user_roles or \
                        len(set(user_roles).intersection(print_roles)) > 0:
            prt_cfg = marshal(prt.print, print_api_model)
            prt_cfg['order'] = prt.order
            viewer_cfg['printing']['prints'].append(prt_cfg)

    viewer_cfg['printing']['groups'] = []
    for grp in sorted(record.print_group_assoc, key=lambda x: x.order or 1):
        group_roles = get_roles_names(grp.print_group.roles, False)
        if len(group_roles) == 0 or constants.ROLE_ADMIN in user_roles or len(
                set(user_roles).intersection(group_roles)) > 0:

            grp_cfg = marshal(grp.print_group, print_group_api_model)
            grp_cfg['order'] = grp.order
            grp_cfg['resource_url'] = url_for('api.app_app_print_group_details',
                                               viewer_id=record.id, group_id=grp.print_group.id)
            viewer_cfg['printing']['groups'].append(grp_cfg)

    '''
    Set calculated properties
    '''
    if viewer_cfg and user and user.is_authenticated and user.id == record.owner_id:
        viewer_cfg['is_owner'] = True
    else:
        viewer_cfg['is_owner'] = False

    viewer_cfg['allow_anonymous'] = False
    for r in record.roles:
        if r.name == ROLE_ANONYMOUS:
            viewer_cfg['allow_anonymous'] = True
            break

    viewer_cfg['allow_add_layers'] = False
    if viewer_cfg.get('config_json', None) and viewer_cfg.get('config_json').get('components', None):
        for c in viewer_cfg.get('config_json').get('components'):
            if c.get('type', None) == 'ThemeWizard':
                viewer_cfg['allow_add_layers'] = True
                break

    #Get general settings
    #USER INFO
    if viewer_cfg and user and user.is_authenticated:
        viewer_cfg['user_info'] = {
            "user": user.id,
            "username": user.name,
            "name": user.name,
            "email": user.email
        }

    #INTEGRATED AUTHENTICATION
    authmode = False
    if hasattr(settings, 'INTEGRATED_AUTHENTICATION'):
        authmode = True if (settings.INTEGRATED_AUTHENTICATION or '').lower() == 'true' else False
    if 'integrated_authentication' in site_settings_db:
        authmode = True if (site_settings_db['integrated_authentication'] or '').lower() == 'true' else False
    viewer_cfg['integrated_authentication'] = authmode

    if (authmode):
        authkey = None
        if hasattr(settings, 'INTEGRATED_AUTHENTICATION_KEY'):
            authkey = settings.INTEGRATED_AUTHENTICATION_KEY or None
        if 'integrated_authentication_key' in site_settings_db:
            authkey = site_settings_db['integrated_authentication_key'] or None
        if authkey:
            viewer_cfg['integrated_authentication_key'] = authkey

    #MAXFILESIZE (KB)
    maxfilesize = 2048
    if hasattr(settings, 'UPLOAD_MAXFILESIZE'):
        maxfilesize = int(settings.UPLOAD_MAXFILESIZE)
    if 'upload_maxfilesize' in site_settings_db:
        maxfilesize = int(site_settings_db['upload_maxfilesize'])
    viewer_cfg['upload_maxfilesize'] = maxfilesize

    #CONTACT_INFO
    contact_info = None
    if hasattr(settings, 'CONTACT_INFO'):
        contact_info = settings.CONTACT_INFO
    if 'contact_info' in site_settings_db:
        contact_info = site_settings_db['contact_info']
    if contact_info:
        viewer_cfg['contact_info'] = contact_info

    #CAPTCHA
    captcha_site_key = get_config_value('CAPTCHA_SITE_KEY')
    if captcha_site_key:
        viewer_cfg['captcha_key'] = captcha_site_key

    return viewer_cfg


def get_data_layer(layer_id):
    record = None
    data = None
    status = 200

    user = get_user(request)

    if layer_id and layer_id.isdigit():
        #By Id
        record = get_record_by_id(UserDataLayer, int(layer_id))
    elif isinstance(layer_id, str):
        #By uuid
        record = UserDataLayer.query.filter(func.lower(UserDataLayer.uuid) == layer_id.lower()).one_or_none()

    if not record:
        filepath = os.path.join(settings.APP_TMP_DIR, layer_id + '.geojson')

        if not os.path.isfile(filepath):
            return {}, 404

        data = None
        metadata = None

        with open(filepath, encoding="utf8") as f:
            data = json.load(f)

        metadata_filepath = os.path.join(settings.APP_TMP_DIR, layer_id + '.metadata')
        if os.path.isfile(metadata_filepath):
            with open(filepath, encoding="utf8") as m:
                metadata = json.load(m)

        record = UserDataLayer()
        record.uuid = layer_id
        record.data_geojson = json.dumps(data)
        if metadata:
            record.metadata_geojson = json.dumps(metadata)
        record.is_private = False
        record.allow_anonymous = True
        record.is_active = True
        record.created_at = datetime.now()
        if user and current_user.is_authenticated:
            record.id_user_create = user.id
            record.owner_id = user.id

    if record:
        record.last_access = datetime.now()

        db.session.add(record)
        db.session.commit()
        db.session.refresh(record)
    else:
        return {}, 404

    if not record.is_active:
        return {}, 404

    if record.is_private:
        if not user:
            return {}, 401
        if not user.is_authenticated:
            return {}, 401
        elif record.owner_id and user.id != record.owner_id:
            return {}, 403

    if not record.allow_anonymous:
        if not user or not user.is_authenticated or not user.is_active:
            return {}, 401

    if record.data_geojson:
        data = json.loads(record.data_geojson)

    return data, status


def get_app_viewer_print_generate(viewer_id, print_code):
    user = None
    data = None
    status = 200

    from app.modules.print.controllers import viewer_generate_pdf

    user = get_user(request)

    data = viewer_generate_pdf(print_code, user)

    return data, status


def get_app_viewer_print_merge(viewer_id):
    user = None
    data = None
    status = 200

    from app.modules.print.controllers import viewer_merge_pdf

    user = get_user(request)

    data = viewer_merge_pdf(user)

    return data, status


def get_viewer_translations(viewer_id):
    data = None
    status = 200

    viewer = get_viewer_record(viewer_id)

    if not viewer:
        return data, 404

    record = SiteSettings.query.\
            filter(SiteSettings.code.ilike('TRANSLATIONS_' + viewer.name)).one_or_none()
    if record:
        try:
            data = json.loads(record.setting_value)
            return data, status
        except:
            pass

    record = SiteSettings.query. \
        filter(SiteSettings.code.ilike('TRANSLATIONS')).one_or_none()
    if record:
        try:
            data = json.loads(record.setting_value)
            return data, status
        except:
            pass

    return None, status

    '''
    data = {
        "common": {
            "en": {
                "viewer_translations": "viewer_translations EN"
            },
            "pt": {
                "viewer_translations": "viewer_translation PT"
            }
        },
        "DataForm": {
            "en": {
                "teste": "teste2EN",
                "teste_dataform": "Teste DataForm EN",
                "Alojamento Local": "Alojamento Local1",
                "Bar": "Bar1",
                "FooBar": "FooBar1"
            },
            "pt": {
                "teste": "teste2PT",
                "teste_dataform": "Teste DataForm PT",
                "Alojamento Local": "Alojamento Local2",
                "Bar": "Bar2",
                "FooBar": "FooBar2"
            }
        },
        "lists": {
            "en": {
                "housing": {
                    "Alojamento Local": "Alojamento Local11",
                    "Bar": "Bar11",
                    "FooBar": "FooBar11",
                    "Apartamento": "Apartamento11",
                    "Moradia": "Motaria11"
                }
            },
            "pt": {
                "housing": {
                    "Alojamento Local": "Alojamento Local21",
                    "Bar": "Bar21",
                    "FooBar": "FooBar21",
                    "Apartamento": "Apartamento21",
                    "Moradia": "Moradia21"
                }
            }
        }
    }
    '''


def get_app_backoffice():
    user = get_user(request)

    record = None
    backoffice_cfg = None
    status = 200

    if not user:
        return {}, 401

    has_permission = False
    backoffice_roles = []
    user_roles = []

    has_permission, status, backoffice_roles, user_roles = check_backoffice_permissions(user)

    if not has_permission:
        return {}, 403

    def filter_actions(actions):
        ret_actions = [d for d in actions if ('roles' not in d) or (len(set(d['roles']).intersection(user_roles)) > 0)]

        for a in ret_actions:
            if 'items' in a:
                a['items'] = filter_actions(a['items'])
                #if len(a['items']) < 1:
                #    del a['items']

        return ret_actions

    backoffice_cfg = json.loads( json.dumps( current_app.config.get('BACKOFFICE_CONFIG')))
    menu_actions = backoffice_cfg.get('config').get('menu')

    menu_actions_filter = filter_actions(menu_actions)
    menu_actions_filter = [d for d in menu_actions_filter if ('items' not in d) or len(d['items']) > 0]

    backoffice_cfg.get('config')['menu'] = menu_actions_filter

    #-- Get Coordinate Systems --
    coord_sys_records = db.session.query(CoordinateSystems).all()
    if coord_sys_records:
        crs_data = marshal(coord_sys_records, generic_api_model)
        backoffice_cfg.get('config')['coordinate_systems'] = crs_data
    #-- End --

    #-- Get Notifications --
    notifications = get_new_notifications()
    backoffice_cfg.get('config')['notifications'] = { "total": notifications if notifications is not None else 0}

    #-- Stats --
    if 'stats' in backoffice_cfg.get('config'):
        is_admin = is_admin_or_manager(user)

        if not is_admin or (is_admin and not 'viewers' in backoffice_cfg.get('config')['stats']):
            qy = db.session.query(Viewer.id, Viewer.name)
            if not is_admin:
                backoffice_cfg.get('config')['stats']['viewers'] = None
                if user:
                    owner_id = user.id
                    if owner_id:
                        qy = qy.filter(Viewer.owner_id == owner_id)

            viewers_records = qy.order_by('name').all()
            if viewers_records and len(viewers_records) < 250:
                viewers_data = list(map(lambda r: {"value": str(r.id), "label": r.name}, viewers_records))

                backoffice_cfg.get('config')['stats']['viewers'] = viewers_data

    auditoria.log_backoffice_async(current_app._get_current_object(), auditoria.EnumAuditOperation.BackOffice,
                                   user.id if user else None)

    return backoffice_cfg, status


def check_backoffice_permissions(user):
    has_permission = True
    status = 200

    '''
    viewer_roles = get_roles_names(viewer.roles, False)
    user_roles = get_user_roles(user)

    if len(viewer_roles) > 0 and constants.ROLE_ADMIN not in user_roles and \
                    len(set(user_roles).intersection(viewer_roles)) == 0:
        has_permission = False
        if user and user.is_authenticated:
            status = 403
        else:
            status = 401

    return has_permission, status, viewer_roles, user_roles
    '''

    backoffice_roles = [ constants.ROLE_AUTHENTICATED ]
    #backoffice_roles = [ constants.ROLE_MANAGER ]

    user_roles = get_user_roles(user)

    if constants.ROLE_ADMIN not in user_roles and len(set(user_roles).intersection(backoffice_roles)) == 0:
        has_permission = False
        if user and user.is_authenticated and user.is_active:
            status = 403
        else:
            status = 401

    return has_permission, status, backoffice_roles, user_roles


def send_email_notification(viewer_id, notification_id, notification_uuid, author_name, author_email,
                            message_text, message_date, attachments = None):
    send_email_notifications_admin = False
    email_notifications_admin = None

    # TODO: use more elegant import
    from app.main import app as main_app

    notification_url = url_for('backoffice.index', path='notifications/edit/{}'.format(str(notification_id)))

    #Send email to notification author
    message_html = render_template("/v1/map/notification/email_map_issue_user.html",
                                   APP_HOST_URL=get_host_url(),
                                   APP_SCRIPT_ROOT=get_script_root(),
                                   APP_BASE_URL=get_base_url(),
                                   notification_id=notification_id, notification_uuid=notification_uuid,
                                   message_text=message_text, message_date=message_date,
                                   notification_url=notification_url)

    # Send email to notification admins
    if 'SCALARGIS_SEND_EMAIL_NOTIFICATIONS_USER' in current_app.config.keys() and current_app.config['SCALARGIS_SEND_EMAIL_NOTIFICATIONS_USER']:
        send_mail(main_app, [author_email], 'Confirmação de Envio de Pedido/Participação', message_html)

    if 'SCALARGIS_SEND_EMAIL_NOTIFICATIONS_ADMIN' in current_app.config.keys() and current_app.config['SCALARGIS_SEND_EMAIL_NOTIFICATIONS_ADMIN']:
        send_email_notifications_admin = True

    if 'SCALARGIS_EMAIL_NOTIFICATIONS_ADMIN' in current_app.config.keys() and current_app.config['SCALARGIS_EMAIL_NOTIFICATIONS_ADMIN']:
        email_notifications_admin = current_app.config['SCALARGIS_EMAIL_NOTIFICATIONS_ADMIN']

    if send_email_notifications_admin and viewer_id:
        viewer = db.session.query(Viewer).filter(Viewer.id == viewer_id).first()
        if viewer and viewer.send_email_notifications_admin is not None:
            send_email_notifications_admin = viewer.send_email_notifications_admin
        if viewer and viewer.email_notifications_admin is not None:
            email_notifications_admin = viewer.email_notifications_admin.split(',')

    if send_email_notifications_admin and email_notifications_admin:
        message_html = render_template("/v1/map/notification/email_map_issue_admin.html",
                                       APP_HOST_URL=get_host_url(),
                                       APP_SCRIPT_ROOT=get_script_root(),
                                       APP_BASE_URL=get_base_url(),
                                       notification_id=notification_id, notification_uuid=notification_uuid,
                                       message_text=message_text, message_date=message_date,
                                       notification_url=notification_url)
        send_mail(main_app, email_notifications_admin,
                  '{} - {}'.format('Notificação de Receção de Pedido/Participação', viewer.title),
                  message_html=message_html, message_text=None, attachments=attachments)
