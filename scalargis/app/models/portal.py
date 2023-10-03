from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, column_property
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import ARRAY
from geoalchemy2.types import Geometry
import geoalchemy2.functions as geo_funcs

from app.database import db
from app import get_db_schema
from .common import PortalTable, PortalTableMixin, GenericTableMixin, TypeTableMixin


db_schema = get_db_schema()


viewers_roles = db.Table('viewers_roles',
                         db.Column('viewer_id', db.Integer,
                                   db.ForeignKey('{schema}.viewers.id'.format(schema=db_schema), ondelete="cascade"),
                                   nullable=False),
                         db.Column('role_id',
                                   db.Integer,
                                   db.ForeignKey('{schema}.role.id'.format(schema=db_schema), ondelete="cascade"),
                                   nullable=False),
                         db.PrimaryKeyConstraint('viewer_id', 'role_id'),
                         schema=db_schema)

prints_roles = db.Table('prints_roles',
                        db.Column('print_id', db.Integer,
                                  db.ForeignKey('{schema}.print.id'.format(schema=db_schema)), nullable=False),
                        db.Column('role_id', db.Integer,
                                  db.ForeignKey('{schema}.role.id'.format(schema=db_schema)), nullable=False),
                        db.PrimaryKeyConstraint('print_id', 'role_id'),
                        schema=db_schema)

print_groups_roles = db.Table('print_groups_roles',
                              db.Column('print_group_id', db.Integer,
                                        db.ForeignKey('{schema}.print_group.id'.format(schema=db_schema)), nullable=False),
                              db.Column('role_id', db.Integer,
                                        db.ForeignKey('{schema}.role.id'.format(schema=db_schema)), nullable=False),
                              db.PrimaryKeyConstraint('print_group_id', 'role_id'),
                              schema=db_schema)


class Viewer(db.Model, PortalTable, PortalTableMixin):
    __tablename__ = "viewers"

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
    is_shared = db.Column(db.Boolean())
    srid = db.Column(db.SmallInteger())
    bbox = db.Column(db.String())
    maxbbox = db.Column(db.String())
    config_version = db.Column(db.String(10))
    config_json = db.Column(db.Text())
    parent_id = db.Column(db.Integer())
    owner_id = db.Column(db.Integer(), ForeignKey('{schema}.user.id'.format(schema=db_schema)))
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
    img_logo_alt = db.Column(db.String())
    img_icon = db.Column(db.String())
    send_email_notifications_admin = db.Column(db.Boolean())
    email_notifications_admin = db.Column(db.Text())
    styles = db.Column(db.Text())
    scripts = db.Column(db.Text())
    custom_script = db.Column(db.Text())
    custom_style = db.Column(db.Text())
    manifest_json = db.Column(db.Text())

    roles = db.relationship(
        'Role',
        secondary=viewers_roles,
        backref=db.backref('viewers', lazy='dynamic')
    )

    notifications_manager_roles = db.Column(ARRAY(db.Text()))


class PrintGroup(db.Model, PortalTable, PortalTableMixin):
    __tablename__ = "print_group"

    __srid__ = 4326

    id = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.String(255), unique=True)
    title = db.Column(db.String(500))
    description = db.Column(db.Text())
    is_active = db.Column(db.Boolean())
    identification = db.Column(db.Boolean(), default=False)
    identification_fields = db.Column(db.JSON())
    allow_drawing = db.Column(db.Boolean(), default=True)
    location_marking = db.Column(db.Boolean())
    draw_location = db.Column(db.Boolean())
    multi_geom = db.Column(db.Boolean())
    show_author = db.Column(db.Boolean(), default=False)
    payment_reference = db.Column(db.Boolean(), default=False)
    print_purpose = db.Column(db.Boolean(), default=False)
    restrict_scales = db.Column(db.Boolean(), default=False)
    restrict_scales_list = db.Column(db.Text(), default='1000,2000,5000,10000,20000,25000,50000')
    free_scale = db.Column(db.Boolean(), default=False)
    map_scale = db.Column(db.Boolean(), default=False)

    form_fields = db.Column(db.JSON())
    select_prints = db.Column(db.Boolean(), default=True)
    group_prints = db.Column(db.Boolean(), default=False)

    layouts = db.relationship(
        "PrintGroupLayout",
        back_populates="print_group",
        cascade="all, delete-orphan"
    )

    roles = db.relationship(
        'Role',
        secondary=print_groups_roles,
        backref=db.backref('print_groups', lazy='dynamic')
    )

    geometry = db.Column('geom', Geometry(geometry_type='Geometry', srid=__srid__))
    geometry_wkt = column_property(geo_funcs.ST_AsText(geo_funcs.ST_Transform(geometry, __srid__)))
    tolerance_filter = db.Column(db.Integer())
    show_all_prints = db.Column(db.Boolean(), default=False)

    geometry_srid = __srid__

    @hybrid_property
    def viewers_sample(self):
        return [rec.viewer for rec in self.viewer_assoc.limit(10).all()]


