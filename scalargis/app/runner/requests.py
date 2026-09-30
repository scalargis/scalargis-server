"""Capture a web request into a job payload and rebuild it inside the job, so a handler that reads flask.request runs unchanged."""
from flask import current_app, g
from werkzeug.datastructures import MultiDict

from app.database import db

REQUEST_KEY = 'request'


def capture_request(req):
    """The url root, path, method, args, form, JSON body, client address and user agent of req."""
    captured = {
        'url_root': req.url_root,
        'path': req.path,
        'method': req.method,
        'args': [[k, v] for k, v in req.args.items(multi=True)],
        'form': [[k, v] for k, v in req.form.items(multi=True)],
        'remote_addr': req.remote_addr,
        'user_agent': req.headers.get('User-Agent'),
    }
    body = req.get_json(silent=True) if req.is_json else None
    if body is not None:
        captured['json'] = body
    return captured


def job_user(user_id):
    """The user with user_id, or None."""
    if user_id is None:
        return None
    from app.models.security import User
    return db.session.get(User, user_id)


def replay_request(captured, user=None):
    """A request context built from a captured request. current_user is user when one is given."""
    options = {
        'base_url': captured.get('url_root') or 'http://localhost/',
        'method': captured.get('method') or 'POST',
        'query_string': MultiDict(captured.get('args') or []),
        'environ_base': {'REMOTE_ADDR': captured.get('remote_addr') or ''},
    }
    if captured.get('user_agent'):
        options['headers'] = {'User-Agent': captured['user_agent']}
    if 'json' in captured:
        options['json'] = captured['json']
    elif captured.get('form'):
        options['data'] = MultiDict(captured['form'])
    ctx = current_app.test_request_context(captured.get('path') or '/', **options)
    return _WithUser(ctx, user)


_UNSET = object()


class _WithUser(object):
    """A request context that sets the Flask-Login user on enter, with no login signal, and restores it on exit."""

    def __init__(self, ctx, user):
        self.ctx = ctx
        self.user = user
        self.saved = _UNSET

    def __enter__(self):
        self.ctx.__enter__()
        self.saved = g.pop('_login_user', _UNSET)
        if self.user is not None:
            g._login_user = self.user
        return self.ctx

    def __exit__(self, *exc):
        g.pop('_login_user', None)
        if self.saved is not _UNSET:
            g._login_user = self.saved
        return self.ctx.__exit__(*exc)


def plain_result(value):
    """The JSON body of a Flask response, or value itself."""
    if hasattr(value, 'get_json') and hasattr(value, 'status_code'):
        return value.get_json(silent=True)
    return value
