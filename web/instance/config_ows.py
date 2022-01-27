OWS_SERVER_NAME = ''

OWS_CONFIG = [
    {
        'group': 'grupo',
        'service': 'servico',
        'type': ['WMS', 'WFS', 'WCS', 'WMTS'],
        #'type': '*',
        #'operation': ['GetCapabilities', 'GetMap', 'GetFeatureInfo', 'GetLegendGraphic'],
        'operation': '*',
        'url': 'http://www.wkt.pt/geoserver/wktapp-tests/concelhos/ows',
        'protected': True,
        'roles': ['Admin']
        #'roles': '*'
    }
]


