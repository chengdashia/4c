import os


def convert_to_url_path(file_path, app_root):
    relative_path = os.path.relpath(file_path, app_root)
    url_path = relative_path.replace(os.sep, "/")
    if not url_path.startswith("/"):
        url_path = "/" + url_path
    return url_path
