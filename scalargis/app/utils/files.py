import os

from werkzeug.utils import safe_join


def contained_path(base, *parts):
    """Returns base joined with parts, or None when base is empty or the result leaves base."""
    if not base:
        return None
    return safe_join(base, *[p for p in parts if p])


def bare_filename(name):
    """Returns the last part of a client file name, or None for an empty, '.' or '..' name."""
    if not isinstance(name, str):
        return None
    name = name.replace('\\', '/').rsplit('/', 1)[-1]
    if name.strip() in ('', '.', '..'):
        return None
    return name


def notifications_folder():
    """Returns the folder of the contact message attachments, or None when no candidate exists."""
    from app.utils.settings import get_config_value

    folder = get_config_value('EMAIL_NOTIFICATIONS_FOLDER')
    if folder and os.path.exists(folder):
        return folder
    for key in ('APP_UPLOADS', 'APP_TMP_DIR'):
        parent = get_config_value(key)
        if parent and os.path.exists(parent):
            return os.path.join(parent, 'notifications')
    return None
