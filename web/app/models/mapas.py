from app.database import db
from .common import TypeTableMixin, TypeExtendedTableMixin
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref, column_property
from geoalchemy2.types import Geometry
import geoalchemy2.functions as geo_funcs

modulos_mapas = db.Table('mapas_modulos',
                         db.Column('mapa_id', db.Integer, db.ForeignKey('portal.mapa.id'), nullable=False),
                         db.Column('modulo_id', db.Integer, db.ForeignKey('portal.modulo.id'), nullable=False),
                         db.PrimaryKeyConstraint('mapa_id', 'modulo_id'),
                         schema='portal')

catalogos_mapas = db.Table('mapas_catalogos',
                           db.Column('mapa_id', db.Integer, db.ForeignKey('portal.mapa.id'), nullable=False),
                           db.Column('catalogo_id', db.Integer, db.ForeignKey('portal.catalogo_metadados.id'),
                                     nullable=False),
                           db.PrimaryKeyConstraint('mapa_id', 'catalogo_id'),
                           schema='portal')

roles_mapas = db.Table('mapas_roles',
                       db.Column('mapa_id', db.Integer, db.ForeignKey('portal.mapa.id'), nullable=False),
                       db.Column('role_id', db.Integer, db.ForeignKey('portal.role.id'), nullable=False),
                       db.PrimaryKeyConstraint('mapa_id', 'role_id'),
                       schema='portal')

roles_plantas = db.Table('plantas_roles',
                         db.Column('planta_id', db.Integer, db.ForeignKey('portal.planta.id'), nullable=False),
                         db.Column('role_id', db.Integer, db.ForeignKey('portal.role.id'), nullable=False),
                         db.PrimaryKeyConstraint('planta_id', 'role_id'),
                         schema='portal')

roles_tipo_plantas = db.Table('tipo_plantas_roles',
                              db.Column('tipo_planta_id', db.Integer, db.ForeignKey('portal.tipo_planta.id'),
                                        nullable=False),
                              db.Column('role_id', db.Integer, db.ForeignKey('portal.role.id'), nullable=False),
                              db.PrimaryKeyConstraint('tipo_planta_id', 'role_id'),
                              schema='portal')


# tipos_plantas_childs = db.Table('tipos_plantas_childs',
#                        db.Column('tipo_planta_id', db.Integer, db.ForeignKey('portal.tipo_planta.id'), nullable=False),
#                        db.Column('tipo_planta_child_id', db.Integer, db.ForeignKey('portal.tipo_planta.id'), nullable=False),
#                        db.PrimaryKeyConstraint('tipo_planta_id', 'tipo_planta_child_id'),
#                        schema='portal')

class SiteSettings(db.Model, TypeTableMixin):
    __tablename__ = "site_settings"
    __table_args__ = {'schema': 'portal'}

    setting_value = db.Column(db.Text())


class ConfigMapa(db.Model):
    __tablename__ = "configuracao_mapa"
    __table_args__ = {'schema': 'portal'}

    id = db.Column(db.Integer(), primary_key=True)
    titulo = db.Column(db.String(255))
    jsonConfig = db.Column("config", db.Text())
    descricao = db.Column(db.Text())
    mapas = db.relationship("Mapa", back_populates="configuracao")
    idUserIns = db.Column("id_user_ins", db.Integer())
    dataIns = db.Column("data_ins", db.Date())


class Mapa(db.Model):
    __tablename__ = "mapa"
    __table_args__ = {'schema': 'portal'}

    id = db.Column(db.Integer(), primary_key=True)
    codigo = db.Column(db.String(255), unique=True)
    titulo = db.Column(db.String(255))
    descricao = db.Column(db.Text())
    configuracao_id = db.Column('configuracao_id', db.Integer, db.ForeignKey('portal.configuracao_mapa.id'))
    configuracao = relationship('ConfigMapa', back_populates='mapas')
    configuracao_mapa = db.Column(db.Text())
    modulos = db.relationship('Modulo', secondary=modulos_mapas,
                              backref=db.backref('mapas', lazy='dynamic'))
    tipos_plantas = db.relationship(
        'TipoPlanta',
        secondary='portal.mapas_tipos_plantas'
    )
    plantas = db.relationship(
        'Planta',
        secondary='portal.mapas_plantas'
    )
    catalogos = db.relationship('CatalogoMetadados', secondary=catalogos_mapas,
                                backref=db.backref('mapas', lazy='dynamic'))
    roles = db.relationship('Role', secondary=roles_mapas,
                            backref=db.backref('mapas', lazy='dynamic'))
    widgets = db.relationship(
        'Widget',
        secondary='portal.mapas_widgets'
    )
    portal = db.Column(db.Boolean())
    activo = db.Column(db.Boolean())
    show_help = db.Column(db.Boolean())
    show_credits = db.Column(db.Boolean())
    show_contact = db.Column(db.Boolean())
    header_html = db.Column(db.Text())
    help_html = db.Column(db.Text())
    credits_html = db.Column(db.Text())
    template = db.Column(db.String(255))
    show_widget = db.Column(db.String(50))
    post_script = db.Column(db.Text())
    show_homepage = db.Column(db.Boolean())
    img_homepage = db.Column(db.Text())
    send_email_notifications_admin = db.Column(db.Boolean())
    email_notifications_admin = db.Column(db.Text())


