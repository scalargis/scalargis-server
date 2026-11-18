import json
import logging
import os
import re
import unicodedata
from collections import Counter

import sqlalchemy
from flask import request
from flask_restx import abort
from sqlalchemy import cast, or_
from sqlalchemy.exc import IntegrityError

from app.database import db
from app.models.portal import SharedLayer, Viewer
from app.utils import utc_now, iso_utc
from ..parsers import parser_records_with_page
from ...endpoints import get_user
from . import history


logger = logging.getLogger(__name__)

ENTITY = 'shared_layer'

CODE_PATTERN = re.compile(r'^[a-z0-9-]+$')

SORT_FIELDS = ('id', 'code', 'title', 'updated_at')


def _layer(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            abort(400, 'layer_json is not valid JSON', error='invalid_layer')
    if not isinstance(value, dict):
        abort(400, 'layer_json must be an object', error='invalid_layer')
    layer_type = value.get('type')
    if not isinstance(layer_type, str) or not layer_type.strip():
        abort(400, 'layer_json must have a type', error='invalid_layer')
    if 'id' in value:
        abort(400, 'layer_json must not have an id', error='invalid_layer')
    if layer_type.strip().upper() == 'GROUP':
        abort(400, 'A shared layer cannot be a GROUP', error='group_layer')
    return value


def _code(value):
    if not isinstance(value, str) or not CODE_PATTERN.match(value):
        abort(400, 'code must match ^[a-z0-9-]+$', error='invalid_code')
    return value


def _code_free(code, record_id=None):
    qy = SharedLayer.query.filter(SharedLayer.code == code)
    if record_id is not None:
        qy = qy.filter(SharedLayer.id != record_id)
    if qy.first() is not None:
        abort(409, 'A shared layer with this code exists', error='duplicate_code')


def _loads(text):
    try:
        return json.loads(text) if text else None
    except ValueError:
        return None


def _pointer_codes(config_text):
    config = _loads(config_text)
    layers = config.get('layers') if isinstance(config, dict) else None
    if not isinstance(layers, list):
        return set()
    return {lyr['shared'] for lyr in layers
            if isinstance(lyr, dict) and isinstance(lyr.get('shared'), str) and lyr['shared']}


def _is_pointer(layer):
    return isinstance(layer, dict) and isinstance(layer.get('shared'), str) and bool(layer['shared'])


def _pointers(config_json):
    layers = config_json.get('layers') if isinstance(config_json, dict) else None
    if not isinstance(layers, list):
        return None, set()
    return layers, {lyr['shared'] for lyr in layers if _is_pointer(lyr)}


def _library(codes):
    rows = db.session.query(SharedLayer.code, SharedLayer.layer_json).filter(SharedLayer.code.in_(sorted(codes))).all()
    return {code: text for code, text in rows if isinstance(_loads(text), dict)}


def merge_shared_layers(config_json, viewer_id=None):
    """Replaces each pointer in config_json.layers with its library layer and the viewer keys on top."""
    layers, codes = _pointers(config_json)
    if not codes:
        return config_json
    library = _library(codes)
    merged = []
    dropped = set()
    for lyr in layers:
        if not _is_pointer(lyr):
            merged.append(lyr)
        elif lyr['shared'] in library:
            merged.append({**json.loads(library[lyr['shared']]), **lyr})
        else:
            logger.warning('Viewer %s names the shared layer code %s, which does not exist. The layer %s is dropped',
                           viewer_id, lyr['shared'], lyr.get('id'))
            dropped.add(lyr.get('id'))
    config_json['layers'] = merged
    for key in ('checked', 'opened'):
        if dropped and isinstance(config_json.get(key), list):
            config_json[key] = [i for i in config_json[key] if i not in dropped]
    return config_json


def _differs(a, b):
    return json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True)


def unmerge_shared_layers(config_json):
    """Strips each pointer in config_json.layers to id, shared, and the keys that differ from the library."""
    layers, codes = _pointers(config_json)
    if not codes:
        return config_json
    library = {code: json.loads(text) for code, text in _library(codes).items()}
    stripped = []
    for lyr in layers:
        base = library.get(lyr['shared']) if _is_pointer(lyr) else None
        if base is None:
            stripped.append(lyr)
        else:
            stripped.append({k: v for k, v in lyr.items()
                             if k in ('id', 'shared') or k not in base or _differs(base[k], v)})
    config_json['layers'] = stripped
    return config_json


