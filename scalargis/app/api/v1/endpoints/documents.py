import os
import logging
import uuid
from flask import request, send_file, make_response, render_template, url_for, Response
from flask_restx import Resource

from instance import settings
from app.utils import http
from app.utils.documents import path_hierarchy
from app.database import db
from app.models.files import DocumentDirectory
from ..endpoints import ns_documents as ns, get_user


logger = logging.getLogger(__name__)


@ns.route('/temporary/<string:filename>')
@ns.response(404, 'Todo not found')
@ns.param('filename', 'The filename')
class FileFromTmpDir(Resource):
    @http.crossdomain(origin='*', methods=['GET', 'HEAD', 'OPTIONS'],
                      headers=['Origin', 'Content-Type', 'X-API-KEY'])
    def options(self, filename):
        return {'Allow': 'GET'}, 200

    '''Get a file from temporary folder'''
    @ns.doc('get_file_from_tmp_dir')
    @http.crossdomain(origin='*', methods=['GET', 'HEAD', 'OPTIONS'],
                      headers=['Origin', 'Content-Type', 'X-API-KEY'])
    def get(self, filename):
        if os.path.exists(os.path.join(settings.APP_TMP_DIR, filename)):
            response = make_response(send_file(os.path.join(settings.APP_TMP_DIR, filename),
                             download_name=filename))

            return response
        else:
            return '', 404

'''
@ns.route('/<string:folder>/<string:filename>')
@ns.response(404, 'Todo not found')
@ns.param('folder', 'The document directory')
@ns.param('filename', 'The filename')
class FileFromDir(Resource):
    @http.crossdomain(origin='*', methods=['GET', 'HEAD', 'OPTIONS'],
                      headers=['Origin', 'Content-Type', 'X-API-KEY'])
    def options(self, folder, filename):
        return {'Allow': 'GET'}, 200

    @ns.doc('get_file_from_dir')
    @http.crossdomain(origin='*', methods=['GET', 'HEAD', 'OPTIONS'],
                      headers=['Origin', 'Content-Type', 'X-API-KEY'])
    def get(self, folder, filename):

        dir = db.session.query(DocumentDirectory).filter(DocumentDirectory.codigo.ilike(folder)).one_or_none()

        filepath = None

        if dir is None:
            #ns.abort(404, 'Document directory not found')
            return { "message": "Document directory does not exists" }, 404
        else:
            filepath = os.path.join(dir.path, filename)
            if not os.path.exists(filepath):
                #ns.abort(404, 'File not found')
                return {"message": "File not found"}, 404

        try:
            response = make_response(send_file(filepath, download_name=filename))

            return response
        except Exception as e:
            #ns.abort(500, 'Internal Server Error')
            return {"message": "Internal Server Error"}, 500
'''

@ns.route('/list/<folder>', defaults={'path': ''})
@ns.route('/list/<folder>/<path:path>')
@ns.param('folder', 'The document directory')
@ns.param('path', 'The folder path')
class ListDir(Resource):
    @http.crossdomain(origin='*', methods=['GET', 'HEAD', 'OPTIONS'],
                      headers=['Origin', 'Content-Type', 'X-API-KEY'])
    def options(self, folder, path):
        return {'Allow': 'GET'}, 200

    @ns.doc('list_dir')
    @ns.doc(params={'mapId': {'description': 'Map Id',
                                'type': 'int'}})
    @ns.doc(params={'filter': {'description': 'Filter',
                                'type': 'str'}})
    @ns.doc(params={'recursive': {'description': 'Recursive',
                                'type': 'bool'}})
    @http.crossdomain(origin='*', methods=['GET', 'HEAD', 'OPTIONS'],
                      headers=['Origin', 'Content-Type', 'X-API-KEY'])
    def get(self, folder, path):
        dir = db.session.query(DocumentDirectory).filter(DocumentDirectory.codigo.ilike(folder)).one_or_none()

        if dir is None:
            return {"message": "Document directory does not exists"}, 404
        else:
            filepath = os.path.join(dir.path, path)
            if not os.path.exists(filepath):
                return {"message": "Document directory not found"}, 404

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
                if not doc_rule.filtro is None:
                    list_filter = doc_rule.filtro.split(',')
                    files_filter.extend(x.strip().lower() for x in list_filter if x not in files_filter)

                if not doc_rule.excluir is None:
                    list_exclude = doc_rule.excluir.split(',')
                    files_exclude.extend(x.strip().lower() for x in list_exclude if x not in files_exclude)

                if not doc_rule.excluir_dir is None:
                    list_exclude_dir = doc_rule.excluir_dir.split(',')
                    dirs_exclude.extend(x.strip().lower() for x in list_exclude_dir if x not in dirs_exclude)

        recursive = False if (not request.args.get('recursive') is None and request.args.get('recursive').lower() == 'false') else True

        tree = path_hierarchy('api.documents_list_dir', 'api.documents_file_dir', http.get_script_root(),
                              folder, path, filepath, files_filter, files_exclude, dirs_exclude, recursive)

        return tree