class Modulo(db.Model):
    __tablename__ = "modulo"
    __table_args__ = {'schema': 'portal'}

    id = db.Column(db.Integer(), primary_key=True)
    codigo = db.Column(db.String(255), unique=True)
    titulo = db.Column(db.String(255))
    # mapas = db.relationship('Mapa', secondary=mapas_modulos, lazy='dynamic')

    idUserIns = db.Column("id_user_ins", db.Integer())
    dataIns = db.Column("data_ins", db.Date())


class TipoPlanta(db.Model):
    __tablename__ = "tipo_planta"
    __table_args__ = {'schema': 'portal'}

    __srid__ = 3763

    id = db.Column(db.Integer(), primary_key=True)
    codigo = db.Column(db.String(255), unique=True)
    titulo = db.Column(db.String(500))
    descricao = db.Column(db.Text())
    activo = db.Column('activo', db.Boolean())
    template_flask = db.Column(db.String(500))
    identificacaoRequerente = db.Column('identificacao_requerente', db.Boolean(), default=False)
    marcacaoLocal = db.Column('marcacao_local', db.Boolean(), default=False)
    multiGeom = db.Column('multi_geom', db.Boolean())
    autorEmissao = db.Column('autor_emissao', db.Boolean(), default=False)
    guiaPagamento = db.Column('guia_pagamento', db.Boolean(), default=False)
    finalidadeEmissao = db.Column('finalidade_emissao', db.Boolean(), default=False)
    escalasRestritas = db.Column('escalas_restritas', db.Boolean(), default=False)
    escalasRestritasLista = db.Column('escalas_restritas_lista', db.Text,
                                      default='1000,2000,5000,10000,20000,25000,50000')
    escalaLivre = db.Column('escala_livre', db.Boolean(), default=False)
    escalaMapa = db.Column('escala_mapa', db.Boolean(), default=False)
    identificacaoCampos = db.Column('identificacao_campos', db.JSON)
    formFields = db.Column('form_fields', db.JSON)
    seleccaoPlantas = db.Column('seleccao_plantas', db.Boolean(), default=True)
    agruparPlantas = db.Column('agrupar_plantas', db.Boolean(), default=False)

    layouts = relationship("TipoPlantaLayout", back_populates="tipo_planta")

    plantas = db.relationship(
        'Planta',
        secondary='portal.plantas_tipos_plantas',
        order_by='PlantaTipoPlanta.ordem'
    )

    viewers = db.relationship(
        'Viewer',
        secondary='portal.viewers_print_groups'
    )

    roles = db.relationship('Role', secondary=roles_tipo_plantas,
                            backref=db.backref('tipo_plantas', lazy='dynamic'))

    geometry = db.Column('geom', Geometry(geometry_type='Geometry', srid=__srid__))
    geometry_wkt = column_property(geo_funcs.ST_AsText(geo_funcs.ST_Transform(geometry, __srid__)))
    tolerancia = db.Column(db.Integer())
    showAll = db.Column('show_all', db.Boolean(), default=False)

    idUserIns = db.Column("id_user_ins", db.Integer())
    dataIns = db.Column("data_ins", db.Date())

    geometry_srid = __srid__


