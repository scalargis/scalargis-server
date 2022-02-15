import os

_basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = False
BUNDLE_FILES = False

#PROXY='/requests/proxy'

SECRET_KEY = u'Gh\x00)\xad\x7fQx\xedvx\xfetS-\x9a\xd7\x17$\x08_5\x17F'

SECURITY_USER_IDENTITY_ATTRIBUTES = ('username', 'email')
SECURITY_PASSWORD_HASH = 'bcrypt'
SECURITY_PASSWORD_SALT = SECRET_KEY
SECURITY_TRACKABLE = True
#SECURITY_UNAUTHORIZED_VIEW = '/unauthorized'
SECURITY_MSG_INVALID_PASSWORD = ("Utilizador ou password errados", "error")
SECURITY_MSG_PASSWORD_NOT_PROVIDED = ("Deverá indicar a password", "error")
SECURITY_MSG_RETYPE_PASSWORD_MISMATCH = ("As passwords não são iguais", "error")
SECURITY_MSG_PASSWORD_INVALID_LENGTH = ("A password deverá ter no mínimo 6 caracteres", "error")
SECURITY_MSG_USER_DOES_NOT_EXIST = ("Utilizador ou password errados", "error")
SECURITY_MSG_PASSWORD_RESET_REQUEST = ("As intruções para definição da nova password foram enviadas para %(email)s.", "info")
#Registration and Recover Password configuration
#SECURITY_RECOVERABLE = True
#SECURITY_CONFIRMABLE = True
#SECURITY_REGISTERABLE = True
#SECURITY_POST_REGISTER_VIEW = "/login"
#SECURITY_EMAIL_SUBJECT_PASSWORD_RESET = "Recuperação de password"
#SECURITY_EMAIL_SUBJECT_PASSWORD_NOTICE = "Alteração de password"
#SECURITY_EMAIL_SUBJECT_PASSWORD_CHANGE_NOTICE = "Alteração de password"
#SECURITY_EMAIL_SUBJECT_REGISTER = "Registo de utilizador"
#SECURITY_MSG_USER_DOES_NOT_EXIST = ("O utilizador não existe.", "error")
#SECURITY_MSG_CONFIRMATION_REQUIRED = ("O email ainda não foi confirmado", "error")
#SECURITY_MSG_CONFIRM_REGISTRATION = ("Obrigado. As instruções para confirmação do registo foram enviadas para o email %(email)s.", "success")
#SECURITY_MSG_EMAIL_ALREADY_ASSOCIATED = ("O email %(email)s já está associado a uma conta.", "error")
#SECURITY_EMAIL_SENDER = 'no-reply <no-reply@wkt.pt>'

#Flask-Mail
#MAIL_SERVER = 'mail.wkt.pt'
#MAIL_PORT = 25
#MAIL_USE_SSL = False
#MAIL_USERNAME = '<email>'
#MAIL_PASSWORD = '<password>'


BCRYPT_LEVEL = 12  # Configuration for the Flask-Bcrypt extension
MAIL_FROM_EMAIL = "name@example.com"  # For use in application emails

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:password@localhost:5432/teste_migrate"

WTF_CSRF_SECRET_KEY = 'a random string'
WTF_CSRF_ENABLED = False

# -*- coding: utf-8 -*-
# ...
# available languages
LANGUAGES = {
    'en': 'English',
    'pt': 'Portugues'
}
BABEL_DEFAULT_LOCALE = 'pt'

#-- DEFAULT APPLICATION HOMEPAGE --
#DEFAULT_APP_PAGE = "home"
#DEFAULT_APP_PAGE = "map"
#DEFAULT_APP_PAGE = "map.index"

LDAP_AUTHENTICATION = False

# acesso interno ao geoserver quando acesso fechado pelo Apache (proxy)
# From > To
# ROUTE_GEOSERVER = ['mapas.wkt.pt','10.88.1.19:8080']

#-- Path to PROJ and GDGAL DATA dirs
#PROJ_LIB_PATH = ''
#GDAL_DATA_PATH = ''

PLUGINS = []

# Emails Notification Configuration
SMTP_SERVER = ''
SMTP_PORT = ''
USE_SSL_EMAIL = False
SMTP_USERNAME = ''
SMTP_PASSWORD = ''
SENDER_EMAIL = ''
SEND_EMAIL_NOTIFICATIONS = False
EMAIL_NOTIFICATION = ''

#EMAIL Settings
'''
SMTP_SERVER = 'mail.wkt.pt'
SMTP_PORT = '25'
USE_SSL_EMAIL = False
SMTP_USERNAME = 'noreply@wkt.pt'
SMTP_PASSWORD = 'password'
SENDER_EMAIL = 'no-reply <noreply@wkt.pt>'
SEND_EMAIL_NOTIFICATIONS_USER = True
SEND_EMAIL_NOTIFICATIONS_ADMIN = True
EMAIL_NOTIFICATIONS_ADMIN = ['dev@wkt.pt']
'''

#Cookie Consent
'''
COOKIE_CONSENT = True
COOKIE_CONSENT_TEMPLATE = '_cookie_warning.html'
COOKIE_CONSENT_NAME = 'idealg-cookie-agreed'
COOKIE_CONSENT_VALUE = '2'
COOKIE_CONSENT_PATH = '/'
COOKIE_CONSENT_MSG_ALERT = 'Este website utiliza cookies para melhorar a sua experiência de utilização'
COOKIE_CONSENT_MSG_DESCRIPTION = 'Ao clicar em qualquer link presente nesta página está a consentir a sua utilização.'
COOKIE_CONSENT_INFO_URL = 'http://ec.europa.eu/ipg/basics/legal/cookies/index_en.htm'
COOKIE_CONSENT_INFO_LABEL = 'Mais Informação'
COOKIE_CONSENT_BTN_ACCEPT_LABEL = 'Sim, concordo'
COOKIE_CONSENT_CLASS = 'cc-floating cc-type-info cc-theme-block cc-bottom cc-right'
'''

del os