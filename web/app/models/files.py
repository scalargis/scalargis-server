from app.database import db


class DocumentDirectory(db.Model):
    __tablename__ = "document_directory"
    __table_args__ = {'schema': 'portal'}

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

    rules = db.relationship('DocumentDirectoryRule', back_populates="document_directory")


class DocumentDirectoryRule(db.Model):
    __tablename__ = "document_directory_rules"
    __table_args__ = {'schema': 'portal'}

    id = db.Column(db.Integer(), primary_key=True)
    doc_dir_id = db.Column(db.Integer, db.ForeignKey('portal.document_directory.id'))
    mapa_id = db.Column(db.Integer, db.ForeignKey('portal.mapa.id'))
    filtro = db.Column(db.Text())
    excluir = db.Column(db.Text())
    excluir_dir = db.Column(db.Text())
    descricao = db.Column(db.Text())

    # document_directory = db.relationship(DocumentDirectory, backref=db.backref("document_directory_assoc"))
    document_directory = db.relationship(DocumentDirectory, back_populates="rules")
