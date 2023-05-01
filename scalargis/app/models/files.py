from app.database import db
from app import get_db_schema
from .common import PortalTable


db_schema = get_db_schema()


class DocumentDirectory(db.Model, PortalTable):
    __tablename__ = "document_directory"

    id = db.Column(db.Integer(), primary_key=True)
    codigo = db.Column(db.String(255), unique=True)
    path = db.Column(db.String(500))
    titulo = db.Column(db.String(255))
    descricao = db.Column(db.Text())
    allow_upload = db.Column(db.Boolean())
    upload_anonymous = db.Column(db.Boolean())
    upload_overwrite = db.Column(db.Boolean())
    upload_generate_filename = db.Column(db.Boolean())
    allow_delete = db.Column(db.Boolean())
    delete_anonymous = db.Column(db.Boolean())

    rules = db.relationship(
        'DocumentDirectoryRule',
        backref="document_directory"
    )


class DocumentDirectoryRule(db.Model, PortalTable):
    __tablename__ = "document_directory_rules"

    id = db.Column(db.Integer(), primary_key=True)
    doc_dir_id = db.Column(db.Integer, db.ForeignKey('{schema}.document_directory.id'.format(schema=db_schema)))
    viewer_id = db.Column(db.Integer, db.ForeignKey('{schema}.viewers.id'.format(schema=db_schema)))
    filtro = db.Column(db.Text())
    excluir = db.Column(db.Text())
    excluir_dir = db.Column(db.Text())
    descricao = db.Column(db.Text())
