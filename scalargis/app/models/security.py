from flask import current_app
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.local import LocalProxy
from flask_security import UserMixin, RoleMixin

from app.database import db
from app import get_db_schema
from .common import PortalTable


db_schema = get_db_schema()


roles_permissions = db.Table('roles_permissions',
                       db.Column('role_id', db.Integer(), db.ForeignKey('{schema}.role.id'.format(schema=db_schema))),
                       db.Column('permission_id', db.Integer(), db.ForeignKey('{schema}.permission.id'.format(schema=db_schema))),
                       schema=db_schema)

roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('{schema}.user.id'.format(schema=db_schema))),
                       db.Column('role_id', db.Integer(), db.ForeignKey('{schema}.role.id'.format(schema=db_schema))),
                       schema=db_schema)

roles_groups = db.Table('roles_groups',
                       db.Column('group_id', db.Integer(), db.ForeignKey('{schema}.group.id'.format(schema=db_schema))),
                       db.Column('role_id', db.Integer(), db.ForeignKey('{schema}.role.id'.format(schema=db_schema))),
                       schema=db_schema)

groups_users = db.Table('groups_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('{schema}.user.id'.format(schema=db_schema))),
                       db.Column('group_id', db.Integer(), db.ForeignKey('{schema}.group.id'.format(schema=db_schema))),
                       schema=db_schema)


_security = LocalProxy(lambda: current_app.extensions['security'])


class Permission(db.Model, PortalTable):
    __tablename__ = "permission"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
    read_only = db.Column(db.Boolean, default=False)


class Role(db.Model, PortalTable, RoleMixin):
    __tablename__ = "role"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
    read_only = db.Column(db.Boolean, default=False)
    permissions = db.relationship('Permission', secondary=roles_permissions)


class Group(db.Model, PortalTable):
    __tablename__ = "group"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
    read_only = db.Column(db.Boolean, default=False)

    roles = db.relationship('Role', secondary=roles_groups,
                            backref=db.backref('groups', lazy='dynamic'))

    def __eq__(self, other):
        return (self.name == other or
                self.name == getattr(other, 'name', None))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.name)


class User(db.Model, PortalTable, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    username = db.Column(db.String(255), unique=True, index=True)
    name = db.Column(db.String(255))
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    nif = db.Column(db.String(9), unique=True, nullable=True, index=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(45))
    current_login_ip = db.Column(db.String(45))
    login_count = db.Column(db.Integer)
    auth_token = db.Column(db.String())
    auth_token_expire = db.Column(db.DateTime())
    default_map = db.Column(db.String(255))
    default_viewer = db.Column(db.String(255))
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    groups = db.relationship('Group', secondary=groups_users,
                            backref=db.backref('users', lazy='dynamic'))

    '''
    def get_mail_confirm_token(self):
        confirm_salt = _security.confirm_salt or "confirm-salt"

        s = URLSafeTimedSerializer(
            current_app.config["SECRET_KEY"], salt=confirm_salt
        )
        return s.dumps(self.email, salt=confirm_salt)


    @staticmethod
    def verify_mail_confirm_token(token):
        confirm_salt = _security.confirm_salt or "confirm-salt"
        max_age = _security.SECURITY_CONFIRM_EMAIL_WITHIN * 24 * 60 * 60 * 60 if _security.SECURITY_CONFIRM_EMAIL_WITHIN  else 3600

        try:
            s = URLSafeTimedSerializer(
                current_app.config["SECRET_KEY"], salt=confirm_salt
            )
            email = s.loads(token, salt=confirm_salt, max_age=3600)
            return email
        except (SignatureExpired, BadSignature):
            return None
    '''


    def __str__(self):
        return '<User id=%s email=%s>' % (self.id, self.email)

    @hybrid_property
    def all_roles(self):
        ar = []
        ar_ids = []

        for r in self.roles:
            ar.append({ "id": r.id, "name": r.name })
            ar_ids.append(r.id)

        for g in self.groups:
            for r in g.roles:
                if r.id not in ar_ids:
                    ar.append({"id": r.id, "name": r.name})
                    ar_ids.append((r.id))

        return ar
