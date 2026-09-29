"""WSGI entry point for gunicorn. Dev keeps server.py with Waitress."""
import fcntl
import os

from app import app as flask_app
from app.main import init_wsgi
from app.utils.wsgi import with_waitress_environ

INIT_LOCK_FILE = os.environ.get('INIT_LOCK_FILE') or '/tmp/scalargis-init.lock'


def _init_once_at_a_time():
    """Run init_wsgi with the other workers of this container held back."""
    with open(INIT_LOCK_FILE, 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            init_wsgi()
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


_init_once_at_a_time()
app = with_waitress_environ(flask_app, os.environ.get('URL_PREFIX'), os.environ.get('URL_SCHEME'))
