from os import path, environ

RECORDS_PER_PAGE = 15
LOCAL_PATH = path.dirname(path.abspath(__file__))
APP_SITE_ROOT = ''
APP_STATIC = path.join(path.dirname(LOCAL_PATH), 'app/static')
APP_RESOURCES = path.join(path.dirname(LOCAL_PATH), 'resources')
APP_TMP_DIR = path.join(path.dirname(LOCAL_PATH), 'tmp')
APP_VERSION = environ.get('WKTAPP_VERSION')

ORGANIZATION_NAME = 'WKT-SI'

MAP_TEMPLATES = [
        {"name": "full", "title": "Ecrã total", "file": "map/index.html"},
        {"name": "header", "title": "Com cabeçalho", "file": "map/index_header.html"}
        #{"name": "header", "title": "Com cabeçalho", "file": "map/index_header.html", "credits": "map/_credits.html"}
    ]

# map size for preview.
LAYOUT_MAP_SIZES_FOR_PREVIEW = [
    {"format": "A4|Retrato", "w": 180, "h": 220},
    {"format": "A4|Paisagem", "w": 250, "h": 160},
    {"format": "A3|Retrato", "w": 270, "h": 360},
    {"format": "A3|Paisagem", "w": 390, "h": 260},
    {"format": "A2|Retrato", "w": 390, "h": 530},
    {"format": "A2|Paisagem", "w": 530, "h": 390},
    {"format": "A1|Retrato", "w": 560, "h": 780},
    {"format": "A1|Paisagem", "w": 800, "h": 560},
    {"format": "A0|Retrato", "w": 750, "h": 1100},
    {"format": "A0|Paisagem", "w": 1100, "h": 750}
]

# max upload file size (KB)
UPLOAD_MAXFILESIZE = 2048
