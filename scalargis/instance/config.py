# DEBUG = False

# -- SECURITY Settings --
# SECRET_KEY = u'Gh\x00)\xad\x7fQx\xedvx\xfetS-\x9a\xd7\x17$\x08_5\x17F'

# SECURITY_USER_IDENTITY_ATTRIBUTES = ('username', 'email')
# SECURITY_PASSWORD_HASH = 'bcrypt'
# SECURITY_PASSWORD_SALT = SECRET_KEY
# SECURITY_TRACKABLE = True

# -- DATATABSE connection --
# SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:postgres@localhost:5432/scalargis"

# -- SCALARGIS settings --
# SCALARGIS_DB_SCHEMA = "scalargis"

# SCALARGIS_HOST_URL = ''
# SCALARGIS_BASE_URL = ''

# SCALARGIS_DEFAULT_LOCALE = ''

# SCALARGIS_LDAP_AUTHENTICATION = False

# -- PLUGINS --
# SCALARGIS_PLUGINS = ['proxy', 'geonames', 'spatial_toolbox']
# SCALARGIS_PLUGINS_SERVICES = []

# -- EXTENSIONS --
# SCALARGIS_EXTENSIONS = []
# SCALARGIS_PLUGINS_EXTENSIONS = []

# -- Geoserver Url replace [[From, To], [From, To]] --
# SCALARGIS_ROUTE_GEOSERVER = []

# -- PROXY (Access-Control-Allow-Origin - CORS) --
#SCALARGIS_PROXY_CORS = ['http://localhost:3000', 'http://localhost:3005']

# -- EMAIL Settings --
# SCALARGIS_SMTP_SERVER = 'mail.wkt.pt'
# SCALARGIS_SMTP_PORT = '25'
# SCALARGIS_USE_SSL_EMAIL = False
# SCALARGIS_SMTP_USERNAME = 'noreply@wkt.pt'
# SCALARGIS_SMTP_PASSWORD = 'password'
# SCALARGIS_SENDER_USERNAME = 'noreply@wkt.pt'
# SCALARGIS_SENDER_EMAIL = 'no-reply <noreply@wkt.pt>'

# Notifications Settings
# SCALARGIS_SEND_EMAIL_NOTIFICATIONS_USER = True
# SCALARGIS_SEND_EMAIL_NOTIFICATIONS_ADMIN = True
# SCALARGIS_EMAIL_NOTIFICATIONS_ADMIN = []
# SCALARGIS_EMAIL_NOTIFICATIONS_FOLDER = 'f:\\tmp\\coscid'

# CAPTCHA Settings
# SCALARGIS_CAPTCHA_URL='https://www.google.com/recaptcha/api/siteverify'
# SCALARGIS_CAPTCHA_SITE_KEY=''
# SCALARGIS_CAPTCHA_SECRET_KEY=''

# -- DEFAULT APPLICATION HOMEPAGE --
# DEFAULT_APP_PAGE = "home"
# DEFAULT_APP_PAGE = "map"
# DEFAULT_APP_PAGE = "map.index"

# -- Path to PROJ and GDGAL DATA dirs
# PROJ_LIB_PATH = '\\venv\\Lib\\site-packages\\osgeo\\data\\proj'
# GDAL_DATA_PATH = '\\venv\\Lib\\site-packages\\osgeo\\data\\gdal'
