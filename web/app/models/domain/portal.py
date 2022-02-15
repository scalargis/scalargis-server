from app.database import db
from ..common import PortalTableMixin, GenericTableMixin
from sqlalchemy import ForeignKey

from ..mapas import Planta, TipoPlanta

viewers_roles = db.Table('viewers_roles',
                         db.Column('viewer_id', db.Integer, db.ForeignKey('portal.viewers.id', ondelete="cascade"),
                                   nullable=False),
                         db.Column('role_id', db.Integer, db.ForeignKey('portal.role.id', ondelete="cascade"),
                                   nullable=False),
                         db.PrimaryKeyConstraint('viewer_id', 'role_id'),
                         schema='portal')

components_roles = db.Table('components_roles',
                            db.Column('component_id', db.Integer, db.ForeignKey('portal.components.id'),
                                      nullable=False),
                            db.Column('role_id', db.Integer, db.ForeignKey('portal.role.id'), nullable=False),
                            db.PrimaryKeyConstraint('component_id', 'role_id'),
                            schema='portal')


class Viewer(db.Model, PortalTableMixin):
    __tablename__ = "viewers"
    __table_args__ = {'schema': 'portal'}

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), unique=True)
    title = db.Column(db.String(255))
    description = db.Column(db.Text())
    keywords = db.Column(db.ARRAY(db.Text()))
    author = db.Column(db.String(255))
    copyright = db.Column(db.String(255))
    lang = db.Column(db.String(8))
    slug = db.Column(db.Text())
    uuid = db.Column(db.String(120))
    is_portal = db.Column(db.Boolean())
    is_active = db.Column(db.Boolean())
    is_template = db.Column(db.Boolean())
    srid = db.Column(db.SmallInteger())
    bbox = db.Column(db.String())
    maxbbox = db.Column(db.String())
    config_version = db.Column(db.String(10))
    config_json = db.Column(db.Text())
    parent_id = db.Column(db.Integer())
    owner_id = db.Column(db.Integer(), ForeignKey('portal.user.id'))
    owner = db.relationship('models.security.User')
    # allow_add_layers = db.Column(db.Boolean())
    allow_user_session = db.Column(db.Boolean())
    allow_sharing = db.Column(db.Boolean())
    default_component = db.Column(db.String(255))
    show_help = db.Column(db.Boolean())
    show_credits = db.Column(db.Boolean())
    show_contact = db.Column(db.Boolean())
    on_homepage = db.Column(db.Boolean())
    header_html = db.Column(db.Text())
    help_html = db.Column(db.Text())
    credits_html = db.Column(db.Text())
    img_homepage = db.Column(db.String())
    img_logo = db.Column(db.String())
    img_icon = db.Column(db.String())
    send_email_notifications_admin = db.Column(db.Boolean())
    email_notifications_admin = db.Column(db.Text())
    template = db.Column(db.String(255))
    styles = db.Column(db.Text())
    scripts = db.Column(db.Text())
    custom_script = db.Column(db.Text())
    custom_style = db.Column(db.Text())

    roles = db.relationship('Role', secondary=viewers_roles,
                            backref=db.backref('viewers', lazy='dynamic'))


class Component(db.Model, PortalTableMixin):
    __tablename__ = "components"
    __table_args__ = {'schema': 'portal'}

    id = db.Column(db.Integer(), primary_key=True)
    type = db.Column(db.String(255))
    plugin = db.Column(db.String(255))
    name = db.Column(db.String(255), unique=True)
    title = db.Column(db.String(500))
    description = db.Column(db.Text())
    target = db.Column(db.String(255))
    scripts = db.Column(db.Text())
    is_active = db.Column(db.Boolean())
    config_version = db.Column(db.String(10))
    config_json = db.Column(db.Text())
    action = db.Column(db.String(255))
    template = db.Column(db.Text())
    icon_css_class = db.Column(db.String(255))
    html_content = db.Column(db.Text())

    roles = db.relationship('Role', secondary=components_roles,
                            backref=db.backref('components', lazy='dynamic'))


