from app.database import db
from sqlalchemy.orm import relationship


class AuditOperacao(db.Model):
    __tablename__ = "audit_operacao"
    __table_args__ = {'schema': 'portal'}

    id = db.Column(db.Integer(), primary_key=True)
    codigo = db.Column(db.String(50), unique=True)
    nome = db.Column(db.String(500))
    descricao = db.Column(db.Text())
    n1 = db.Column(db.Float())
    n2 = db.Column(db.Float())
    v1 = db.Column(db.String(50))
    v2 = db.Column(db.String(50))
    anulado = db.Column(db.Boolean())
    flg_ro = db.Column(db.Boolean())


class AuditLog(db.Model):
    __tablename__ = "audit_log"
    __table_args__ = {'schema': 'portal'}

    id = db.Column(db.Integer(), primary_key=True)
    id_mapa = db.Column(db.Integer(), db.ForeignKey('portal.mapa.id'))
    mapa = relationship("Mapa")  # TO CHECK IF MISSING SOMEWHERE
    id_ref = db.Column(db.Integer())
    data_ref = db.Column(db.DateTime(timezone=False))
    descricao = db.Column(db.Text())
    id_user = db.Column(db.Integer())
    id_modulo = db.Column(db.Integer())
    id_tema = db.Column(db.Integer())
    operacao_id = db.Column(db.Integer, db.ForeignKey('portal.audit_operacao.id'))
    operacao = relationship("AuditOperacao")


class AuditViewerLog(db.Model):
    __tablename__ = "audit_viewer_log"
    __table_args__ = {'schema': 'portal'}

    id = db.Column(db.Integer(), primary_key=True)
    id_viewer = db.Column(db.Integer())
    id_ref = db.Column(db.Integer())
    data_ref = db.Column(db.DateTime(timezone=False))
    description = db.Column(db.Text())
    id_user = db.Column(db.Integer())
    id_module = db.Column(db.Integer())
    id_theme = db.Column(db.Integer())
    operation_id = db.Column(db.Integer)
