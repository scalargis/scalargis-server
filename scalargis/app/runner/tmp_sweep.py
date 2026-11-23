"""Periodic task that deletes the old files of the tmp folder, one age limit for each kind of file."""
import logging
import os
import re
import time

from sqlalchemy import func

from .runner import _env_int, register_periodic

logger = logging.getLogger(__name__)

SWEEP_NAME = 'runner.tmp_sweep'
SWEEP_SECONDS = 3600
LAYER_CHUNK = 500

KIND_PRINT = 'print'
KIND_INTERSECT = 'intersect'
KIND_UPLOAD = 'upload'
KIND_LAYER = 'layer'

DEFAULT_HOURS = {KIND_PRINT: 168, KIND_INTERSECT: 24, KIND_UPLOAD: 24, KIND_LAYER: 24}
ENV_NAMES = {
    KIND_PRINT: 'RUNNER_TMP_PRINT_HOURS',
    KIND_INTERSECT: 'RUNNER_TMP_INTERSECT_HOURS',
    KIND_UPLOAD: 'RUNNER_TMP_UPLOAD_HOURS',
    KIND_LAYER: 'RUNNER_TMP_LAYER_HOURS',
}

_UUID = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
_PRINT = re.compile(r'^' + _UUID + r'\.pdf$', re.I)
_INTERSECT = re.compile(r'^intersect_layers-' + _UUID + r'\.[a-z0-9]+$', re.I)
_UPLOAD = re.compile(r'^(?:' + _UUID + r'|[0-9a-f]{32})\.(?!pdf$|geojson$|metadata$)[a-z0-9]+$', re.I)
_LAYER = re.compile(r'^([0-9a-f]{32})\.(?:geojson|metadata)$', re.I)


def tmp_hours():
    """Age limit in hours of each kind of file. A value of 0 turns the sweep of that kind off."""
    return {kind: max(_env_int(ENV_NAMES[kind], default), 0) for kind, default in DEFAULT_HOURS.items()}


def classify(name):
    """The kind of a file name in the tmp folder, or None for a file that the sweep never touches."""
    if _PRINT.match(name):
        return KIND_PRINT
    if _INTERSECT.match(name):
        return KIND_INTERSECT
    if _LAYER.match(name):
        return KIND_LAYER
    if _UPLOAD.match(name):
        return KIND_UPLOAD
    return None


def _layers_with_row(layer_uuids):
    """The lowercase uuids of layer_uuids that have a user_data_layer row."""
    from app.database import db
    from app.models.portal import UserDataLayer

    found = set()
    wanted = sorted(layer_uuids)
    for start in range(0, len(wanted), LAYER_CHUNK):
        chunk = wanted[start:start + LAYER_CHUNK]
        rows = db.session.query(func.lower(UserDataLayer.uuid)).filter(func.lower(UserDataLayer.uuid).in_(chunk))
        found.update(row[0] for row in rows)
    return found


def sweep_folder(folder, hours, now=None, layers_with_row=_layers_with_row):
    """Delete the files of folder that are older than the hours of their kind. Returns {kind: (files, bytes)}."""
    now = time.time() if now is None else now
    expired = {}
    layer_files = {}
    with os.scandir(folder) as entries:
        for entry in entries:
            kind = classify(entry.name)
            if kind is None or not hours.get(kind):
                continue
            try:
                if not entry.is_file(follow_symlinks=False):
                    continue
                info = entry.stat(follow_symlinks=False)
            except OSError:
                continue
            if info.st_mtime >= now - hours[kind] * 3600:
                continue
            if kind == KIND_LAYER:
                layer_files.setdefault(_LAYER.match(entry.name).group(1).lower(), []).append((entry.path, info.st_size))
            else:
                expired.setdefault(kind, []).append((entry.path, info.st_size))
    if layer_files:
        for layer_uuid in layers_with_row(layer_files):
            expired.setdefault(KIND_LAYER, []).extend(layer_files[layer_uuid])
    removed = {}
    for kind, files in expired.items():
        count = size = 0
        for path, file_size in files:
            try:
                os.remove(path)
            except FileNotFoundError:
                continue
            except OSError as err:
                logger.warning('runner: the tmp sweep could not delete %s: %s', path, err)
                continue
            count += 1
            size += file_size
        removed[kind] = (count, size)
    return removed


def sweep_tmp(wakes=None):
    """Delete the old print, export, upload, and converted layer files of APP_TMP_DIR. Returns the number of files."""
    from instance import settings

    folder = getattr(settings, 'APP_TMP_DIR', None)
    if not folder or not os.path.isdir(folder):
        return 0
    removed = sweep_folder(folder, tmp_hours())
    total = sum(count for count, _ in removed.values())
    if total:
        logger.info('runner: tmp sweep of %s removed %s', folder, ', '.join(
            '{0} {1} files ({2:.1f} MiB)'.format(count, kind, size / 1048576.0)
            for kind, (count, size) in sorted(removed.items())))
    return total


register_periodic(SWEEP_NAME, sweep_tmp, SWEEP_SECONDS)
