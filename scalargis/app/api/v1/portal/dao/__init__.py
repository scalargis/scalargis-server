from werkzeug.exceptions import Forbidden


def get_record_by_id(entity, id):
    qy = entity.query.filter(entity.id == id)
    return qy.one_or_none()


def refuse_read_only(*records):
    """Raises Forbidden when any record has read_only set."""
    if any(getattr(r, 'read_only', None) for r in records):
        raise Forbidden('The record is read only')
