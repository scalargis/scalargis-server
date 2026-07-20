import logging
import os
import os.path
import json
import uuid
import zipfile

import fiona
from fiona import crs as fiona_crs

from instance import settings


def _enable_kml_drivers():
    fiona.drvsupport.supported_drivers['LIBKML'] = 'rw'
    fiona.drvsupport.supported_drivers['kml'] = 'rw'
    fiona.drvsupport.supported_drivers['KML'] = 'rw'


# GeoJSON attribute values are arbitrary JSON; vector formats (GML/KML/SHP) only
# hold scalar fields, so everything is written as text — a nested object (e.g.
# the drawings' `state`) would otherwise break the writer.
def _to_text(value):
    if value is None:
        return ''
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return json.dumps(value, ensure_ascii=False)


def export_geojson_to_format(geojson_data, out_format, epsg=4326):
    """Convert an in-memory GeoJSON FeatureCollection to GML, KML or a zipped
    ESRI Shapefile via fiona. Returns (filepath, download_name, mimetype).

    Shapefiles cannot hold mixed geometry types in one file, so features are
    grouped by geometry type into one .shp each and zipped together.
    """
    logger = logging.getLogger(__name__)
    _enable_kml_drivers()

    out_format = (out_format or '').lower()
    features = (geojson_data or {}).get('features', []) or []

    try:
        crs = fiona_crs.from_epsg(int(epsg))
    except Exception:
        crs = fiona_crs.from_epsg(4326)

    # Union of property keys, in first-seen order; all fields typed as str.
    prop_keys = []
    for feat in features:
        for k in (feat.get('properties') or {}).keys():
            if k not in prop_keys:
                prop_keys.append(k)
    schema_props = {k: 'str' for k in prop_keys}

    def record(feat):
        props = feat.get('properties') or {}
        return {
            'geometry': feat.get('geometry'),
            'properties': {k: _to_text(props.get(k)) for k in prop_keys},
        }

    file_uuid = uuid.uuid4().hex

    if out_format == 'gml':
        driver, ext, mimetype = 'GML', '.gml', 'application/gml+xml'
    elif out_format == 'kml':
        driver, ext, mimetype = 'KML', '.kml', 'application/vnd.google-earth.kml+xml'
    elif out_format in ('shape', 'shp', 'shapefile'):
        return _export_shapefile_zip(features, record, schema_props, crs, file_uuid)
    else:
        raise ValueError('Unsupported export format: {0}'.format(out_format))

    out_filepath = os.path.join(settings.APP_TMP_DIR, file_uuid + ext)
    schema = {'geometry': 'Unknown', 'properties': schema_props}
    with fiona.open(out_filepath, 'w', driver=driver, crs=crs, schema=schema, encoding='utf-8') as sink:
        for feat in features:
            if feat.get('geometry'):
                sink.write(record(feat))

    return out_filepath, 'export' + ext, mimetype


def _export_shapefile_zip(features, record, schema_props, crs, file_uuid):
    logger = logging.getLogger(__name__)

    # One shapefile per geometry type (SHP is single-geometry-type).
    groups = {}
    for feat in features:
        geom = feat.get('geometry') or {}
        gtype = geom.get('type')
        if not gtype:
            continue
        groups.setdefault(gtype, []).append(feat)

    work_dir = os.path.join(settings.APP_TMP_DIR, file_uuid)
    os.makedirs(work_dir, exist_ok=True)

    for gtype, feats in groups.items():
        shp_path = os.path.join(work_dir, '{0}.shp'.format(gtype.lower()))
        schema = {'geometry': gtype, 'properties': schema_props}
        with fiona.open(shp_path, 'w', driver='ESRI Shapefile', crs=crs, schema=schema,
                        encoding='utf-8') as sink:
            for feat in feats:
                sink.write(record(feat))

    zip_path = os.path.join(settings.APP_TMP_DIR, file_uuid + '.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name in os.listdir(work_dir):
            zf.write(os.path.join(work_dir, name), name)

    # The .shp/.shx/.dbf/.prj set is now inside the zip.
    for name in os.listdir(work_dir):
        try:
            os.remove(os.path.join(work_dir, name))
        except Exception as e:
            logger.debug(e)
    try:
        os.rmdir(work_dir)
    except Exception as e:
        logger.debug(e)

    return zip_path, 'export.zip', 'application/zip'


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