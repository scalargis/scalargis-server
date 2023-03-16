def get_record_by_id(entity, id):
    qy = entity.query.filter(entity.id == id)
    return qy.one_or_none()