class Planta(db.Model):
    __tablename__ = "planta"
    __table_args__ = {'schema': 'portal'}

    __srid__ = 3763

    id = db.Column(db.Integer(), primary_key=True)
    codigo = db.Column(db.String(255), unique=True)
    nome = db.Column(db.String(255))
    titulo = db.Column(db.String(500))
    descricao = db.Column(db.Text())
    escala = db.Column(db.Integer())
    formato = db.Column(db.String(50))
    orientacao = db.Column(db.String(50))
    template = db.Column(db.String(255))
    configuracao = db.Column(db.Text())
    identificacao = db.Column(db.Boolean())
    marcacaoLocal = db.Column('marcacao_local', db.Boolean())
    desenharLocal = db.Column('desenhar_local', db.Boolean())
    multiGeom = db.Column('multi_geom', db.Boolean())
    emissaoLivre = db.Column('emissao_livre', db.Boolean())
    tituloEmissao = db.Column('titulo_emissao', db.Boolean())
    autorEmissao = db.Column('autor_emissao', db.Boolean(), default=False)
    guiaPagamento = db.Column('guia_pagamento', db.Boolean(), default=False)
    finalidadeEmissao = db.Column('finalidade_emissao', db.Boolean(), default=False)
    escalasRestritas = db.Column('escalas_restritas', db.Boolean(), default=False)
    escalasRestritasLista = db.Column('escalas_restritas_lista', db.Text,
                                      default='1000,2000,5000,10000,20000,25000,50000')
    escalaLivre = db.Column('escala_livre', db.Boolean(), default=False)
    escalaMapa = db.Column('escala_mapa', db.Boolean(), default=False)
    identificacaoCampos = db.Column('identificacao_campos', db.JSON)
    formFields = db.Column('form_fields', db.JSON)
    srid = db.Column(db.Integer())
    activo = db.Column('activo', db.Boolean())

    layouts = relationship("PlantaLayout", back_populates="planta")

    tipos_plantas = db.relationship(
        'TipoPlanta',
        secondary='portal.plantas_tipos_plantas'
    )

    mapas = db.relationship(
        'Mapa',
        secondary='portal.mapas_plantas'
    )

    viewers = db.relationship(
        'Viewer',
        secondary='portal.viewers_prints'
    )

    roles = db.relationship('Role', secondary=roles_plantas,
                            backref=db.backref('plantas', lazy='dynamic'))

    geometry = db.Column('geom', Geometry(geometry_type='Geometry', srid=__srid__))
    geometry_wkt = column_property(geo_funcs.ST_AsText(geo_funcs.ST_Transform(geometry, __srid__)))
    tolerancia = db.Column(db.Integer())

    owner_id = db.Column(db.Integer(), ForeignKey('portal.user.id'))
    owner = db.relationship('models.security.User')

    idUserIns = db.Column("id_user_ins", db.Integer())
    dataIns = db.Column("data_ins", db.Date())

    geometry_srid = __srid__


class SubPlanta(db.Model):
    __tablename__ = "sub_planta"
    __table_args__ = {'schema': 'portal'}

    id = db.Column(db.Integer(), primary_key=True)
    codigo = db.Column(db.String(255), unique=True)
    nome = db.Column(db.String(255))
    configuracao = db.Column(db.Text())


class PlantaLayout(db.Model):
    __tablename__ = "planta_layouts"
    __table_args__ = {'schema': 'portal'}

    id = db.Column(db.Integer(), primary_key=True)
    planta_id = db.Column(db.Integer, db.ForeignKey('portal.planta.id', ondelete='cascade'))
    planta = relationship("Planta", back_populates="layouts")
    orientacao = db.Column(db.String(25))
    formato = db.Column(db.String(25))
    configuracao = db.Column(db.Text())


class TipoPlantaLayout(db.Model):
    __tablename__ = "tipo_planta_layouts"
    __table_args__ = {'schema': 'portal'}

    id = db.Column(db.Integer(), primary_key=True)
    tipo_planta_id = db.Column(db.Integer, db.ForeignKey('portal.tipo_planta.id'))
    tipo_planta = relationship("TipoPlanta", back_populates="layouts")
    orientacao = db.Column(db.String(25))
    formato = db.Column(db.String(25))
    configuracao = db.Column(db.Text())


class PlantaTipoPlanta(db.Model):
    __tablename__ = "plantas_tipos_plantas"
    __table_args__ = {'schema': 'portal'}

    tipo_planta_id = db.Column(db.Integer, db.ForeignKey('portal.tipo_planta.id'), primary_key=True)
    planta_id = db.Column(db.Integer, db.ForeignKey('portal.planta.id'), primary_key=True)
    ordem = db.Column(db.Integer)

    tipo_planta = db.relationship(
        TipoPlanta,
        backref=db.backref("planta_assoc")
    )
    planta = db.relationship(Planta, backref=db.backref("tipo_planta_assoc"))


