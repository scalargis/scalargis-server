import urllib
import jinja2
import flask


mod = flask.Blueprint('filters', __name__)

@jinja2.contextfilter
@mod.app_template_filter()
def datetimefilter(context, value, format='%d/%m/%Y %H:%M'):
    """convert a datetime to a different format."""
    if value is None:
        return None
    else:
        return value.strftime(format)


@jinja2.contextfilter
@mod.app_template_filter()
def urlencode(context, uri, **query):
    parts = list(urllib.parse.urlparse(uri))
    q = urllib.parse.parse_qs(parts[4])
    q.update(query)
    parts[4] = urllib.parse.urlencode(q)
    return urllib.parse.urlunparse(parts)