class ViewerComponent(db.Model):
    __tablename__ = "viewers_components"
    __table_args__ = {'schema': 'portal'}

    component_id = db.Column(db.Integer, db.ForeignKey('portal.components.id'), primary_key=True)
    viewer_id = db.Column(db.Integer, db.ForeignKey('portal.viewers.id'), primary_key=True)
    is_active = db.Column(db.Boolean())
    order = db.Column(db.Integer)
    config_json = db.Column(db.Text())
    html_content = db.Column(db.Text())
    roles = db.Column(db.Text())
    target = db.Column(db.String(255))

    component = db.relationship(
        Component,
        backref=db.backref("viewers")
    )
    viewer = db.relationship(
        Viewer,
        backref=db.backref("components")
    )


class ViewerPrintGroup(db.Model):
    __tablename__ = "viewers_print_groups"
    __table_args__ = {'schema': 'portal'}

    print_group_id = db.Column(db.Integer, db.ForeignKey('portal.tipo_planta.id'), primary_key=True)
    viewer_id = db.Column(db.Integer, db.ForeignKey('portal.viewers.id'), primary_key=True)
    order = db.Column(db.Integer)

    print_group = db.relationship(
        TipoPlanta,
        backref=db.backref("viewers")
    )
    viewer = db.relationship(
        Viewer,
        backref=db.backref("print_groups")
    )


class ViewerPrint(db.Model):
    __tablename__ = "viewers_prints"
    __table_args__ = {'schema': 'portal'}

    print_id = db.Column(db.Integer, db.ForeignKey('portal.planta.id'), primary_key=True)
    viewer_id = db.Column(db.Integer, db.ForeignKey('portal.viewers.id'), primary_key=True)
    order = db.Column(db.Integer)

    print = db.relationship(
        Planta,
        backref=db.backref("viewers")
    )
    viewer = db.relationship(
        Viewer,
        backref=db.backref("prints")
    )


class UserViewerSession(db.Model):
    __tablename__ = "user_viewer_session"
    __table_args__ = {'schema': 'portal'}

    id = db.Column(db.Integer(), primary_key=True)
    config_json = db.Column(db.Text())
    viewer_id = db.Column(db.Integer(), db.ForeignKey("portal.viewers.id", ondelete="cascade"))
    user_id = db.Column(db.Integer(), db.ForeignKey("portal.user.id", ondelete="cascade"))

    id_user_create = db.Column(db.Integer())
    created_at = db.Column(db.DateTime())
    id_user_update = db.Column(db.Integer())
    updated_at = db.Column(db.DateTime())


class UserDataLayer(db.Model, PortalTableMixin):
    __tablename__ = "user_data_layer"
    __table_args__ = {'schema': 'portal'}

    id = db.Column(db.Integer(), primary_key=True)
    uuid = db.Column(db.String(120))
    title = db.Column(db.String(500))
    description = db.Column(db.Text())
    data_geojson = db.Column(db.Text())
    metadata_geojson = db.Column(db.Text())
    viewer_id = db.Column(db.Integer)
    owner_id = db.Column(db.Integer())
    is_private = db.Column(db.Boolean())
    is_active = db.Column(db.Boolean())
    allow_anonymous = db.Column(db.Boolean())
    last_access = db.Column(db.DateTime())


class CoordinateSystems(db.Model, GenericTableMixin):
    __tablename__ = "coordinate_systems"
    __table_args__ = {'schema': 'portal'}


class ContactMessage(db.Model):
    __tablename__ = "contact_message"
    __table_args__ = {'schema': 'portal'}

    id = db.Column(db.Integer(), primary_key=True)
    viewer_id = db.Column(db.Integer())
    name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    message = db.Column(db.Text())
    message_json = db.Column(db.Text())
    user_id = db.Column(db.Integer())
    message_date = db.Column(db.Date())
    checked = db.Column(db.Boolean())
    checked_date = db.Column(db.Date())
    closed = db.Column(db.Boolean())
    closed_date = db.Column(db.Date())
    notes = db.Column(db.Text())
    message_uuid = db.Column(db.Text())