class TipoPlantaChild(db.Model):
    __tablename__ = "tipos_plantas_childs"
    __table_args__ = {'schema': 'portal'}

    tipo_planta_id = db.Column(db.Integer, db.ForeignKey('portal.tipo_planta.id'), primary_key=True)
    tipo_planta_child_id = db.Column(db.Integer, db.ForeignKey('portal.tipo_planta.id'), primary_key=True)
    ordem = db.Column(db.Integer)

    tipo_planta_parent = db.relationship(
        TipoPlanta,
        backref=db.backref("tipo_planta_child_assoc", cascade="save-update, merge, delete, delete-orphan",
                           order_by='TipoPlantaChild.ordem'),
        foreign_keys=[tipo_planta_id]
    )

    tipo_planta_child = db.relationship("TipoPlanta", foreign_keys=[tipo_planta_child_id])


class MapaTipoPlanta(db.Model):
    __tablename__ = "mapas_tipos_plantas"
    __table_args__ = {'schema': 'portal'}

    tipo_planta_id = db.Column(db.Integer, db.ForeignKey('portal.tipo_planta.id'), primary_key=True)
    mapa_id = db.Column(db.Integer, db.ForeignKey('portal.mapa.id'), primary_key=True)
    ordem = db.Column(db.Integer)

    tipo_planta = db.relationship(
        TipoPlanta,
        backref=db.backref("mapa_assoc")
    )
    mapa = db.relationship(Mapa, backref=db.backref("tipo_planta_assoc"))


class MapaPlanta(db.Model):
    __tablename__ = "mapas_plantas"
    __table_args__ = {'schema': 'portal'}

    planta_id = db.Column(db.Integer, db.ForeignKey('portal.planta.id'), primary_key=True)
    mapa_id = db.Column(db.Integer, db.ForeignKey('portal.mapa.id'), primary_key=True)
    ordem = db.Column(db.Integer)

    planta = db.relationship(
        Planta,
        backref=db.backref("mapa_assoc")
    )
    mapa = db.relationship(Mapa, backref=db.backref("planta_assoc"))


class CatalogoMetadados(db.Model):
    __tablename__ = "catalogo_metadados"
    __table_args__ = {'schema': 'portal'}

    id = db.Column(db.Integer(), primary_key=True)
    codigo = db.Column(db.String(255), unique=True)
    titulo = db.Column(db.String(500))
    descricao = db.Column(db.Text())
    url_base = db.Column(db.String(255))
    url_csw = db.Column(db.String(255))
    autenticacao = db.Column(db.Boolean())
    username = db.Column(db.String(255))
    password = db.Column(db.String(255))
    activo = db.Column(db.Boolean())
    tipo = db.Column(db.String(50))
    portal = db.Column(db.Boolean())
    xslt_results_file = db.Column(db.String(500))
    xslt_results = db.Column(db.Text())
    xslt_metadata_file = db.Column(db.String(500))
    xslt_metadata = db.Column(db.Text())
    idUserIns = db.Column("id_user_ins", db.Integer())
    dataIns = db.Column("data_ins", db.Date())


class SistemaCoordenadas(db.Model):
    __tablename__ = "sistema_coordenadas"
    __table_args__ = {'schema': 'portal'}

    id = db.Column(db.Integer(), primary_key=True)
    codigo = db.Column(db.String(50), unique=True)
    srid = db.Column(db.Integer)
    nome = db.Column(db.String(255))
    proj4text = db.Column(db.Text())
    unidades = db.Column(db.Text())
    descricao = db.Column(db.Text())
    ordem = db.Column(db.Integer())
    portal = db.Column(db.Boolean())
    activo = db.Column(db.Boolean())
    idUserIns = db.Column("id_user_ins", db.Integer())
    dataIns = db.Column("data_ins", db.Date())


