# -- Turns on debugging features in Flask --
DEBUG = True

# -- SECURITY Settings --
SECRET_KEY = u'Gh\x00)\xad\x7fQx\xedvx\xfetS-\x9a\xd7\x17$\x08_5\x17F'

SECURITY_USER_IDENTITY_ATTRIBUTES = ('username', 'email')
SECURITY_PASSWORD_HASH = 'bcrypt'
SECURITY_PASSWORD_SALT = SECRET_KEY
SECURITY_TRACKABLE = True

# -- DATATABSE connection --
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://scalargis:scalargis@db:5432/scalargis"

# -- SCALARGIS settings --
SCALARGIS_HOST_URL = ''
SCALARGIS_BASE_URL = ''

SCALARGIS_LDAP_AUTHENTICATION = False

SCALARGIS_PLUGINS = ['proxy']

SCALARGIS_PLUGINS_SERVICES = []

SCALARGIS_ROUTE_GEOSERVER = []

SCALARGIS_DB_SCHEMA = 'portal'
