import os
import shutil

from fastapi import UploadFile
from starlette.responses import JSONResponse

from app.utils.image_processing import allowed_file, allowed_mime_type


def success_response(message, data=None):
    payload = {"code": 200, "message": message}
    if data is not None:
        payload["data"] = data
    return payload


def error_response(message, status_code=400, code=None):
    return JSONResponse(
        status_code=status_code,
        content={"code": code or status_code, "message": message},
    )


class UploadFileStorage:
    def __init__(self, upload_file: UploadFile):
        self.upload_file = upload_file
        self.filename = upload_file.filename
        self.content_type = upload_file.content_type

    def save(self, path):
        self.upload_file.file.seek(0)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as output_file:
            shutil.copyfileobj(self.upload_file.file, output_file)
        self.upload_file.file.seek(0)


def validate_upload_file(file: UploadFile | None):
    if file is None:
        return error_response("没有文件被上传", 400)
    if file.filename == "":
        return error_response("没有选择文件", 400)
    if not allowed_file(file.filename or ""):
        return error_response("不允许的文件类型", 400)
    if not allowed_mime_type(file.content_type or ""):
        return error_response("不允许的MIME类型", 400)
    return None
