from app.database import db


class TypeTableMixin(object):
    id = db.Column(db.Integer(), primary_key=True)
    code = db.Column("code", db.String(255), unique=True)
    name = db.Column(db.String(255))
    notes = db.Column(db.String(255))
    read_only = db.Column(db.Boolean())
    active = db.Column(db.Boolean(), default=True)


class TypeExtendedTableMixin(TypeTableMixin):
    n1 = db.Column(db.Float())
    n2 = db.Column(db.Float())
    t1 = db.Column(db.String(255))
    t2 = db.Column(db.String(255))


class DomainTableMixin(object):
    id = db.Column(db.Integer(), primary_key=True)
    record_status = db.Column("record_status_id", db.Integer())
    id_user_ins = db.Column("id_user_ins", db.Integer())
    date_ins = db.Column("date_ins", db.Date())
    id_user_upd = db.Column("id_user_upd", db.Integer())
    date_upd = db.Column("date_upd", db.Date())


class RecordStatus(db.Model, TypeTableMixin):
    __tablename__ = "record_status_value"
    __table_args__ = {'schema': 'portal'}


class PortalTableMixin(object):
    id_user_create = db.Column(db.Integer())
    created_at = db.Column(db.Date())
    id_user_update = db.Column(db.Integer())
    updated_at = db.Column(db.Date())


class GenericTableMixin(PortalTableMixin):
    id = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.Text(), unique=True)
    name = db.Column(db.Text())
    description = db.Column(db.Text())
    config_json = db.Column(db.Text())
    order = db.Column(db.Integer())
    read_only = db.Column(db.Boolean(), default=False)
    active = db.Column(db.Boolean(), default=True)
