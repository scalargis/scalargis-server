from app.database import db


class PortalTableMixin(object):
    id_user_create = db.Column(db.Integer())
    created_at = db.Column(db.DateTime())
    id_user_update = db.Column(db.Integer())
    updated_at = db.Column(db.DateTime())


class TypeTableMixin(object):
    id = db.Column(db.Integer(), primary_key=True)
    code = db.Column("code", db.String(255), unique=True)
    name = db.Column(db.String(255))
    notes = db.Column(db.String(255))
    read_only = db.Column(db.Boolean())
    active = db.Column(db.Boolean(), default=True)


class GenericTableMixin(PortalTableMixin):
    id = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.Text(), unique=True)
    name = db.Column(db.Text())
    description = db.Column(db.Text())
    config_json = db.Column(db.Text())
    order = db.Column(db.Integer())
    read_only = db.Column(db.Boolean(), default=False)
    active = db.Column(db.Boolean(), default=True)
