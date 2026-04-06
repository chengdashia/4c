import base64
import binascii
import io
import os
import uuid
from datetime import datetime

import cv2
import numpy as np
from flask import Request
from PIL import Image
from werkzeug.utils import secure_filename


class ImageDecodeError(ValueError):
    pass


def _decode_image_bytes(image_bytes):
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        raise ImageDecodeError("无法解析图片数据")
    return image


def decode_request_image(request: Request):
    if "file" in request.files:
        file = request.files["file"]
        if not file.filename:
            raise ImageDecodeError("上传文件名为空")
        return _decode_image_bytes(file.read())

    payload = request.get_json(silent=True) or {}
    image_base64 = payload.get("image_base64")
    if not image_base64:
        raise ImageDecodeError("请提供 file 文件或 image_base64 字段")

    if "," in image_base64:
        image_base64 = image_base64.split(",", 1)[1]

    try:
        image_bytes = base64.b64decode(image_base64, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ImageDecodeError("image_base64 不是合法的 Base64 图片") from exc

    return _decode_image_bytes(image_bytes)


def encode_image_to_base64(image):
    success, encoded = cv2.imencode(".jpg", image)
    if not success:
        raise ValueError("结果图片编码失败")
    return base64.b64encode(encoded.tobytes()).decode("utf-8")


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/jpg"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def allowed_mime_type(mime_type):
    return mime_type in ALLOWED_MIME_TYPES


def decode_base64_to_image(base64_data):
    if "," in base64_data:
        base64_data = base64_data.split(",", 1)[1]
    try:
        image_bytes = base64.b64decode(base64_data, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ImageDecodeError("image_base64 不是合法的 Base64 图片") from exc
    return _decode_image_bytes(image_bytes)


def cv2_to_base64(image):
    return encode_image_to_base64(image)


def detections_to_dict(detections, class_names):
    results = []
    for x1, y1, x2, y2, score, class_id in detections:
        class_id = int(class_id)
        results.append(
            {
                "class_id": class_id,
                "class_name": class_names.get(class_id, str(class_id)),
                "score": float(score),
                "bbox": {
                    "x1": float(x1),
                    "y1": float(y1),
                    "x2": float(x2),
                    "y2": float(y2),
                },
            }
        )
    return results


def create_unique_filename(filename):
    filename = secure_filename(filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    name, ext = os.path.splitext(filename)
    safe_ext = ext if ext else ".jpg"
    return f"{name}_{timestamp}_{unique_id}{safe_ext}"


def save_upload_file(file_storage, save_dir):
    os.makedirs(save_dir, exist_ok=True)
    filename = create_unique_filename(file_storage.filename or "upload.jpg")
    save_path = os.path.join(save_dir, filename)
    file_storage.save(save_path)
    return save_path


def save_cv2_image(image, save_dir, filename):
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, filename)
    success = cv2.imwrite(save_path, image)
    if not success:
        raise ValueError("结果图片保存失败")
    return save_path
