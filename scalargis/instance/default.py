# -- Turns on debugging features in Flask --
DEBUG = False

# -- SECURITY Settings --
SECRET_KEY = u'Gh\x00)\xad\x7fQx\xedvx\xfetS-\x9a\xd7\x17$\x08_5\x17F'

SECURITY_USER_IDENTITY_ATTRIBUTES = ('username', 'email')
SECURITY_PASSWORD_HASH = 'bcrypt'
SECURITY_PASSWORD_SALT = SECRET_KEY
SECURITY_TRACKABLE = True
# Avoid conflicts with client endpoints
SECURITY_URL_PREFIX = "/server"

# -- DATATABSE connection --
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:postgres@localhost:5432/scalargis"

# -- SCALARGIS settings --
SCALARGIS_DB_SCHEMA = "scalargis"

SCALARGIS_HOST_URL = ''
SCALARGIS_BASE_URL = ''

SCALARGIS_LDAP_AUTHENTICATION = False

# -- Brute-force login protection --
SCALARGIS_LOGIN_BLOCK_THRESHOLD = 20
SCALARGIS_LOGIN_BLOCK_DURATION_MINUTES = 30

# -- Rate limiting (Flask-Limiter) for auth endpoints --
SCALARGIS_RATELIMIT_LOGIN = "30/minute"
SCALARGIS_RATELIMIT_EMAIL = "5/minute;20/hour"

# -- Password complexity policy --
# Enforced whenever a password is set (register, reset, admin user create/update).
# Set any rule to False to disable it; existing passwords/logins are unaffected.
SCALARGIS_PASSWORD_MIN_LENGTH = 12
SCALARGIS_PASSWORD_REQUIRE_UPPERCASE = True
SCALARGIS_PASSWORD_REQUIRE_LOWERCASE = True
SCALARGIS_PASSWORD_REQUIRE_DIGIT = True
SCALARGIS_PASSWORD_REQUIRE_SPECIAL = True

SCALARGIS_PLUGINS = []
SCALARGIS_PLUGINS_SERVICES = []

SCALARGIS_EXTENSIONS = []
SCALARGIS_EXTENSIONS_SERVICES = []

SCALARGIS_ROUTE_GEOSERVER = []

SCALARGIS_PROXY_CORS = ['http://localhost:3000', 'http://localhost:3005']

# -- Security Response Headers --
# Set any value to '' (empty string) to suppress that header.
SCALARGIS_SECURITY_HEADERS_X_FRAME_OPTIONS = 'SAMEORIGIN'
SCALARGIS_SECURITY_HEADERS_X_CONTENT_TYPE_OPTIONS = 'nosniff'
SCALARGIS_SECURITY_HEADERS_X_XSS_PROTECTION = '0'
SCALARGIS_SECURITY_HEADERS_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SCALARGIS_SECURITY_HEADERS_CSP = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https: http:; style-src 'self' 'unsafe-inline' https: http:; img-src 'self' data: blob: https: http:; font-src 'self' data:; connect-src 'self' blob: https: http:; frame-src 'self' https: http:; frame-ancestors 'self'; object-src 'none'; base-uri 'self'; form-action 'self'"
SCALARGIS_SECURITY_HEADERS_CSP_REPORT_ONLY = False
SCALARGIS_SECURITY_HEADERS_HSTS_MAX_AGE = 31536000
SCALARGIS_SECURITY_HEADERS_HSTS_INCLUDE_SUBDOMAINS = False
SCALARGIS_SECURITY_HEADERS_HSTS_PRELOAD = False
SCALARGIS_SECURITY_HEADERS_HSTS_FORCE = False
# Cross-origin framing: clickjacking protection is ON for all routes by default.
# To let specific routes be embedded (iframed) by other sites, list their path
# prefixes here and set the allowed parents below. Empty = no embedding.
# Example for an embedded-map deployment:
#   SCALARGIS_SECURITY_HEADERS_EMBED_PATHS = ['/embedded', '/sso', '/map', '/mapa']
#   SCALARGIS_SECURITY_HEADERS_EMBED_FRAME_ANCESTORS = '*'   # or "'self' https://parent.example"
SCALARGIS_SECURITY_HEADERS_EMBED_PATHS = []
SCALARGIS_SECURITY_HEADERS_EMBED_FRAME_ANCESTORS = '*'

# -- Session / remember-cookie hardening (CSRF defence-in-depth, H1) --
# SameSite=Lax stops the browser sending these cookies on cross-site POST/PUT/DELETE,
# which closes the file-upload/delete session-CSRF vector. The JSON API is header-auth
# (X-API-KEY, no cookies) so it is unaffected; /server/login already carries a FlaskForm
# CSRF token. SameSite/HttpOnly/Secure are applied unconditionally from config (independent
# of request scheme), so they work behind a TLS-terminating reverse proxy. Secure stays
# False here for local HTTP dev -- production config must override it to True.
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True       # already Flask's default; set explicitly
SESSION_COOKIE_SECURE = False        # prod per-box config -> True (HTTPS only)
REMEMBER_COOKIE_SAMESITE = 'Lax'
REMEMBER_COOKIE_HTTPONLY = True
REMEMBER_COOKIE_SECURE = False       # prod per-box config -> True
