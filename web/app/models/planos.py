from app.database import db
from app.models.security import Role
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, synonym
from geoalchemy2.types import Geometry


class TipoPlano(db.Model):
    __tablename__ = "tipo_plano"
    __table_args__ = {'schema': 'planeamento'}

    id = db.Column(db.Integer(), primary_key=True)
    codigo = db.Column(db.String(255), unique=True)
    nome = db.Column(db.String(500))
    descricao = db.Column(db.Text())

    idUserIns = db.Column("id_user_ins", db.Integer())
    dataIns = db.Column("data_ins", db.Date())

class EstadoPlano(db.Model):
    __tablename__ = "estado_plano"
    __table_args__ = {'schema': 'planeamento'}

    id = db.Column(db.Integer(), primary_key=True)
    codigo = db.Column(db.String(255), unique=True)
    nome = db.Column(db.String(500))
    descricao = db.Column(db.Text())

    idUserIns = db.Column("id_user_ins", db.Integer())
    dataIns = db.Column("data_ins", db.Date())

class TipoAlteracaoPlano(db.Model):
    __tablename__ = "tipo_alteracao_plano"
    __table_args__ = {'schema': 'planeamento'}

    id = db.Column(db.Integer(), primary_key=True)
    codigo = db.Column(db.String(255), unique=True)
    nome = db.Column(db.String(500))
    descricao = db.Column(db.Text())

    idUserIns = db.Column("id_user_ins", db.Integer())
    dataIns = db.Column("data_ins", db.Date())

class Plano(db.Model):
    __tablename__ = "plano"
    __table_args__ = {'schema': 'planeamento'}

    id = db.Column(db.Integer(), primary_key=True)
    codigo = db.Column(db.String(255), unique=True)
    nome = db.Column(db.Text())
    nome_abrev = db.Column(db.String(255))
    deposito = db.Column(db.String(255))
    data_publicacao = db.Column(db.Date())
    diploma_publicacao = db.Column(db.String(255))
    dr_publicacao = db.Column(db.String(255))
    descricao = db.Column(db.Text())
    anulado = db.Column(db.Boolean())

    tipo_plano_id = db.Column(db.Integer, db.ForeignKey('planeamento.tipo_plano.id'))
    tipo_plano = relationship("app.models.planos.TipoPlano")

    estado_plano_id = db.Column(db.Integer, db.ForeignKey('planeamento.estado_plano.id'))
    estado_plano = relationship("app.models.planos.EstadoPlano")

    wkb_geometry = db.Column(Geometry(geometry_type='MULTIPOLYGON', srid=3763))

    _ordem = db.Column("ordem", db.Integer, default=0)

    idUserIns = db.Column("id_user_ins", db.Integer())
    dataIns = db.Column("data_ins", db.Date())

    @property
    def ordem(self):
        return self._ordem or 0

    @ordem.setter
    def ordem(self, value):
        self._ordem = value

    ordem = synonym('_ordem', descriptor=ordem)

class DinamicaPlano(db.Model):
    __tablename__ = "dinamica_plano"
    __table_args__ = {'schema': 'planeamento'}

    id = db.Column(db.Integer(), primary_key=True)
    nome = db.Column(db.Text())
    nome_abrev = db.Column(db.String(255))
    data_procedimento = db.Column(db.Date())
    diploma_procedimento = db.Column(db.String(255))
    dr_procedimento = db.Column(db.String(255))
    deposito = db.Column(db.String(255))
    data_publicacao = db.Column(db.Date())
    diploma_publicacao = db.Column(db.String(255))
    dr_publicacao = db.Column(db.String(255))
    descricao = db.Column(db.Text())
    anulado = db.Column(db.Boolean())

    plano_id = db.Column(db.Integer, db.ForeignKey('planeamento.plano.id'))
    plano = relationship("app.models.planos.Plano", backref = 'dinamicas')

    tipo_alteracao_plano_id = db.Column(db.Integer, db.ForeignKey('planeamento.tipo_alteracao_plano.id'))
    tipo_alteracao_plano = relationship("TipoAlteracaoPlano")

    estado_plano_id = db.Column(db.Integer, db.ForeignKey('planeamento.estado_plano.id'))
    estado_plano = relationship("app.models.planos.EstadoPlano")

    _ordem = db.Column("ordem", db.Integer, default=0)

    idUserIns = db.Column("id_user_ins", db.Integer())
    dataIns = db.Column("data_ins", db.Date())

    @property
    def ordem(self):
        return self._ordem or 0

    @ordem.setter
    def ordem(self, value):
        self._ordem = value

    ordem = synonym('_ordem', descriptor=ordem)

class DocumentoPlano(db.Model):
    __tablename__ = "documento_plano"
    __table_args__ = {'schema': 'planeamento'}

    id = db.Column(db.Integer(), primary_key=True)
    nome = db.Column(db.Text())
    nome_abrev = db.Column(db.String(255))
    descricao = db.Column(db.Text())
    url = db.Column(db.Text())
    ficheiro = db.Column(db.String(255))
    ficheiro_original = db.Column(db.String(255))
    dimensao_ficheiro_kb = db.Integer()
    url_mapa = db.Column(db.Text())
    anulado = db.Column(db.Boolean())

    plano_id = db.Column(db.Integer, db.ForeignKey('planeamento.plano.id'))
    plano = relationship("app.models.planos.Plano", backref = 'documentos')

    dinamica_plano_id = db.Column(db.Integer, db.ForeignKey('planeamento.dinamica_plano.id'))
    dinamica_plano = relationship("app.models.planos.DinamicaPlano", backref = 'documentos')

    _ordem = db.Column("ordem", db.Integer, default=0)

    idUserIns = db.Column("id_user_ins", db.Integer())
    dataIns = db.Column("data_ins", db.Date())

    @property
    def ordem(self):
        return self._ordem or 0

    @ordem.setter
    def ordem(self, value):
        self._ordem = value

    ordem = synonym('_ordem', descriptor=ordem)


class FicheiroDocumentoPlano(db.Model):
    __tablename__ = "ficheiro_documento_plano"
    __table_args__ = {'schema': 'planeamento'}

    id = db.Column(db.Integer(), primary_key=True)
    nome = db.Column(db.Text())
    nome_abrev = db.Column(db.String(255))
    descricao = db.Column(db.Text())
    url = db.Column(db.Text())
    ficheiro = db.Column(db.String(255))
    ficheiro_original = db.Column(db.String(255))
    dimensao_ficheiro_kb = db.Integer()
    url_mapa = db.Column(db.Text())
    anulado = db.Column(db.Boolean())

    documento_plano_id = db.Column(db.Integer, db.ForeignKey('planeamento.documento_plano.id'))
    documento_plano = relationship("DocumentoPlano", backref = 'ficheiros')

    _ordem = db.Column("ordem", db.Integer, default=0)

    idUserIns = db.Column("id_user_ins", db.Integer())
    dataIns = db.Column("data_ins", db.Date())

    @property
    def ordem(self):
        return self._ordem or 0

    @ordem.setter
    def ordem(self, value):
        self._ordem = value

    ordem = synonym('_ordem', descriptor=ordem)
