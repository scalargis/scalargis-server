from werkzeug.exceptions import Forbidden


def get_record_by_id(entity, id):
    qy = entity.query.filter(entity.id == id)
    return qy.one_or_none()


def copy_fields(record, data, fields, blank_to_none=False):
    """Copies each field that data holds onto record and keeps the value of each field that data omits."""
    pairs = fields.items() if isinstance(fields, dict) else ((f, f) for f in fields)
    for key, attr in pairs:
        if key in data and hasattr(record, attr):
            value = data[key]
            setattr(record, attr, None if blank_to_none and value == '' else value)


def refuse_read_only(*records):
    """Raises Forbidden when any record has read_only set."""
    if any(getattr(r, 'read_only', None) for r in records):
        raise Forbidden('The record is read only')