class Print(db.Model, PortalTable, PortalTableMixin):
    __tablename__ = "print"

    __srid__ = 4326

    id = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.String(255), unique=True)
    name = db.Column(db.String(255))
    title = db.Column(db.String(500))
    description = db.Column(db.Text())
    scale = db.Column(db.Integer())
    format = db.Column(db.String(50))
    orientation = db.Column(db.String(50))
    config_json = db.Column(db.Text())
    identification = db.Column(db.Boolean())
    identification_fields = db.Column(db.JSON())
    allow_drawing = db.Column(db.Boolean(), default=True)
    location_marking = db.Column(db.Boolean())
    draw_location = db.Column(db.Boolean())
    multi_geom = db.Column(db.Boolean())
    free_printing = db.Column(db.Boolean())
    add_title = db.Column(db.Boolean())
    show_author = db.Column(db.Boolean(), default=False)
    payment_reference = db.Column(db.Boolean(), default=False)
    print_purpose = db.Column(db.Boolean(), default=False)
    restrict_scales = db.Column(db.Boolean(), default=False)
    restrict_scales_list = db.Column(db.Text(),
                                     default='1000,2000,5000,10000,20000,25000,50000')
    free_scale = db.Column(db.Boolean(), default=False)
    map_scale = db.Column(db.Boolean(), default=False)
    form_fields = db.Column(db.JSON())
    srid = db.Column(db.Integer())
    is_active = db.Column(db.Boolean())

    layouts = db.relationship(
        "PrintLayout",
        back_populates="print",
        cascade="all, delete-orphan"
    )

    roles = db.relationship(
        'Role',
        secondary=prints_roles,
        backref=db.backref('prints', lazy='dynamic')
    )

    geometry = db.Column('geom', Geometry(geometry_type='Geometry', srid=__srid__))
    geometry_wkt = column_property(geo_funcs.ST_AsText(geo_funcs.ST_Transform(geometry, __srid__)))
    tolerance_filter = db.Column(db.Integer())

    owner_id = db.Column(db.Integer(), ForeignKey('{schema}.user.id'.format(schema=db_schema)))
    owner = db.relationship('models.security.User')

    geometry_srid = __srid__

    @hybrid_property
    def viewers_sample(self):
        return [rec.viewer for rec in self.viewer_assoc.limit(10).all()]


class ViewerPrintGroup(db.Model, PortalTable):
    __tablename__ = "viewers_print_groups"

    print_group_id = db.Column(db.Integer,
                               db.ForeignKey('{schema}.print_group.id'.format(schema=db_schema)), primary_key=True)
    viewer_id = db.Column(db.Integer, db.ForeignKey('{schema}.viewers.id'.format(schema=db_schema)), primary_key=True)
    order = db.Column(db.Integer)

    print_group = db.relationship(
        PrintGroup,
        backref=db.backref("viewer_assoc", cascade="all, delete-orphan", lazy='dynamic')
    )
    viewer = db.relationship(
        Viewer,
        backref=db.backref("print_group_assoc", order_by='ViewerPrintGroup.order', cascade="all, delete-orphan")
    )


