"""gunicorn settings from the same env vars the Waitress server reads."""
import os


def _int(name, default):
    """Read an int env var, with a default for an empty or absent value."""
    value = os.environ.get(name)
    return int(value) if value else default


wsgi_app = 'wsgi:app'
chdir = os.path.dirname(os.path.abspath(__file__))
bind = '0.0.0.0:{}'.format(_int('PORT', 5000))
worker_class = 'gthread'
workers = _int('WORKERS', 2)
threads = _int('THREADS', 6)
worker_connections = _int('CONNECTION_LIMIT', 100)
timeout = _int('WORKER_TIMEOUT', 120)
graceful_timeout = _int('GRACEFUL_TIMEOUT', 30)
keepalive = _int('KEEPALIVE', 75)
max_requests = _int('MAX_REQUESTS', 0)
max_requests_jitter = _int('MAX_REQUESTS_JITTER', 0)
preload_app = False
forwarded_allow_ips = os.environ.get('TRUSTED_PROXY') or '127.0.0.1'
accesslog = None
errorlog = '-'
loglevel = os.environ.get('GUNICORN_LOG_LEVEL') or 'info'
