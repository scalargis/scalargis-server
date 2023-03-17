import os

def to_bool(bool_str):
    """Parse the string and return the boolean value encoded or raise an exception"""
    if isinstance(bool_str, str):
        if bool_str.lower() in ['true', 't', '1']: return True
        elif bool_str.lower() in ['false', 'f', '0']: return False

    return None


def get_file_path(base_path, path, filename):
    filepath = None
    if os.path.isfile(os.path.abspath(filename)):
        filepath = os.path.abspath(filename)
    elif base_path and os.path.isfile(os.path.join(base_path, filename)):
        filepath = os.path.join(base_path, filename)
    elif base_path and path and os.path.isfile(os.path.join(base_path, path, filename)):
        filepath = os.path.join(base_path, path, filename)

    return filepath