class ViewerPrint(db.Model, PortalTable):
    __tablename__ = "viewers_prints"

    print_id = db.Column(db.Integer, db.ForeignKey('{schema}.print.id'.format(schema=db_schema)), primary_key=True)
    viewer_id = db.Column(db.Integer, db.ForeignKey('{schema}.viewers.id'.format(schema=db_schema)), primary_key=True)
    order = db.Column(db.Integer)

    print = db.relationship(
        Print,
        backref=db.backref("viewer_assoc", cascade="all, delete-orphan", lazy='dynamic'),
    )
    viewer = db.relationship(
        Viewer,
        backref=db.backref("print_assoc", order_by='ViewerPrint.order', cascade="all, delete-orphan")
    )


class PrintElement(db.Model, PortalTable, PortalTableMixin):
    __tablename__ = "print_element"

    id = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.String(255), unique=True)
    name = db.Column(db.String(255))
    config = db.Column(db.Text())


class PrintLayout(db.Model, PortalTable):
    __tablename__ = "print_layouts"

    id = db.Column(db.Integer(), primary_key=True)
    print_id = db.Column(db.Integer,
                         db.ForeignKey('{schema}.print.id'.format(schema=db_schema), ondelete='cascade'))
    print = relationship("Print", back_populates="layouts")
    orientation = db.Column(db.String(25))
    format = db.Column(db.String(25))
    config = db.Column(db.Text())


class PrintGroupLayout(db.Model, PortalTable):
    __tablename__ = "print_group_layouts"

    id = db.Column(db.Integer(), primary_key=True)
    print_group_id = db.Column(db.Integer,
                               db.ForeignKey('{schema}.print_group.id'.format(schema=db_schema), ondelete='cascade'))
    print_group = relationship("PrintGroup", back_populates="layouts")
    orientation = db.Column(db.String(25))
    format = db.Column(db.String(25))
    config = db.Column(db.Text())


class PrintGroupPrint(db.Model, PortalTable):
    __tablename__ = "print_group_prints"

    print_group_id = db.Column(db.Integer,
                               db.ForeignKey('{schema}.print_group.id'.format(schema=db_schema)), primary_key=True)
    print_id = db.Column(db.Integer,
                         db.ForeignKey('{schema}.print.id'.format(schema=db_schema)), primary_key=True)
    order = db.Column(db.Integer)

    print_group = db.relationship(
        PrintGroup,
        backref=db.backref("print_assoc", order_by='PrintGroupPrint.order', cascade="all, delete-orphan")
    )
    print = db.relationship(
        Print,
        backref=db.backref("print_group_assoc", cascade="all, delete-orphan", lazy='dynamic')
    )


class PrintGroupChild(db.Model, PortalTable):
    __tablename__ = "print_group_childs"

    print_group_id = db.Column(db.Integer,
                               db.ForeignKey('{schema}.print_group.id'.format(schema=db_schema)), primary_key=True)
    print_group_child_id = db.Column(db.Integer,
                                     db.ForeignKey('{schema}.print_group.id'.format(schema=db_schema)), primary_key=True)
    order = db.Column(db.Integer)

    print_group_parent = db.relationship(
        PrintGroup,
        backref=db.backref(
            "print_group_child_assoc",
            cascade="save-update, merge, delete, delete-orphan",
            order_by='PrintGroupChild.order'
        ),
        foreign_keys=[print_group_id]
    )

    print_group_child = db.relationship(
        "PrintGroup",
        foreign_keys=[print_group_child_id]
    )


class PrintOutput(db.Model, PortalTable, PortalTableMixin):
    __tablename__ = "print_outputs"

    __srid__ = 4326

    id = db.Column(db.Integer(), primary_key=True)
    output_number = db.Column(db.Integer())
    output_year = db.Column(db.Integer())
    print_group_id = db.Column(db.Integer())
    print_group_name = db.Column(db.String(255))
    print_id = db.Column(db.Integer, db.ForeignKey('{schema}.print.id'.format(schema=db_schema)))
    print_name = db.Column(db.String(255))
    print = relationship("Print")
    source_id = db.Column(db.Integer())
    source = db.Column(db.String(255))
    scale = db.Column(db.Integer())
    title = db.Column(db.String(500))
    from_values = db.Column(db.JSON())  # TODO - remove,
    user_reference_number = db.Column(db.String())
    user_reference_name = db.Column(db.String())
    output_date = db.Column(db.DateTime())
    geom = db.Column(Geometry(geometry_type='GEOMETRY', srid=__srid__))
    geometry_wkt = column_property(geo_funcs.ST_AsText(geo_funcs.ST_Transform(geom, __srid__)))

    geometry_srid = __srid__

    @property
    def print_output_number(self):
        return '{}/{}'.format(self.output_number or '    ', self.output_year or '    ') if self.output_number else None