def _viewers_with_pointers():
    return db.session.query(Viewer.id, Viewer.name, Viewer.title, Viewer.config_json) \
        .filter(Viewer.config_json.contains('"shared"')).order_by(Viewer.id).all()


def usage(code):
    """Returns the viewers whose config_json.layers hold a layer with shared equal to code."""
    return [{'id': v.id, 'name': v.name, 'title': v.title}
            for v in _viewers_with_pointers() if code in _pointer_codes(v.config_json)]


def usage_counts():
    """Returns a map of each code to the number of viewers that name it."""
    counts = {}
    for v in _viewers_with_pointers():
        for code in _pointer_codes(v.config_json):
            counts[code] = counts.get(code, 0) + 1
    return counts


def _type_of(record):
    layer = _loads(record.layer_json)
    return layer.get('type') if isinstance(layer, dict) else None


def to_dict(record, with_layer=True):
    """Returns the API form of a library row."""
    data = {'id': record.id, 'code': record.code, 'title': record.title, 'type': _type_of(record),
            'updated_at': iso_utc(record.updated_at)}
    if with_layer:
        data['layer_json'] = _loads(record.layer_json)
    return data


def get_by_filter(req):
    """Returns a page of library rows with the type and the usage count of each row."""
    args = parser_records_with_page.parse_args(req)
    page = args.get('page') or 1
    per_page = args.get('per_page') or 10
    try:
        filters = json.loads(args.get('filter') or '{}')
        sort = json.loads(args.get('sort') or '[]')
    except ValueError:
        abort(400, 'filter and sort must be JSON', error='invalid_filter')

    qy = SharedLayer.query
    for key, value in (filters.items() if isinstance(filters, dict) else []):
        if key == 'id':
            ids = value if isinstance(value, list) else [value]
            qy = qy.filter(SharedLayer.id.in_([int(i) for i in ids]))
        elif key in ('code', 'title'):
            qy = qy.filter(cast(getattr(SharedLayer, key), sqlalchemy.String).ilike('%' + str(value) + '%'))
        elif key == 'q':
            text = '%' + str(value) + '%'
            qy = qy.filter(or_(SharedLayer.code.ilike(text), SharedLayer.title.ilike(text)))

    ordered = False
    if isinstance(sort, list):
        for i in range(0, len(sort) - 1, 2):
            if sort[i] in SORT_FIELDS and str(sort[i + 1]).lower() in ('asc', 'desc'):
                qy = qy.order_by(getattr(getattr(SharedLayer, sort[i]), str(sort[i + 1]).lower())())
                ordered = True
    if not ordered:
        qy = qy.order_by(SharedLayer.code.asc())

    result = qy.paginate(page=page, per_page=per_page, error_out=False)
    counts = usage_counts()
    items = []
    for record in result.items:
        item = to_dict(record, with_layer=False)
        item['usage_count'] = counts.get(record.code, 0)
        items.append(item)
    return {'page': result.page, 'pages': result.pages, 'per_page': result.per_page, 'total': result.total,
            'items': items}


def get_by_id(record_id):
    return SharedLayer.query.filter(SharedLayer.id == record_id).one_or_none()


def _commit():
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(409, 'A shared layer with this code exists', error='duplicate_code')


def create(data):
    """Creates a library row after the code and layer checks."""
    if not isinstance(data, dict):
        abort(400, 'The body must be an object')
    user = get_user(request)
    code = _code(data.get('code'))
    layer = _layer(data.get('layer_json'))
    _code_free(code)
    record = SharedLayer(code=code, title=data.get('title') or layer.get('title'),
                         layer_json=json.dumps(layer, ensure_ascii=False),
                         id_user_create=user.id if user else None, created_at=utc_now())
    db.session.add(record)
    _commit()
    db.session.refresh(record)
    return record


