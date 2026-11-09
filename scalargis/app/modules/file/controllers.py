import os
import os.path
import uuid

from flask import Blueprint, send_file, request, jsonify, abort, url_for, Response

from app.models.files import DocumentDirectory
from app.database import db
from instance import settings
from app.utils import http
from app.utils.files import bare_filename, contained_path, request_user


mod = Blueprint('file',  __name__, template_folder='templates', static_folder='static')


@mod.route('/file/<filename>')
def get(filename):
    filepath = contained_path(settings.APP_TMP_DIR, filename)
    if filepath is None:
        abort(404)
    try:
        return send_file(filepath,
                         #attachment_filename=filename)
                         download_name=filename)
    except Exception as e:
        return str(e)


@mod.route('/file/<folder>', defaults={'path': ''}, methods=['GET', 'HEAD', 'OPTIONS'])
@mod.route('/file/<folder>/<path:path>', methods=['GET', 'HEAD', 'OPTIONS'])
@http.crossdomain(origin='*', methods=['GET', 'DELETE', 'HEAD', 'OPTIONS'], headers=['Origin', 'Content-Type', 'X-API-KEY'])
def get_file_tmp_folder(folder, path):
    if settings.APP_TMP_DIR is None:
        abort(404)
    else:
        filepath = contained_path(settings.APP_TMP_DIR, folder, path)
        if filepath is None or not os.path.exists(filepath):
            #Get file based on document directory folder (for compatibility issues)
            return get_file_folder(folder, path)
            #abort(404)

    if request.method == 'HEAD':
        response = Response()
        response.headers.add('content-length', str(os.path.getsize(filepath)))
        return response

    try:
        return send_file(os.path.join(filepath),
                         #attachment_filename=os.path.basename(path))
                         download_name=os.path.basename(path))
    except Exception as e:
        return str(e)


@mod.route('/file/plantas/template/<filename>')
def get_planta_template(filename):
    filepath = contained_path(os.path.join(settings.APP_RESOURCES, 'pdf'), filename)
    if filepath is None:
        abort(404)
    try:
        return send_file(filepath,
                         #attachment_filename=filename)
                         download_name=filename)
    except Exception as e:
        return str(e)


@mod.route('/docs/<folder>/<filename>')
def get_doc_file(folder, filename):

    dir = db.session.query(DocumentDirectory).filter(DocumentDirectory.codigo.ilike(folder)).first()

    filepath = None

    if dir is None:
        abort(404)
    else:
        filepath = contained_path(dir.path, filename)
        if filepath is None or not os.path.exists(filepath):
            abort(404)

    #file_ext = os.path.splitext(filename)[1][1:]

    try:
        #return send_file(filepath, attachment_filename=filename)
        return send_file(filepath, download_name=filename)
    except Exception as e:
        return str(e)


def get_file_folder(folder, path):
    dir = db.session.query(DocumentDirectory).filter(DocumentDirectory.codigo.ilike(folder)).first()

    if dir is None:
        abort(404)
    else:
        filepath = contained_path(dir.path, path)
        if filepath is None or not os.path.exists(filepath):
            abort(404)

    if request.method == 'HEAD':
        response = Response()
        response.headers.add('content-length', str(os.path.getsize(filepath)))
        return response

    try:
        return send_file(os.path.join(filepath),
                         #attachment_filename=os.path.basename(path))
                         download_name=os.path.basename(path))
    except Exception as e:
        return str(e)


@mod.route('/file/<folder>/<path:path>', methods=['DELETE', 'OPTIONS'])
@http.crossdomain(origin='*', methods=['GET', 'DELETE', 'HEAD', 'OPTIONS'], headers=['Origin', 'Content-Type', 'X-API-KEY'])
def delete_file_folder(folder, path):
    dir = db.session.query(DocumentDirectory).filter(DocumentDirectory.codigo.ilike(folder)).first()

    if dir is None:
        abort(404)
    elif not os.path.isdir(dir.path):
        return jsonify(Success=False, Message='Directory not found', Data=None), 404

    if not dir.allow_delete:
        return jsonify(Success=False, Message='Permission denied', Data=None), 403

    if not dir.delete_anonymous and request_user() is None:
        return jsonify(Success=False, Message='Permission denied', Data=None), 401

    filepath = contained_path(dir.path, path)

    if filepath is not None and os.path.isfile(filepath):
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

    if not dir.upload_anonymous and request_user() is None:
        return jsonify(Success=False, Message='Permission denied', Data=None), 401

    target_dir = contained_path(dir.path, path)
    if target_dir is None:
        abort(404)

    errors = False
    data = []

    for files_key in request.files:
        files = request.files.getlist(files_key)

        for file in files:
            filename = file.filename
            extension = os.path.splitext(filename)[1]

            if dir.upload_generate_filename:
                filename = '{}{}'.format(str(uuid.uuid4().hex), extension)

            filepath = contained_path(target_dir, filename) if bare_filename(filename) == filename else None

            if filepath is None:
                errors = True
                data.append({'upload': False, 'source': file.filename, 'filename': None, 'overwrite': None,
                             'url': None, 'message': 'Nome de ficheiro inválido.'})
            elif dir.upload_overwrite or not os.path.isfile(filepath):
                overwrite = os.path.isfile(filepath)

                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)

                file.save(filepath)

                file_url = url_for('.get_file_tmp_folder', folder=folder,
                                   path='{}/{}'.format(path, filename) if path else filename)

                data.append({'upload': True, 'source': file.filename, 'filename': filename, 'overwrite': overwrite,
                             'url': file_url, 'message': 'Upload realizado com sucesso.'})
            else:
                errors = True
                data.append({'upload': False, 'source': file.filename, 'filename': None, 'overwrite': None,
                             'url': None, 'message': 'Existe um ficheiro com o mesmo nome.'})

    saved = any(item['upload'] for item in data)

    return jsonify(Success=saved, Message=None, Errors=errors, Data=data)

