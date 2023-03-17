from os import path, environ

LOCAL_PATH = path.dirname(path.abspath(__file__))
APP_STATIC = path.join(path.dirname(LOCAL_PATH), 'app/static')
APP_UPLOADS = path.join(path.dirname(LOCAL_PATH), 'uploads')
APP_RESOURCES = path.join(path.dirname(LOCAL_PATH), 'resources')
APP_TMP_DIR = path.join(path.dirname(LOCAL_PATH), 'tmp')

# max upload file size (KB)
UPLOAD_MAXFILESIZE = 2048
