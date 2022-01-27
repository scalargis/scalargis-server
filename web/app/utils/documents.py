import os
import uuid
from flask import url_for


def path_hierarchy(dir_endpoint, file_endpoint, root, folder, base_path, path, files_filter, files_exclude, dirs_exclude, recursive):

    name = os.path.basename(path)

    hierarchy = {
        'name': name,
        'type': ''
    }

    if os.path.isdir(path):
        try:
            hierarchy['type'] = 'folder'
            hierarchy['folder_id'] = str(uuid.uuid4().hex)
            hierarchy['resource_url'] = url_for(dir_endpoint, folder=folder, path=base_path).replace(r'//', r'/')
            hierarchy['children'] = [
                path_hierarchy(dir_endpoint, file_endpoint, root, folder, ''.join([base_path, r'/',  contents]).replace(r'//',r'/'), os.path.join(path, contents), files_filter, files_exclude, dirs_exclude, recursive)
                for contents in os.listdir(path)
                if (os.path.isdir(os.path.join(path, contents)) and not contents.lower() in tuple(dirs_exclude) and recursive) or
                (not os.path.isdir(os.path.join(path, contents)) and
                 (len(files_filter) == 0 or contents.lower().endswith(tuple(files_filter))) and
                 (len(files_exclude) == 0 or not contents.lower().endswith(tuple(files_exclude)))
                 )
            ]
        except:
            pass
    else:
        try:
            hierarchy['type'] = 'file'
            hierarchy['resource_url'] = url_for(file_endpoint, folder=folder,
                                       path=base_path.encode('utf8', 'surrogateescape')).replace(r'//', r'/')
        except:
            pass

    return hierarchy