import os
import os.path
import uuid
from flask import Blueprint, send_file, request, jsonify, abort, render_template, url_for, Response
from flask_security import current_user
from app.models.files import DocumentDirectory
from app.database import db
from instance import settings
from app.utils import http
from app.utils.security import get_user_from_token

mod = Blueprint('file', __name__, template_folder='templates', static_folder='static')


@mod.route('/file/<filename>')
def get(filename):
    try:
        return send_file(os.path.join(settings.APP_TMP_DIR, filename),
                         attachment_filename=filename)
    except Exception as e:
        return str(e)


@mod.route('/file/<folder>', defaults={'path': ''}, methods=['GET', 'HEAD', 'OPTIONS'])
@mod.route('/file/<folder>/<path:path>', methods=['GET', 'HEAD', 'OPTIONS'])
@http.crossdomain(origin='*', methods=['GET', 'DELETE', 'HEAD', 'OPTIONS'],
                  headers=['Origin', 'Content-Type', 'X-API-KEY'])
def get_file_tmp_folder(folder, path):
    filepath = None

    if settings.APP_TMP_DIR is None:
        abort(404)
    else:
        filepath = os.path.join(settings.APP_TMP_DIR, folder, path)
        if not os.path.exists(filepath):
            # Get file based on document directory folder (for compatibility issues)
            return get_file_folder(folder, path)
            # abort(404)

    if request.method == 'HEAD':
        response = Response()
        response.headers.add('content-length', str(os.path.getsize(filepath)))
        return response

    try:
        return send_file(os.path.join(filepath),
                         attachment_filename=os.path.basename(path))
    except Exception as e:
        return str(e)


@mod.route('/file/plantas/template/<filename>')
def get_planta_template(filename):
    try:
        return send_file(os.path.join(settings.APP_RESOURCES, 'pdf', filename),
                         attachment_filename=filename)
    except Exception as e:
        return str(e)


@mod.route('/file/plantas/template/upload', methods=['GET', 'POST'])
def upload_planta_template():
    if request.method == 'POST':
        files = request.files.getlist("files[]")

        data = []

        for file in files:
            filepath = os.path.join(settings.APP_RESOURCES, 'pdf', file.filename)

            if not os.path.isfile(filepath):
                file.save(filepath)
                data.append({'Success': True, 'Filename': file.filename, 'Message': 'Ficheiro gravado com sucesso.'})
            else:
                data.append({'Success': False, 'Filename': file.filename,
                             'Message': 'Existe um ficheiro com o mesmo nome.'})

        return jsonify(Success=True, Message=None, Data=data)

    return jsonify(Success=False, Message='Erro', Data=None)


@mod.route('/docs/<folder>/<filename>')
def get_doc_file(folder, filename):
    dir = db.session.query(DocumentDirectory).filter(DocumentDirectory.codigo.ilike(folder)).first()

    filepath = None

    if dir is None:
        abort(404)
    else:
        filepath = os.path.join(dir.path, filename)
        if not os.path.exists(filepath):
            abort(404)

    # file_ext = os.path.splitext(filename)[1][1:]

    try:
        return send_file(filepath, attachment_filename=filename)
    except Exception as e:
        return str(e)


@mod.route('/dir/<folder>', defaults={'path': ''})
@mod.route('/dir/<folder>/<path:path>')
def get_folder(folder, path):
    filepath = None

    dir = db.session.query(DocumentDirectory).filter(DocumentDirectory.codigo.ilike(folder)).first()

    if dir is None:
        abort(404)
    else:
        filepath = os.path.join(dir.path, path)
        if not os.path.exists(filepath):
            html = path + '<P><h6>[Não existem documentos]</h6>'
            return jsonify(Success=False, Message=html, Data=None)
            # abort(404)

    map_id = None
    if 'mapId' in request.values and request.values['mapId'] != '':
        map_id = int(request.values['mapId'])

    files_filter = []
    files_exclude = []
    dirs_exclude = []

    if not request.args.get('filter') is None:
        files_filter = request.args.get('filter').split(',')

    for doc_rule in dir.rules:
        if doc_rule.mapa_id is None or doc_rule.mapa_id == map_id:
            if doc_rule.filtro is not None:
                list_filter = doc_rule.filtro.split(',')
                files_filter.extend(x.strip().lower() for x in list_filter if x not in files_filter)

            if doc_rule.excluir is not None:
                list_exclude = doc_rule.excluir.split(',')
                files_exclude.extend(x.strip().lower() for x in list_exclude if x not in files_exclude)

            if doc_rule.excluir_dir is not None:
                list_exclude_dir = doc_rule.excluir_dir.split(',')
                dirs_exclude.extend(x.strip().lower() for x in list_exclude_dir if x not in dirs_exclude)

    recursive = False if (not request.args.get('recursive') is None and
                          request.args.get('recursive').lower() == 'false') else True

    tree = path_hierarchy(request.script_root, folder, path, filepath, files_filter,
                          files_exclude, dirs_exclude, recursive)

    html = render_template("map/_dir_list.html", dir=tree, folder=folder, path=path)

    return jsonify(Success=True, Message=html, Data=tree)


@mod.route('/file/<folder>', defaults={'path': ''}, methods=['GET', 'HEAD', 'OPTIONS'])
@mod.route('/file/<folder>/<path:path>', methods=['GET', 'HEAD', 'OPTIONS'])
@http.crossdomain(origin='*', methods=['GET', 'DELETE', 'HEAD', 'OPTIONS'],
                  headers=['Origin', 'Content-Type', 'X-API-KEY'])