class PrintOutputNumber(db.Model, PortalTable):
    __tablename__ = "print_output_number"

    output_number = db.Column(db.Integer(), primary_key=True)
    output_year = db.Column(db.Integer(), primary_key=True)


class UserViewerSession(db.Model, PortalTable, PortalTableMixin):
    __tablename__ = "user_viewer_session"

    id = db.Column(db.Integer(), primary_key=True)
    config_json = db.Column(db.Text())
    viewer_id = db.Column(db.Integer(), db.ForeignKey("{schema}.viewers.id".format(schema=db_schema), ondelete="cascade"))
    user_id = db.Column(db.Integer(), db.ForeignKey("{schema}.user.id".format(schema=db_schema), ondelete="cascade"))


class UserDataLayer(db.Model, PortalTable, PortalTableMixin):
    __tablename__ = "user_data_layer"

    id = db.Column(db.Integer(), primary_key=True)
    uuid = db.Column(db.String(120))
    title = db.Column(db.String(500))
    description = db.Column(db.Text())
    data_geojson = db.Column(db.Text())
    metadata_geojson = db.Column(db.Text())
    viewer_id = db.Column(db.Integer())
    owner_id = db.Column(db.Integer())
    is_private = db.Column(db.Boolean())
    is_active = db.Column(db.Boolean())
    allow_anonymous = db.Column(db.Boolean())
    last_access = db.Column(db.DateTime())


class CoordinateSystems(db.Model, PortalTable, GenericTableMixin):
    __tablename__ = "coordinate_systems"

    srid = db.Column(db.Integer())


class ContactMessage(db.Model, PortalTable, PortalTableMixin):
    __tablename__ = "contact_message"

    id = db.Column(db.Integer(), primary_key=True)
    viewer_id = db.Column(db.Integer(), db.ForeignKey("{schema}.viewers.id".format(schema=db_schema), ondelete="cascade"))
    viewer = db.relationship(Viewer)
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


class SiteSettings(db.Model, PortalTable, TypeTableMixin, PortalTableMixin):
    __tablename__ = "site_settings"

    setting_value = db.Column(db.Text())


class ViewerContent(db.Model, PortalTable, PortalTableMixin):
    __tablename__ = "viewer_content"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.Text(), unique=True)
    description = db.Column(db.Text())
    keywords = db.Column(db.ARRAY(db.Text()))
    content = db.Column(db.Text())
    template = db.Column(db.Text())
    roles = db.Column(db.ARRAY(db.Text()))
    read_only = db.Column(db.Boolean(), default=False)
    active = db.Column(db.Boolean(), default=True)


class Widget(db.Model, PortalTable, PortalTableMixin):
    __tablename__ = "widget"

    id = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.String(255), unique=True)
    title = db.Column(db.String(500))
    description = db.Column(db.Text())
    active = db.Column(db.Boolean())
    config = db.Column(db.Text())
    roles = db.Column(db.Text())


class RecordStatus(db.Model, PortalTable, TypeTableMixin):
    __tablename__ = "record_status_value"


class AuditOperation(db.Model, PortalTable, TypeTableMixin):
    __tablename__ = "audit_operation"


class AuditLog(db.Model, PortalTable):
    __tablename__ = "audit_log"

    id = db.Column(db.Integer(), primary_key=True)
    id_viewer = db.Column(db.Integer())
    id_ref = db.Column(db.Integer())
    date_ref = db.Column(db.DateTime(timezone=False))
    description = db.Column(db.Text())
    id_user = db.Column(db.Integer())
    id_module = db.Column(db.Integer())
    id_theme = db.Column(db.Integer())
    operation_id = db.Column(db.Integer)
