import urllib
import flask

# NOTE: jinja2 3.1.0 dropped contextfilter in favour of pass_context.
try:
    from jinja2 import pass_context
except ImportError:
    from jinja2 import contextfilter as pass_context


mod = flask.Blueprint('filters', __name__)

@pass_context
@mod.app_template_filter()
def datetimefilter(context, value, format='%d/%m/%Y %H:%M'):
    """convert a datetime to a different format."""
    if value is None:
        return None
    else:
        return value.strftime(format)


@pass_context
@mod.app_template_filter()
def urlencode(context, uri, **query):
    parts = list(urllib.parse.urlparse(uri))
    q = urllib.parse.parse_qs(parts[4])
    q.update(query)
    parts[4] = urllib.parse.urlencode(q)
    return urllib.parse.urlunparse(parts)