@ns.route('/<folder>/<path:path>')
@ns.param('folder', 'The document directory')
@ns.param('path', 'The file path')
class FileDir(Resource):
    @http.crossdomain(origin='*', methods=['GET', 'POST', 'DELETE', 'HEAD', 'OPTIONS'],
                      headers=['Origin', 'Content-Type', 'X-API-KEY'])
    def options(self, folder, path):
        return {'Allow': 'GET'}, 200

    @http.crossdomain(origin='*', methods=['GET', 'POST', 'DELETE', 'HEAD', 'OPTIONS'],
                      headers=['Origin', 'Content-Type', 'X-API-KEY'])
    def head(self, folder, path):
        dir = db.session.query(DocumentDirectory).filter(DocumentDirectory.codigo.ilike(folder)).one_or_none()

        if dir is None:
            return {"message": "Document directory does not exists"}, 404
        else:
            filepath = os.path.join(dir.path, path)
            if not os.path.exists(filepath):
                return {"message": "File path not found"}, 404

        response = Response()
        response.headers.add('content-length', str(os.path.getsize(filepath)))

        return response


    '''Get a file from path'''
    @ns.doc('file_dir')
    @http.crossdomain(origin='*', methods=['GET', 'POST', 'DELETE', 'HEAD', 'OPTIONS'],
                      headers=['Origin', 'Content-Type', 'X-API-KEY'])
    def get(self, folder, path):
        dir = db.session.query(DocumentDirectory).filter(DocumentDirectory.codigo.ilike(folder)).one_or_none()

        if dir is None:
            return {"message": "Document directory does not exists"}, 404
        else:
            filepath = os.path.join(dir.path, path)
            if not os.path.exists(filepath):
                return {"message": "File path not found"}, 404

        if os.path.isfile(filepath):
            try:
                response = make_response(send_file(filepath,  download_name=os.path.basename(filepath)))

                return send_file(os.path.join(filepath),
                                 download_name=os.path.basename(path))
            except Exception as e:
                return {"message": "Internal Server Error"}, 500
        else:
            return {"message": "File path not found"}, 404

    '''Delete a file from path'''
    @ns.doc('delete_file_dir')
    @http.crossdomain(origin='*', methods=['GET', 'POST', 'DELETE', 'HEAD', 'OPTIONS'],
                      headers=['Origin', 'Content-Type', 'X-API-KEY'])
    def delete(self, folder, path):
        dir = db.session.query(DocumentDirectory).filter(DocumentDirectory.codigo.ilike(folder)).one_or_none()

        if dir is None:
            return {"message": "Document directory does not exists"}, 404
        elif not os.path.isdir(dir.path):
            return {"message": "File path not found"}, 404

        if not dir.allow_delete:
            return {"message": "Forbidden"}, 403

        # Check Permissions
        if not dir.delete_anonymous:
            user = get_user(request)
            if not user:
                return {"message": "Unauthorized"}, 401

        filepath = os.path.join(dir.path, path)

        if os.path.isfile(filepath):
            os.unlink(filepath)
        else:
            return {"message": "File path not found"}, 404

        return {"message": "File deleted"}, 204


    '''Upload a file to path'''
    @ns.doc('upload_file_dir')
    @http.crossdomain(origin='*', methods=['GET', 'POST', 'DELETE', 'HEAD', 'OPTIONS'],
                      headers=['Origin', 'Content-Type', 'X-API-KEY'])
    def post(self, folder, path):
        dir = db.session.query(DocumentDirectory).filter(DocumentDirectory.codigo.ilike(folder)).one_or_none()

        if dir is None:
            return {"message": "Document directory does not exists"}, 404
        elif not os.path.isdir(dir.path):
            return {"message": "File path not found"}, 404

        if not dir.allow_upload:
            return {"message": "Forbidden"}, 403

        # Check Permissions
        if not dir.upload_anonymous:
            user = get_user(request)
            if not user:
                return {"message": "Unauthorized"}, 401

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

                    file_url = url_for('api.documents_file_dir', folder=folder,
                                       path='{}/{}'.format(path, filename) if path else filename)

                    data.append({'upload': True, 'source': file.filename, 'filename': filename, 'overwrite': overwrite,
                                 'resource_url': file_url, 'message': 'File uploaded successfully'})
                else:
                    errors = True
                    data.append({'upload': False, 'source': file.filename, 'filename': None, 'overwrite': None,
                                 'resource_url': None, 'message': 'Error uploading file'})

        return { "files": data }, 201