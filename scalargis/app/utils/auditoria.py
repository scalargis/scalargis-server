from enum import Enum
import datetime
import logging

from app.database import db
from app.models.portal import AuditLog, AuditOperation
from app.utils import constants
from app.utils.decorators import async_task


class EnumAuditOperation(Enum):
    VisualizarMapa = 'VM'
    EmissaoPlanta = 'EP'
    EmissaoPlantaMerge = 'EPM'
    ContactoMensagem = 'MSG'
    BackOffice = 'BOF'


def log_viewer(id_viewer, id_ref, operation, module_id, theme_id, user_id):
    logger = logging.getLogger(__name__)

    try:
        se = db.session

        if isinstance(operation, int):
            op = se.query(AuditOperation).filter(AuditOperation.id == operation).first()
        else:
            op = se.query(AuditOperation).filter(AuditOperation.code.ilike(operation.value)).first()

        record = AuditLog()
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
                op = se.query(AuditOperation).filter(AuditOperation.id == operation).first()
            else:
                op = se.query(AuditOperation).filter(AuditOperation.code.ilike(operation.value)).first()

            record = AuditLog()
            record.operation_id = op.id if op else None
            record.id_viewer = id_viewer
            record.id_ref = id_ref
            record.id_module = module_id
            record.id_theme = theme_id
            record.id_user = user_id
            record.date_ref = datetime.datetime.now()

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
                op = se.query(AuditOperation).filter(AuditOperation.id == operation).first()
            else:
                op = se.query(AuditOperation).filter(AuditOperation.code.ilike(operation.value)).first()

            record = AuditLog()
            record.operation_id = op.id if op else None
            record.id_user = user_id
            record.data_ref = datetime.datetime.now()

            se.add(record)

            se.commit()
        except Exception as e:
            se.rollback()

            logger.error(constants.AUDIT_INSERT_ERROR + ': ' + str(e))
