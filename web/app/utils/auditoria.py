from enum import Enum
import datetime
import logging
from app.database import db
from app.models.auditoria import AuditLog, AuditViewerLog, AuditOperacao
from app.utils import constants
from app.utils.decorators import async_task

class EnumOperacaoAuditoria(Enum):
    VisualizarMapa = 'VM'
    EmissaoPlanta = 'EP'
    EmissaoPlantaMerge = 'EPM'
    AnalisePlano = 'AP'
    Confrontacao = 'CFT'
    ContactoMensagem = 'MSG'
    BackOffice = 'BOF'


def log(id_mapa, id_ref, operacao, modulo_id, tema_id, user_id):
    logger = logging.getLogger(__name__)

    try:
        se = db.session

        if isinstance(operacao, int):
            op = se.query(AuditOperacao).filter(AuditOperacao.id == operacao).first()
        else:
            op = se.query(AuditOperacao).filter(AuditOperacao.codigo.ilike(operacao.value)).first()

        record = AuditLog()
        record.operacao_id = op.id
        record.id_mapa = id_mapa
        record.id_ref = id_ref
        record.id_modulo = modulo_id
        record.id_tema = tema_id
        record.id_user = user_id
        record.data_ref = datetime.datetime.now()

        se.add(record)

        se.commit()
    except Exception as e:
        se.rollback()

        logger.error(constants.AUDIT_INSERT_ERROR + ': ' + str(e))

@async_task
def log_async(app, id_mapa, id_ref, operacao, modulo_id, tema_id, user_id):
    with app.app_context():
        logger = logging.getLogger(__name__)

        try:
            se = db.session

            if isinstance(operacao, int):
                op = se.query(AuditOperacao).filter(AuditOperacao.id == operacao).first()
            else:
                op = se.query(AuditOperacao).filter(AuditOperacao.codigo.ilike(operacao.value)).first()

            record = AuditLog()
            record.operacao_id = op.id
            record.id_mapa = id_mapa
            record.id_ref = id_ref
            record.id_modulo = modulo_id
            record.id_tema = tema_id
            record.id_user = user_id
            record.data_ref = datetime.datetime.now()

            se.add(record)

            se.commit()
        except Exception as e:
            se.rollback()

            logger.error(constants.AUDIT_INSERT_ERROR + ': ' + str(e))

def log_viewer(id_viewer, id_ref, operation, module_id, theme_id, user_id):
    logger = logging.getLogger(__name__)

    try:
        se = db.session

        if isinstance(operation, int):
            op = se.query(AuditOperacao).filter(AuditOperacao.id == operation).first()
        else:
            op = se.query(AuditOperacao).filter(AuditOperacao.codigo.ilike(operation.value)).first()

        record = AuditViewerLog()
        record.operation_id = op.id if op else None
        record.id_viewer = id_viewer
        record.id_ref = id_ref
        record.id_module = module_id
        record.id_theme = theme_id
        record.id_user = user_id
        record.data_ref = datetime.datetime.now()

        se.add(record)

        se.commit()
    except Exception as e:
        se.rollback()

        logger.error(constants.AUDIT_INSERT_ERROR + ': ' + str(e))

@async_task
def log_viewer_async(app, id_viewer, id_ref, operation, module_id, theme_id, user_id):
    with app.app_context():
        logger = logging.getLogger(__name__)

        try:
            se = db.session

            if isinstance(operation, int):
                op = se.query(AuditOperacao).filter(AuditOperacao.id == operation).first()
            else:
                op = se.query(AuditOperacao).filter(AuditOperacao.codigo.ilike(operation.value)).first()

            record = AuditViewerLog()
            record.operation_id = op.id if op else None
            record.id_viewer = id_viewer
            record.id_ref = id_ref
            record.id_module = module_id
            record.id_theme = theme_id
            record.id_user = user_id
            record.data_ref = datetime.datetime.now()

            se.add(record)

            se.commit()
        except Exception as e:
            se.rollback()

            logger.error(constants.AUDIT_INSERT_ERROR + ': ' + str(e))


@async_task
def log_backoffice_async(app, operation, user_id):
    with app.app_context():
        logger = logging.getLogger(__name__)

        try:
            se = db.session

            if isinstance(operation, int):
                op = se.query(AuditOperacao).filter(AuditOperacao.id == operation).first()
            else:
                op = se.query(AuditOperacao).filter(AuditOperacao.codigo.ilike(operation.value)).first()

            record = AuditLog()
            record.operacao_id = op.id if op else None
            record.id_user = user_id
            record.data_ref = datetime.datetime.now()

            se.add(record)

            se.commit()
        except Exception as e:
            se.rollback()

            logger.error(constants.AUDIT_INSERT_ERROR + ': ' + str(e))