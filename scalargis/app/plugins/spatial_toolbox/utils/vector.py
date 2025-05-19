import logging
import os
import os.path
import json
import uuid

import fiona
from fiona import crs as fiona_crs

from instance import settings


def convert_to_geojson_create_layer(file, persist=True):
    logger = logging.getLogger(__name__)

    fiona.drvsupport.supported_drivers['LIBKML'] = 'r'
    fiona.drvsupport.supported_drivers['kml'] = 'rw'  # enable KML support which is disabled by default
    fiona.drvsupport.supported_drivers['KML'] = 'rw'  # enable KML support which is disabled by default

    metadata = {"filename": None, "size": None, "driver": None, "crs": None, "schema": None,
                'filename': file.filename}

    filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
    filepath = os.path.join(settings.APP_TMP_DIR, filename)

    file.save(filepath)

    metadata['size'] = os.stat(filepath).st_size

    # KML fix- remove a blank line at the beginning of the file if it exists
    if os.path.splitext(file.filename)[1].lower() == '.kml':
        with open(filepath, "r+", encoding="utf-8") as f:
            content = f.read().lstrip('\n')
            f.seek(0)
            f.write(content)
            f.truncate()

    #dd = open(filepath, 'rb').read()

    if os.path.splitext(file.filename)[1].lower() == '.zip':
        filepath = 'zip://' + filepath

    file_uuid = str(uuid.uuid4().hex)

    with fiona.open(filepath, 'r', encoding='utf-8') as source:
        metadata['driver'] = source.driver
        metadata['crs'] = source.meta.get('crs').get('init').upper() if 'init' in source.meta.get('crs')\
            else fiona_crs.to_string(source.meta.get('crs'))
        metadata['extent'] = source.bounds
        metadata['schema'] = source.meta.get('schema')

        out_filepath = os.path.join(settings.APP_TMP_DIR, file_uuid + '.geojson')
        with fiona.open(
                out_filepath,
                'w',
                encoding='utf-8',
                driver='GeoJSON',
                #crs=fiona.crs.from_epsg(4326),
                #crs=fiona.crs.from_epsg(3763),
                crs_wkt=source.crs_wkt,
                schema={ 'geometry': 'Unknown', 'properties': source.schema['properties']}) as sink:
            for rec in source:
                sink.write(rec)

    try:
        if os.path.exists(filepath.lstrip('zip://')):
            os.remove(filepath.lstrip('zip://'))
    except Exception as e:
        logger.debug(e)

    metadata_out_filepath = os.path.join(settings.APP_TMP_DIR, file_uuid + '.metadata')
    if metadata:
        with open(metadata_out_filepath, 'w', encoding="utf8") as metadata_outfile:
            json.dump(metadata, metadata_outfile)

    '''
    with open(out_filepath, encoding="utf8") as f:
        data = json.load(f)

        user = None
        if not current_user or not current_user.is_authenticated:
            if 'X-API-KEY' in request.headers:
                token = request.headers['X-API-KEY']
                user = get_user_from_token(token)
            else:
                user = current_user

        record = UserDataLayer()
        record.uuid = layer_uuid
        record.data_geojson = json.dumps(data)
        if metadata:
            record.metadata_geojson = json.dumps(metadata)
        record.is_private = False
        record.allow_anonymous = True
        record.is_active = True
        record.created_at = datetime.now()
        if (user and current_user.is_authenticated):
            record.id_user_create = user.id
            record.owner_id = user.id

        db.session.add(record)
        db.session.commit()
        db.session.refresh(record)
    '''

    if not persist:
        # Open and read generated geoJSON file
        with open(out_filepath, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)

        # Remove files
        try:
            if os.path.exists(out_filepath):
                os.remove(out_filepath)
        except Exception as e:
            logger.debug(e)

        try:
            if os.path.exists(metadata_out_filepath):
                os.remove(out_filepath)
        except Exception as e:
            logger.debug(e)

        return {"metadata": metadata, "data": geojson_data}


    #Build url for resource
    #url = url_for('api2.app_app_data_layer', layer_id=file_uuid)
    url = '/app/data/layer/{0}'.format(file_uuid)

    return {"uuid": file_uuid, "url": url, "metadata": metadata}