def update(record_id, data):
    """Updates a library row and keeps a history row of the state before. None when the row does not exist."""
    if not isinstance(data, dict):
        abort(400, 'The body must be an object')
    record = get_by_id(record_id)
    if record is None:
        return None
    user = get_user(request)
    history.check_stale(record, data)
    before = history.snapshot(ENTITY, record)

    if 'code' in data:
        code = _code(data.get('code'))
        if code != record.code:
            _code_free(code, record.id)
            used = usage(record.code)
            if used:
                abort(409, 'The code is in use by viewers', error='in_use', viewers=used)
            record.code = code
    if 'layer_json' in data:
        record.layer_json = json.dumps(_layer(data.get('layer_json')), ensure_ascii=False)
    if 'title' in data:
        record.title = data.get('title') or None

    record.id_user_update = user.id if user else None
    record.updated_at = utc_now()
    history.keep(ENTITY, record, before, history.ORIGIN_BACKOFFICE, user)
    _commit()
    db.session.refresh(record)
    return record


def delete(record_id):
    """Deletes a library row and its history rows. Aborts with 409 when a viewer names it."""
    record = get_by_id(record_id)
    if record is None:
        return False
    used = usage(record.code)
    if used:
        abort(409, 'The shared layer is in use by viewers', error='in_use', viewers=used)
    history.forget(ENTITY, [record.id])
    db.session.delete(record)
    db.session.commit()
    return True


MATCH_KEYS = ('type', 'url', 'layers', 'wms_style')

CONVERT_ORIGIN = 'comando'

DIFF_LIMIT = 20


def _match_key(layer):
    return json.dumps([json.dumps(layer[k], sort_keys=True) if k in layer else None for k in MATCH_KEYS])


def _match_dict(layer):
    return {k: layer[k] for k in MATCH_KEYS if k in layer}


def _is_copy(layer):
    return isinstance(layer, dict) and 'shared' not in layer and layer.get('id') is not None \
        and isinstance(layer.get('type'), str) and layer['type'].strip().upper() != 'GROUP' \
        and isinstance(layer.get('url'), str) and bool(layer['url'].strip())


def _slug(text):
    text = unicodedata.normalize('NFKD', str(text or '')).encode('ascii', 'ignore').decode('ascii').lower()
    return re.sub(r'[^a-z0-9]+', '-', text)[:60].strip('-')


def _new_code(layer, title, taken):
    base = _slug(layer.get('layers')) or _slug(title) or _slug(layer.get('type')) or 'layer'
    code, n = base, 2
    while code in taken:
        code, n = '%s-%d' % (base, n), n + 1
    taken.add(code)
    return code


def _common_layer(copies):
    first = copies[0]
    layer = {k: v for k, v in first.items()
             if k not in ('id', 'shared') and all(k in c and not _differs(c[k], v) for c in copies[1:])}
    titles = [c['title'] for c in copies if 'title' in c]
    title = None
    if titles:
        title = json.loads(Counter(json.dumps(t, sort_keys=True) for t in titles).most_common(1)[0][0])
    if len(titles) == len(copies):
        layer['title'] = title
    return layer, title


def _pointer(layer, code, base):
    pointer = {'id': layer['id'], 'shared': code}
    for k, v in layer.items():
        if k not in ('id', 'shared') and (k not in base or _differs(base[k], v)):
            pointer[k] = v
    return pointer


def _scope(viewer_ids, lock):
    qy = Viewer.query
    if viewer_ids:
        qy = qy.filter(Viewer.id.in_(list(viewer_ids)))
    if lock:
        qy = qy.with_for_update()
    return qy.order_by(Viewer.id).all()


