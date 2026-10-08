import glob
import json
import logging
import logging.config
import multiprocessing
import os

LOGGING_JSON = os.path.join(os.path.dirname(__file__), '..', 'instance', 'logging.json')
FILE_HANDLERS = ('info_file_handler', 'debug_file_handler', 'error_file_handler')
PROCESSES = 5
LINES = 600
MAX_BYTES = 20000


def _handler_config(path):
    """The shipped info file handler, with a small size and a temp file."""
    with open(LOGGING_JSON, 'rt') as f:
        config = json.load(f)
    handler = dict(config['handlers']['info_file_handler'])
    handler.update(filename=path, maxBytes=MAX_BYTES, backupCount=100)
    config['handlers'] = {'file': handler}
    config['root'] = {'level': 'INFO', 'handlers': ['file']}
    config['formatters']['simple']['format'] = '%(message)s'
    return config


def _write_lines(path, worker):
    """Write LINES numbered lines through the shipped handler config."""
    logging.config.dictConfig(_handler_config(path))
    log = logging.getLogger('rotation')
    for n in range(LINES):
        log.info('w%d-%04d %s', worker, n, 'x' * 60)
    logging.shutdown()


def test_file_handlers_lock_across_processes():
    with open(LOGGING_JSON, 'rt') as f:
        handlers = json.load(f)['handlers']
    for name in FILE_HANDLERS:
        assert handlers[name]['class'] == 'concurrent_log_handler.ConcurrentRotatingFileHandler'


def test_rotation_with_many_processes_keeps_every_line(tmp_path):
    path = str(tmp_path / 'arade_info.log')
    ctx = multiprocessing.get_context('spawn')
    procs = [ctx.Process(target=_write_lines, args=(path, w)) for w in range(PROCESSES)]
    for p in procs:
        p.start()
    for p in procs:
        p.join(120)
        assert p.exitcode == 0

    files = glob.glob(path + '*')
    lines = []
    for name in files:
        with open(name, 'rt', encoding='utf8') as f:
            lines.extend(f.read().splitlines())
    expected = {'w%d-%04d' % (w, n) for w in range(PROCESSES) for n in range(LINES)}
    assert len(lines) == len(expected)
    assert {line.split(' ')[0] for line in lines} == expected

    backups = [name for name in files if name != path]
    assert len(backups) >= 10
    for name in backups:
        assert os.path.getsize(name) > MAX_BYTES * 0.9