class Widget(db.Model):
    __tablename__ = "widget"
    __table_args__ = {'schema': 'portal'}

    id = db.Column(db.Integer(), primary_key=True)
    codigo = db.Column(db.String(255), unique=True)
    plugin = db.Column(db.String(255))
    titulo = db.Column(db.String(500))
    descricao = db.Column(db.Text())
    scripts = db.Column(db.Text())
    activo = db.Column(db.Boolean())
    config = db.Column(db.Text())
    action = db.Column(db.String(255))
    template = db.Column(db.Text())
    target = db.Column(db.String(255))
    icon_css_class = db.Column(db.String(255))
    html_content = db.Column(db.Text())
    roles = db.Column(db.Text())

    parent_id = db.Column(db.Integer, db.ForeignKey('portal.widget.id'))
    # parent = relationship("Widget")
    children = relationship("Widget", backref=backref('parent', remote_side=[id]))

    mapas = db.relationship(
        'Mapa',
        secondary='portal.mapas_widgets'
    )

    idUserIns = db.Column("id_user_ins", db.Integer())
    dataIns = db.Column("data_ins", db.Date())


class MapaWidget(db.Model):
    __tablename__ = "mapas_widgets"
    __table_args__ = {'schema': 'portal'}

    widget_id = db.Column(db.Integer, db.ForeignKey('portal.widget.id'), primary_key=True)
    mapa_id = db.Column(db.Integer, db.ForeignKey('portal.mapa.id'), primary_key=True)
    ordem = db.Column("order", db.Integer)
    config = db.Column(db.Text())
    html_content = db.Column(db.Text())
    roles = db.Column(db.Text())
    target = db.Column(db.String(255))

    widget = db.relationship(Widget, backref=db.backref("mapa_assoc"))
    mapa = db.relationship(Mapa, backref=db.backref("widget_assoc"))


class EmissaoPlanta(db.Model):
    __tablename__ = "emissao_planta"
    __table_args__ = {'schema': 'portal'}

    __srid__ = 3763

    id = db.Column(db.Integer(), primary_key=True)
    numero = db.Column(db.Integer())
    ano = db.Column(db.Integer())
    tipo_id = db.Column(db.Integer())
    tipo_nome = db.Column(db.String(255))
    planta_id = db.Column(db.Integer, db.ForeignKey('portal.planta.id'))
    planta_nome = db.Column(db.String(255))
    planta = relationship("Planta")
    mapa_id = db.Column(db.Integer())
    escala = db.Column(db.Integer())
    titulo = db.Column(db.String(500))
    nif_requerente = db.Column(db.String(10))
    nome_requerente = db.Column(db.String(255))
    data_emissao = db.Column("data_emissao", db.DateTime())
    geom = db.Column(Geometry(geometry_type='GEOMETRY', srid=__srid__))
    geometry_wkt = column_property(geo_funcs.ST_AsText(geo_funcs.ST_Transform(geom, __srid__)))
    grupo_emissao = db.Column(db.String(36))
    idUserIns = db.Column("id_user_ins", db.Integer())
    dataIns = db.Column("data_ins", db.Date())

    geometry_srid = __srid__

    @property
    def numero_emissao(self):
        return '{}/{}'.format(self.numero or '    ', self.ano or '    ') if self.numero else None


class ContactoMensagem(db.Model):
    __tablename__ = "contacto_mensagem"
    __table_args__ = {'schema': 'portal'}

    id = db.Column(db.Integer(), primary_key=True)
    mapa_id = db.Column(db.Integer())
    nome = db.Column(db.String(255))
    email = db.Column(db.String(255))
    mensagem = db.Column(db.Text())
    user_id = db.Column(db.Integer())
    data_mensagem = db.Column(db.Date())
    checked = db.Column(db.Boolean())
    checked_date = db.Column(db.Date())
    closed = db.Column(db.Boolean())
    closed_date = db.Column(db.Date())
    observacoes = db.Column(db.Text())
    mensagem_uuid = db.Column(db.Text())


class MDTemaInspire(db.Model, TypeExtendedTableMixin):
    __tablename__ = "geo_t_temas_inspire"
    __table_args__ = {'schema': 'portal'}


class MDTipoServico(db.Model, TypeExtendedTableMixin):
    __tablename__ = "geo_t_tipo_servicos"
    __table_args__ = {'schema': 'portal'}


class MDTipoRecurso(db.Model, TypeExtendedTableMixin):
    __tablename__ = "geo_t_tipo_recursos"
    __table_args__ = {'schema': 'portal'}


class MDTipoRecursoSNIG(db.Model, TypeExtendedTableMixin):
    __tablename__ = "geo_t_snig_tipo_recursos"
    __table_args__ = {'schema': 'portal'}


class MDCategoria(db.Model, TypeExtendedTableMixin):
    __tablename__ = "geo_t_categorias"
    __table_args__ = {'schema': 'portal'}
