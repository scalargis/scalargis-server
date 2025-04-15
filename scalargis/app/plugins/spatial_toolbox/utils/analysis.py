import os
import json
from collections import OrderedDict
import uuid
from flask import redirect, url_for, send_file, make_response
from sqlalchemy import text
from pyexcel_xls import save_data as save_xls
from pyexcel_io import save_data as save_csv

from app.database import db
from app.database.schema import db_schema
from instance import settings


def get_intersect_results(config_code, geom_wkt, geom_srid, buffer, buffer_srid, out_srid):

    iewkt = "SRID={0};{1}".format(geom_srid or 4326, geom_wkt)
    outsrid = out_srid or 4326
    ibuffer = buffer or 0
    ibuffer_srid = buffer_srid or 3857

    print(db_schema)

    # get layers def
    sql = "select * from {0}.site_settings where code like '{1}'".format(db_schema, config_code or 'config_intersect')
    result = db.session.execute(text(sql)).fetchall()
    layers = []
    if len(result) > 0:
        layers = result[0].setting_value

    # parse confrontation config to json object
    json_cfg = json.loads(layers)

    sql = "select * from {0}.intersects_layers(:layers, :ewkt, :outsrid, :buffer, :buffer_srid)".format(db_schema)
    params = {"layers": layers, "ewkt": iewkt, "outsrid": outsrid, "buffer": ibuffer, "buffer_srid": ibuffer_srid}
    result = db.session.execute(text(sql), params).fetchall()
    record = None
    if len(result) > 0:
        record = result[0].intersects_layers

    # Filter empty layers
    record_filtered = OrderedDict()
    record_filtered['layers'] = []
    record_filtered['output_geom'] = record['output_geom']

    for row in record['layers']:
        if len(row['results']):
            record_filtered['layers'].append(row)

    if 'description' in json_cfg:
        record_filtered['description'] = json_cfg['description']

    return record_filtered


def export_intersect_results(record, out_format):

    # Build tabular data
    data = OrderedDict()

    if 'description' in record:
        data['Descricao'] = []
        data['Descricao'].append([record['description']])

    data['Resultados'] = []
    data['Resultados'].append(['Grupo', 'Título', 'Área', '%', 'Campos'])
    for row in record['layers']:
        records = []
        group = row['title_alias'].replace(" ", "") if row.get('title_alias') else row['title'].replace(" ", "")
        column_names = ['Grupo', 'Título']
        column_names.append('Área')
        column_names.append('%')

        for field in row['fields']:
            column_names.append(field['alias'])

        records.append(column_names)

        for item in row['results']:
            l = []
            l.append(row['group'])
            l.append(row['title'])
            l.append(round(item['area'], 3))
            l.append(round(item['percent'], 3))
            for field in row['fields']:
                l.append(item[field['field']])
            records.append(l)

            # Build main result
            rl = []
            rl.append(row['group'])
            rl.append(row['title'])
            rl.append(round(item['area'], 3))
            rl.append(round(item['percent'], 3))

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
    file_name = "intersect_layers"

    # Send XLS file
    if out_format == 'xls':
        outfile = file_name + ".xls"
        file_name = "{0}-{1}.{2}".format(file_name, uuid.uuid4(), out_format)
        filename = os.path.join(settings.APP_TMP_DIR, file_name)
        if os.path.exists(filename):
            os.remove(filename)
        save_xls(filename, data)
        return send_file(filename, download_name=outfile)
    # Send CSV file
    else:
        outfile = file_name + ".zip"
        filename = os.path.join(settings.APP_TMP_DIR, file_name + ".csvz")
        if os.path.exists(filename):
            os.remove(filename)
        save_csv(filename, data)
        if os.path.exists(os.path.join(settings.APP_TMP_DIR, outfile)):
            os.remove(os.path.join(settings.APP_TMP_DIR, outfile))

        return send_file(filename, download_name=outfile)