def _plan(records, min_viewers):
    configs = {}
    groups = {}
    skipped = []
    for record in records:
        config = _loads(record.config_json)
        layers = config.get('layers') if isinstance(config, dict) else None
        if not isinstance(layers, list):
            skipped.append(record.id)
            continue
        configs[record.id] = config
        for index, lyr in enumerate(layers):
            if _is_copy(lyr):
                groups.setdefault(_match_key(lyr), []).append((record.id, index, lyr))

    existing = {}
    for row in SharedLayer.query.order_by(SharedLayer.id).all():
        layer = _loads(row.layer_json)
        if isinstance(layer, dict):
            existing.setdefault(_match_key(layer), (row, layer))
    taken = {code for (code,) in db.session.query(SharedLayer.code).all()}

    library = []
    changes = {}
    for key in sorted(groups):
        members = groups[key]
        if len({vid for vid, _, _ in members}) < min_viewers:
            continue
        if key in existing:
            row, base = existing[key]
            members = [m for m in members if all(k in m[2] for k in base)]
            if not members:
                continue
            entry = {'code': row.code, 'title': row.title, 'layer_json': base, 'reused': True, 'id': row.id}
        else:
            base, title = _common_layer([m[2] for m in members])
            code = _new_code(base, title, taken)
            entry = {'code': code, 'title': title if isinstance(title, str) and title else code,
                     'layer_json': base, 'reused': False}
        entry['match'] = _match_dict(base)
        entry['viewers'] = sorted({vid for vid, _, _ in members})
        entry['copies'] = len(members)
        library.append(entry)
        for vid, index, lyr in members:
            changes.setdefault(vid, {})[index] = (_pointer(lyr, entry['code'], base), entry['code'])

    viewers = []
    names = {r.id: r.name for r in records}
    for vid in sorted(changes):
        config = configs[vid]
        pointers = []
        for index, (pointer, code) in sorted(changes[vid].items()):
            config['layers'][index] = pointer
            pointers.append({'layer': pointer['id'], 'code': code})
        viewers.append({'id': vid, 'name': names.get(vid), 'pointers': pointers, 'config': config})
    return library, viewers, skipped


def _report(mode, min_viewers, viewer_ids, library, viewers, skipped):
    return {'command': 'convert-shared-layers', 'mode': mode, 'date': iso_utc(utc_now()),
            'min_viewers': min_viewers, 'viewer_scope': sorted(viewer_ids) if viewer_ids else None,
            'library': library, 'skipped_viewers': skipped,
            'viewers': [{k: v for k, v in item.items() if k != 'config'} for item in viewers]}


def plan_conversion(min_viewers=2, viewer_ids=None):
    """Returns the report of a dry run: the library layers to make or reuse and the pointers of each viewer."""
    library, viewers, skipped = _plan(_scope(viewer_ids, False), min_viewers)
    db.session.rollback()
    return _report('dry-run', min_viewers, viewer_ids, library, viewers, skipped)


def _served(record):
    from flask import current_app
    from app.utils.constants import ROLE_ADMIN
    from .app import build_viewer_config
    with current_app.test_request_context('/'):
        cfg = build_viewer_config(record, [ROLE_ADMIN], user=None)
    cfg = json.loads(json.dumps(cfg, default=str))
    cfg.pop('updated_at', None)
    return cfg


def _without_shared(cfg, pointers):
    made = {(p['layer'], p['code']) for p in pointers}
    layers = (cfg.get('config_json') or {}).get('layers')
    if isinstance(layers, list):
        for lyr in layers:
            if isinstance(lyr, dict) and (lyr.get('id'), lyr.get('shared')) in made:
                del lyr['shared']
    return cfg


def _diff(a, b, path='', out=None):
    out = [] if out is None else out
    if len(out) >= DIFF_LIMIT:
        return out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                out.append('%s/%s: %s -> %s' % (path, k, json.dumps(a.get(k), ensure_ascii=False)[:200],
                                                json.dumps(b.get(k), ensure_ascii=False)[:200]))
            else:
                _diff(a[k], b[k], '%s/%s' % (path, k), out)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            _diff(x, y, '%s/%d' % (path, i), out)
    elif _differs(a, b):
        out.append('%s: %s -> %s' % (path, json.dumps(a, ensure_ascii=False)[:200],
                                     json.dumps(b, ensure_ascii=False)[:200]))
    return out[:DIFF_LIMIT]