def get_file_folder(folder, path):
    filepath = None

    dir = db.session.query(DocumentDirectory).filter(DocumentDirectory.codigo.ilike(folder)).first()

    if dir is None:
        abort(404)
    else:
        filepath = os.path.join(dir.path, path)
        if not os.path.exists(filepath):
            abort(404)

    if request.method == 'HEAD':
        response = Response()
        response.headers.add('content-length', str(os.path.getsize(filepath)))
        return response

    try:
        return send_file(os.path.join(filepath),
                         attachment_filename=os.path.basename(path))
    except Exception as e:
        return str(e)


@mod.route('/file/<folder>/<path:path>', methods=['DELETE', 'OPTIONS'])
@http.crossdomain(origin='*', methods=['GET', 'DELETE', 'HEAD', 'OPTIONS'],
                  headers=['Origin', 'Content-Type', 'X-API-KEY'])
def delete_file_folder(folder, path):
    dir = db.session.query(DocumentDirectory).filter(DocumentDirectory.codigo.ilike(folder)).first()

    if dir is None:
        abort(404)
    elif not os.path.isdir(dir.path):
        return jsonify(Success=False, Message='Directory not found', Data=None), 404

    if not dir.allow_delete:
        return jsonify(Success=False, Message='Permission denied', Data=None), 403

    # Check Permissions
    if not dir.delete_anonymous:
        if not current_user or not current_user.is_authenticated:
            if 'X-API-KEY' in request.headers:
                token = request.headers['X-API-KEY']
                user = get_user_from_token(token)

                if not user:
                    return jsonify(Success=False, Message='Bad credentials', Data=None), 401
            else:
                return jsonify(Success=False, Message='Permission denied', Data=None), 401

    filepath = os.path.join(dir.path, path)

    if os.path.isfile(filepath):
        os.unlink(filepath)
    else:
        return jsonify(Success=False, Message='File not found', Data=None), 404

    return jsonify(Success=True, Message='Ficheiro eliminado com sucesso', Data=None)


@mod.route('/file/<folder>/upload', defaults={'path': ''}, methods=['OPTIONS', 'POST'])
@mod.route('/file/<folder>/<path:path>/upload', methods=['OPTIONS', 'POST'])
@http.crossdomain(origin='*', methods=['POST', 'OPTIONS'], headers='Origin, Content-Type, X-API-KEY')
def upload_file_folder(folder, path):
    dir = db.session.query(DocumentDirectory).filter(DocumentDirectory.codigo.ilike(folder)).first()

    if dir is None:
        abort(404)
    elif not os.path.isdir(dir.path):
        return jsonify(Success=False, Message='Directory not found', Data=None), 404

    if not dir.allow_upload:
        return jsonify(Success=False, Message='Permission denied', Data=None), 403

    # Check Permissions
    if not dir.upload_anonymous:
        if not current_user or not current_user.is_authenticated:
            if 'X-API-KEY' in request.headers:
                token = request.headers['X-API-KEY']
                user = get_user_from_token(token)

                if not user:
                    return jsonify(Success=False, Message='Bad credentials', Data=None), 401
            else:
                return jsonify(Success=False, Message='Permission denied', Data=None), 401

    errors = False
    data = []

    for files_key in request.files:
        files = request.files.getlist(files_key)

        for file in files:
            filename = file.filename
            extension = os.path.splitext(filename)[1]

            if dir.upload_generate_filename:
                filename = '{}{}'.format(str(uuid.uuid4().hex), extension)

            filepath = os.path.join(dir.path, path, filename)

            if dir.upload_overwrite or not os.path.isfile(filepath):
                overwrite = os.path.isfile(filepath)

                if not os.path.exists(os.path.join(dir.path, path)):
                    os.makedirs(os.path.join(dir.path, path))

                file.save(filepath)

                file_url = url_for('.get_file_folder', folder=folder,
                                   path='{}/{}'.format(path, filename) if path else filename)

                data.append({'upload': True, 'source': file.filename, 'filename': filename, 'overwrite': overwrite,
                             'url': file_url, 'message': 'Upload realizado com sucesso.'})
            else:
                errors = True
                data.append({'upload': False, 'source': file.filename, 'filename': None, 'overwrite': None,
                             'url': None, 'message': 'Existe um ficheiro com o mesmo nome.'})

    return jsonify(Success=True, Message=None, Errors=errors, Data=data)


def path_hierarchy(root, folder, base_path, path, files_filter, files_exclude, dirs_exclude, recursive):
    name = os.path.basename(path)

    hierarchy = {
        'name': name,
        'type': ''
    }

    if os.path.isdir(path):
        try:
            hierarchy['type'] = 'folder'
            hierarchy['folder_id'] = str(uuid.uuid4().hex)
            hierarchy['url'] = url_for('.get_folder', folder=folder, path=base_path).replace(r'//', r'/'),
            hierarchy['children'] = [
                path_hierarchy(root, folder, ''.join([base_path, r'/', contents]).replace(r'//', r'/'),
                               os.path.join(path, contents), files_filter, files_exclude, dirs_exclude, recursive)
                for contents in os.listdir(path)
                if (os.path.isdir(os.path.join(path, contents)) and not contents.lower() in tuple(dirs_exclude) and
                    recursive) or (not os.path.isdir(os.path.join(path, contents)) and
                                   (len(files_filter) == 0 or contents.lower().endswith(tuple(files_filter))) and
                                   (len(files_exclude) == 0 or not contents.lower().endswith(tuple(files_exclude)))
                                   )
            ]
        except:
            pass
    else:
        try:
            hierarchy['type'] = 'file'
            hierarchy['url'] = url_for('.get_file_folder', folder=folder,
                                       path=base_path.encode('utf8', 'surrogateescape')).replace(r'//', r'/')
        except:
            pass

    return hierarchy
