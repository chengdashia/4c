import logging
import os

from app.models.low_light.diffusion_low_light import DiffusionLowLight
from app.models.yolo26_bdd100k.yolo26_onnx import YOLO26ONNX
from app.utils.image_processing import cv2_to_base64, detections_to_dict

logger = logging.getLogger(__name__)

_low_light_model = None
_yolo26_model = None


def check_model_file(model_path):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"模型文件不存在: {model_path}")
    if os.path.getsize(model_path) == 0:
        raise ValueError(f"模型文件为空: {model_path}")


def get_app_root():
    return os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def get_static_model_path(*parts):
    return os.path.join(get_app_root(), "static", "models", *parts)


def load_low_light_model():
    global _low_light_model
    if _low_light_model is None:
        model_path = get_static_model_path("low_light", "diffusion_low_light_1x3x384x640.onnx")
        check_model_file(model_path)
        _low_light_model = DiffusionLowLight(model_path)
        logger.info("低照度增强模型加载完成: %s", model_path)
    return _low_light_model


def load_yolo26_model(conf_thres=0.25, iou_thres=0.45):
    global _yolo26_model
    if _yolo26_model is None:
        model_path = get_static_model_path("yolo26_bdd100k", "yolo26s.onnx")
        check_model_file(model_path)
        _yolo26_model = YOLO26ONNX(model_path, conf_thres=conf_thres, iou_thres=iou_thres)
        logger.info("YOLO26 模型加载完成: %s", model_path)
    _yolo26_model.conf_thres = conf_thres
    _yolo26_model.iou_thres = iou_thres
    return _yolo26_model


def enhance_low_light(image):
    model = load_low_light_model()
    output_image, timing = model.predict(image, return_timing=True)
    return {
        "image_base64": cv2_to_base64(output_image),
        "timing_ms": timing,
        "image_shape": {
            "height": int(output_image.shape[0]),
            "width": int(output_image.shape[1]),
            "channels": int(output_image.shape[2]),
        },
    }


def detect_yolo26(image, conf_thres=0.25, iou_thres=0.45):
    model = load_yolo26_model(conf_thres=conf_thres, iou_thres=iou_thres)
    output_image, detections, timing = model.predict(image, return_timing=True)
    return {
        "image_base64": cv2_to_base64(output_image),
        "detections": detections_to_dict(detections, model.names),
        "count": int(len(detections)),
        "timing_ms": timing,
        "thresholds": {
            "conf_thres": conf_thres,
            "iou_thres": iou_thres,
        },
    }


def get_model_status():
    low_light_path = get_static_model_path("low_light", "diffusion_low_light_1x3x384x640.onnx")
    yolo_path = get_static_model_path("yolo26_bdd100k", "yolo26s.onnx")
    return [
        {
            "id": "low_light",
            "name": "Diffusion Low Light",
            "ready": os.path.exists(low_light_path),
            "loaded": _low_light_model is not None,
            "model_path": low_light_path,
        },
        {
            "id": "yolo26_bdd100k",
            "name": "YOLO26 BDD100K",
            "ready": os.path.exists(yolo_path),
            "loaded": _yolo26_model is not None,
            "model_path": yolo_path,
        },
    ]