def conversion_summary(report):
    """Returns the text summary of a conversion report."""
    library = report.get('library') or []
    viewers = report.get('viewers') or []
    lines = ['convert-shared-layers %s, %s' % (report.get('mode'), report.get('date')),
             'min viewers: %s, viewer scope: %s' % (report.get('min_viewers'), report.get('viewer_scope') or 'all'),
             'library layers: %d (new %d, reused %d)' % (len(library), sum(1 for e in library if not e['reused']),
                                                        sum(1 for e in library if e['reused'])),
             'viewers changed: %d, pointers: %d' % (len(viewers), sum(len(v['pointers']) for v in viewers))]
    if report.get('skipped_viewers'):
        lines.append('viewers with no layers list, skipped: %s' % report['skipped_viewers'])
    for v in viewers:
        lines.append('viewer %s: %d pointers' % (v['id'], len(v['pointers'])))
    for e in library:
        lines.append('library %s (%s): %d viewers, %d copies' % (e['code'], 'reused' if e['reused'] else 'new',
                                                                len(e['viewers']), e['copies']))
    if 'differences' in report:
        lines.append('compare: %d differences' % len(report['differences']))
        for d in report['differences']:
            lines.append('viewer %s: %s' % (d['id'], '; '.join(d['paths'])))
    return '\n'.join(lines) + '\n'


def write_report(report, path):
    """Writes the report as JSON at path and the text summary next to it, with the extension .txt."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    with open(os.path.splitext(path)[0] + '.txt', 'w', encoding='utf-8') as f:
        f.write(conversion_summary(report))


def apply_conversion(min_viewers=2, viewer_ids=None, report_path=None):
    """Makes the library layers and the pointers in one transaction. Rolls back when a served config changes."""
    records = _scope(viewer_ids, True)
    by_id = {r.id: r for r in records}
    library, viewers, skipped = _plan(records, min_viewers)
    report = _report('apply', min_viewers, viewer_ids, library, viewers, skipped)

    before = {}
    for item in report['viewers']:
        record = by_id[item['id']]
        item['config_json_before'] = record.config_json
        before[record.id] = (_served(record), history.snapshot('viewer', record))

    for entry in library:
        if entry['reused']:
            continue
        row = SharedLayer(code=entry['code'], title=entry['title'],
                          layer_json=json.dumps(entry['layer_json'], ensure_ascii=False), created_at=utc_now())
        db.session.add(row)
        db.session.flush()
        entry['id'] = row.id

    now = utc_now()
    for item, planned in zip(report['viewers'], viewers):
        record = by_id[item['id']]
        record.config_json = json.dumps(planned['config'], ensure_ascii=False)
        record.id_user_update = None
        record.updated_at = now
        history.keep('viewer', record, before[record.id][1], CONVERT_ORIGIN, None)
        item['config_json_after'] = record.config_json

    differences = []
    for item in report['viewers']:
        after = _without_shared(_served(by_id[item['id']]), item['pointers'])
        paths = _diff(before[item['id']][0], after)
        if paths:
            differences.append({'id': item['id'], 'paths': paths})
    report['differences'] = differences

    if differences:
        db.session.rollback()
        report['mode'] = 'apply rolled back'
        for item in report['viewers']:
            item.pop('config_json_before', None)
            item.pop('config_json_after', None)
        return report
    if report_path:
        write_report(report, report_path)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        if report_path:
            os.remove(report_path)
        raise
    return report


def revert_conversion(report):
    """Puts back the viewers of an apply report and removes its new library layers that no viewer names."""
    items = report.get('viewers') or []
    records = {r.id: r for r in _scope([item['id'] for item in items], True)} if items else {}
    now = utc_now()
    restored, changed, missing = [], [], []
    for item in items:
        record = records.get(item['id'])
        if record is None:
            missing.append(item['id'])
            continue
        if record.config_json != item.get('config_json_after'):
            changed.append(item['id'])
            continue
        before = history.snapshot('viewer', record)
        record.config_json = item['config_json_before']
        record.id_user_update = None
        record.updated_at = now
        history.keep('viewer', record, before, CONVERT_ORIGIN, None)
        restored.append(item['id'])
    db.session.flush()

    removed, kept = [], []
    for entry in report.get('library') or []:
        if entry.get('reused'):
            continue
        row = SharedLayer.query.filter(SharedLayer.code == entry['code']).one_or_none()
        if row is None:
            continue
        if usage(row.code):
            kept.append(row.code)
            continue
        history.forget(ENTITY, [row.id])
        db.session.delete(row)
        removed.append(row.code)
    db.session.commit()
    return {'restored': restored, 'changed_since_apply': changed, 'missing': missing,
            'library_removed': removed, 'library_kept': kept}
