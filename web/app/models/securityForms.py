# -*- coding: utf-8 -*-
"""
    app.models.securityForm
    ~~~~~~~~~~~~~~~~~~~~
    Security module
    :copyright: (c) 2017 by WKT-SI.
    :license: XXX see LICENSE for more details.
"""
from flask import current_app
from flask_security import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm, ConfirmRegisterForm
from flask_security.utils import get_message, config_value, verify_and_update_password, hash_password
from flask_security.confirmable import requires_confirmation
from flask_wtf import FlaskForm as Form
from werkzeug.local import LocalProxy
from wtforms import StringField, IntegerField, FieldList, BooleanField, PasswordField, DateTimeField
from wtforms.validators import InputRequired, DataRequired, Regexp
from wtforms.widgets import HiddenInput
from app.database import db
from app.utils.security import authenticate_ldap_user
from app.utils import constants
from .security import User

# Reference for flask-security datastore
_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


class ExtendedRegisterForm(RegisterForm):
    """
        Overrides flask_security RegisterForm Class
    """
    username = StringField('Username', [DataRequired(message='Username não preenchido'),
                                        Regexp('[a-z0-9_-]{4,20}$', message='Formato da password errado')])

    def validate(self, **kwargs):
        # check for username
        if db.session.quer(User).filter(User.username == self.username.data.strip()).first():
            # append the error message
            self.username.errors.append("O Username já existe")
            return False

        # now check for Flask-Security validate functions
        if not super(ExtendedRegisterForm, self).validate():
            return False

        return True


class ExtendedLoginForm(LoginForm):
    """
        Overrides flask_security LoginForm Class
    """
    email = StringField('Username ou Email', [InputRequired()])
    remember = BooleanField('Memorizar')

    # email = StringField('Email', [InputRequired()])

    def __init__(self, *args, **kwargs):
        super(ExtendedLoginForm, self).__init__(*args, **kwargs)
        self.user = None
        self.email.label.text = config_value("APP_USERNAME_LABEL") or self.email.label.text
        self.password.label.text = config_value("APP_PASSWORD_LABEL") or self.password.label.text
        self.remember.label.text = config_value("APP_REMEMBER_LABEL") or self.remember.label.text

    def validate(self):
        if not Form.validate(self):
            return False

        if self.email.data.strip() == '':
            self.email.errors.append(get_message('EMAIL_NOT_PROVIDED')[0])
            return False

        if self.password.data.strip() == '':
            self.password.errors.append(get_message('PASSWORD_NOT_PROVIDED')[0])
            return False

        self.user = _datastore.get_user(self.email.data)

        if self.user is None:
            self.email.errors.append(get_message('USER_DOES_NOT_EXIST')[0])
            return False
        if not self.user.password:
            self.password.errors.append(get_message('PASSWORD_NOT_SET')[0])
            return False
        # Tries to authenticate user on LDAP before database
        if authenticate_ldap_user(self.email.data, self.password.data, None):
            # If user authenticated, updates password stored on database
            self.user.password = hash_password(self.password.data)
            _datastore.put(self.user)
        else:
            if not verify_and_update_password(self.password.data, self.user):
                self.password.errors.append(get_message('INVALID_PASSWORD')[0])
                return False

        if requires_confirmation(self.user):
            self.email.errors.append(get_message('CONFIRMATION_REQUIRED')[0])
            return False
        if not self.user.is_active:
            self.email.errors.append(get_message('DISABLED_ACCOUNT')[0])
            return False

        return True


class ExtendedForgotPasswordForm(ForgotPasswordForm):
    """The default forgot password form"""

    def __init__(self, *args, **kwargs):
        super(ExtendedForgotPasswordForm, self).__init__(*args, **kwargs)
        self.email.label.text = 'Email'  # config_value("APP_EMAIL_LABEL") or self.email.label.text
        self.submit.label.text = 'Enviar'  # config_value("APP_USERNAME_LABEL") or self.email.label.text


class ExtendedResetPasswordForm(ResetPasswordForm):
    """The default reset password form"""

    def __init__(self, *args, **kwargs):
        super(ExtendedResetPasswordForm, self).__init__(*args, **kwargs)
        self.submit.label.text = 'Aceitar'  # config_value("APP_USERNAME_LABEL") or self.email.label.text
        self.password_confirm.label.text = 'Confirmar password'


class ExtendedConfirmRegisterForm(ConfirmRegisterForm):
    username = StringField('Username', [DataRequired(message='Username não preenchido')])

    def __init__(self, *args, **kwargs):
        super(ExtendedConfirmRegisterForm, self).__init__(*args, **kwargs)
        self.email.label.text = 'Email'
        self.submit.label.text = 'Registar'  # config_value("APP_USERNAME_LABEL") or self.email.label.text

    def validate(self, **kwargs):
        success = True
        if not super(ConfirmRegisterForm, self).validate():
            success = False
        if db.session.query(User).filter(User.username == self.username.data.strip()).first():
            self.username.errors.append("O Username já existe")
            success = False
        return success


class UserSearchForm(Form):
    id = StringField('Id')
    username = StringField('Username')
    email = StringField('Email')
    name = StringField('Nome')
    active = IntegerField('Activo')
    role = StringField('Grupo')
    page = IntegerField('Página', widget=HiddenInput())
    orderField = StringField('Campo de Ordenação')
    sortOrder = StringField('Direcção da Ordenação')


class UserForm(Form):
    username = StringField('Username', [DataRequired(message=constants.VALIDATOR_REQUIRED_FIELD)])
    email = StringField('Email', [DataRequired(message=constants.VALIDATOR_REQUIRED_FIELD)])
    first_name = StringField('Primeiro Nome')
    last_name = StringField('Último Nome')
    name = StringField('Nome')
    active = BooleanField('Activo')
    password = PasswordField('Password')
    confirmedAt = DateTimeField('Data de Confirmação')
    RolesList = FieldList(StringField('RolesList'))
    defaultMap = StringField('Mapa')


class RoleSearchForm(Form):
    id = StringField('Id')
    name = StringField('Nome')
    page = IntegerField('Página', widget=HiddenInput())
    orderField = StringField('Campo de Ordenação')
    sortOrder = StringField('Direcção da Ordenação')


class RoleForm(Form):
    name = StringField('Email', [DataRequired(message=constants.VALIDATOR_REQUIRED_FIELD)])
    UsersList = FieldList(StringField('UsersList'))
