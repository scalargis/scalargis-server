from app.database import db
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property
from flask_security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required

roles_permissions = db.Table('roles_permissions',
                       db.Column('role_id', db.Integer(), db.ForeignKey('portal.role.id')),
                       db.Column('permission_id', db.Integer(), db.ForeignKey('portal.permission.id')),
                       schema='portal')

roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('portal.user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('portal.role.id')),
                       schema='portal')

roles_groups = db.Table('roles_groups',
                       db.Column('group_id', db.Integer(), db.ForeignKey('portal.group.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('portal.role.id')),
                       schema='portal')

groups_users = db.Table('groups_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('portal.user.id')),
                       db.Column('group_id', db.Integer(), db.ForeignKey('portal.group.id')),
                       schema='portal')


class Permission(db.Model):
    __tablename__ = "permission"
    __table_args__ = {'schema': 'portal'}

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
    read_only = db.Column(db.Boolean, default=False)


class Role(db.Model, RoleMixin):
    __tablename__ = "role"
    __table_args__ = {'schema': 'portal'}

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
    read_only = db.Column(db.Boolean, default=False)
    permissions = db.relationship('Permission', secondary=roles_permissions)


class Group(db.Model):
    __tablename__ = "group"
    __table_args__ = {'schema': 'portal'}

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


class User(db.Model, UserMixin):
    __tablename__ = "user"
    __table_args__ = {'schema': 'portal'}

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    username = db.Column(db.String(255), unique=True, index=True)
    name = db.Column(db.String(255))
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
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
