import pytest
from flask import Flask

from app.utils import wms
from app.utils.http import replace_geoserver_url


GS = 'http://geoserver:8080/geoserver/'


def rewrite(routes, url):
    app = Flask(__name__)
    app.config['SCALARGIS_ROUTE_GEOSERVER'] = routes
    with app.app_context():
        return replace_geoserver_url(url)


@pytest.mark.parametrize('routes', [[], None])
def test_no_routes_keeps_the_url(routes):
    assert rewrite(routes, '/geoserver/ws/wms?') == '/geoserver/ws/wms?'


def test_flat_start_rule_replaces_a_prefix():
    assert rewrite(['/geoserver/', GS, 'start'], '/geoserver/ws/wms?') == GS + 'ws/wms?'


def test_flat_start_rule_skips_a_url_with_no_prefix():
    url = 'https://maps.example.org/geoserver/ws/wms?'
    assert rewrite(['/geoserver/', GS, 'start'], url) == url


def test_list_start_rule_skips_a_url_with_no_prefix():
    url = 'https://maps.example.org/geoserver/ws/wms?'
    assert rewrite([['/geoserver/', GS, 'start']], url) == url


@pytest.mark.parametrize('routes', [
    ['/geoserver/', GS, 'start'],
    [['/geoserver/', GS, 'start']],
])
def test_start_rule_replaces_only_the_prefix(routes):
    url = '/geoserver/ws/wms?viewparams=path:/geoserver/x'
    assert rewrite(routes, url) == GS + 'ws/wms?viewparams=path:/geoserver/x'


@pytest.mark.parametrize('routes', [
    ['https://maps.example.org/geoserver/', GS],
    [['https://maps.example.org/geoserver/', GS]],
    [['https://maps.example.org/geoserver/', GS, 'other']],
])
def test_rule_with_no_start_replaces_every_match(routes):
    url = 'x=https://maps.example.org/geoserver/&y=https://maps.example.org/geoserver/'
    assert rewrite(routes, url) == 'x={0}&y={0}'.format(GS)


def test_rules_run_in_order():
    routes = [
        ['/geoserver/', GS, 'start'],
        ['https://maps.example.org/geoserver/', GS],
        ['/geoserver_other/', 'http://10.0.0.1/geoserver/', 'start'],
    ]
    assert rewrite(routes, '/geoserver/ws/wms?') == GS + 'ws/wms?'
    assert rewrite(routes, 'https://maps.example.org/geoserver/ws/wms?') == GS + 'ws/wms?'
    assert rewrite(routes, '/geoserver_other/ws/wms?') == 'http://10.0.0.1/geoserver/ws/wms?'


def test_wms_uses_the_same_rewrite():
    assert wms.replace_geoserver_url is replace_geoserver_url
