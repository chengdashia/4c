import logging
import os
import platform
import threading

import onnxruntime
from app.models.c2pnet.c2pnet_onnx import C2PNetONNX
from app.models.derain.attentive_gan_derainnet_onnx import AttentiveGANDerainNetONNX
from app.models.lightweight_low_light.lyt_net_onnx import LYTNetONNX
from app.models.low_light.diffusion_low_light import DiffusionLowLight
from app.models.yolo26_bdd100k.yolo26_onnx import YOLO26ONNX
from app.utils.image_processing import cv2_to_base64, detections_to_dict

logger = logging.getLogger(__name__)

_low_light_model = None
_yolo26_model = None
_c2pnet_model = None
_lightweight_low_light_model = None
_derain_model = None
_low_light_loaded = False
_yolo26_loaded = False
_c2pnet_loaded = False
_lightweight_low_light_loaded = False
_derain_loaded = False
_thread_local = threading.local()


def select_torch_device():
    try:
        import torch
    except ImportError:
        return "cpu"

    if torch.cuda.is_available():
        return torch.device("cuda")

    mps = getattr(getattr(torch, "backends", None), "mps", None)
    if mps is not None and mps.is_available():
        return torch.device("mps")

    return torch.device("cpu")


def get_ort_execution_providers():
    available = set(onnxruntime.get_available_providers())
    preferred = []
    system = platform.system()
    coreml_disabled = str(os.getenv("ENABLE_COREML", "")).strip().lower() in {"0", "false", "no"}
    allow_coreml = system == "Darwin" and not coreml_disabled

    if system == "Windows":
        for provider in (
            "CUDAExecutionProvider",
            "DmlExecutionProvider",
            "CPUExecutionProvider",
        ):
            if provider in available:
                preferred.append(provider)
        return preferred or ["CPUExecutionProvider"]

    if allow_coreml and "CoreMLExecutionProvider" in available:
        preferred.append("CoreMLExecutionProvider")

    for provider in (
        "CUDAExecutionProvider",
        "CPUExecutionProvider",
    ):
        if provider in available:
            preferred.append(provider)

    if not preferred:
        preferred = ["CPUExecutionProvider"]

    return preferred


def is_gpu_accelerated():
    providers = get_ort_execution_providers()
    return any(provider != "CPUExecutionProvider" for provider in providers)


def get_acceleration_status():
    return {
        "onnxruntime_providers": get_ort_execution_providers(),
        "torch_device": str(select_torch_device()),
    }


def get_session_thread_config():
    if is_gpu_accelerated():
        return {"intra_op_num_threads": 0, "inter_op_num_threads": 0}

    # For CPU parallel video processing, keep each session single-threaded to avoid oversubscription.
    return {"intra_op_num_threads": 1, "inter_op_num_threads": 1}


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
    global _low_light_model, _low_light_loaded
    if getattr(_thread_local, "low_light_model", None) is None:
        model_path = get_static_model_path("low_light", "diffusion_low_light_1x3x384x640.onnx")
        check_model_file(model_path)
        _thread_local.low_light_model = DiffusionLowLight(
            model_path,
            providers=get_ort_execution_providers(),
            **get_session_thread_config(),
        )
        _low_light_model = _thread_local.low_light_model
        _low_light_loaded = True
        logger.info("低照度增强模型加载完成: %s", model_path)
    return _thread_local.low_light_model


def load_yolo26_model(conf_thres=0.25, iou_thres=0.45):
    global _yolo26_model, _yolo26_loaded
    if getattr(_thread_local, "yolo26_model", None) is None:
        model_path = get_static_model_path("yolo26_bdd100k", "my_yolo26.onnx")
        check_model_file(model_path)
        _thread_local.yolo26_model = YOLO26ONNX(
            model_path,
            conf_thres=conf_thres,
            iou_thres=iou_thres,
            providers=get_ort_execution_providers(),
            **get_session_thread_config(),
        )
        _yolo26_model = _thread_local.yolo26_model
        _yolo26_loaded = True
        logger.info("YOLO26 模型加载完成: %s", model_path)
    _thread_local.yolo26_model.conf_thres = conf_thres
    _thread_local.yolo26_model.iou_thres = iou_thres
    return _thread_local.yolo26_model


def load_c2pnet_model():
    global _c2pnet_model, _c2pnet_loaded
    if getattr(_thread_local, "c2pnet_model", None) is None:
        model_path = get_static_model_path("c2p", "c2pnet_outdoor_360x640.onnx")
        check_model_file(model_path)
        _thread_local.c2pnet_model = C2PNetONNX(
            model_path,
            providers=get_ort_execution_providers(),
            **get_session_thread_config(),
        )
        _c2pnet_model = _thread_local.c2pnet_model
        _c2pnet_loaded = True
        logger.info("C2PNet 去雾模型加载完成: %s", model_path)
    return _thread_local.c2pnet_model


def load_lightweight_low_light_model():
    global _lightweight_low_light_model, _lightweight_low_light_loaded
    if getattr(_thread_local, "lightweight_low_light_model", None) is None:
        model_path = get_static_model_path("low_light", "lyt_net_lolv2_real_640x360.onnx")
        check_model_file(model_path)
        _thread_local.lightweight_low_light_model = LYTNetONNX(
            model_path,
            providers=get_ort_execution_providers(),
            **get_session_thread_config(),
        )
        _lightweight_low_light_model = _thread_local.lightweight_low_light_model
        _lightweight_low_light_loaded = True
        logger.info("轻量化低照度增强模型加载完成: %s", model_path)
    return _thread_local.lightweight_low_light_model


def load_derain_model():
    global _derain_model, _derain_loaded
    if getattr(_thread_local, "derain_model", None) is None:
        model_path = get_static_model_path("derain", "attentive_gan_derainnet_360x640.onnx")
        check_model_file(model_path)
        _thread_local.derain_model = AttentiveGANDerainNetONNX(
            model_path,
            providers=get_ort_execution_providers(),
            **get_session_thread_config(),
        )
        _derain_model = _thread_local.derain_model
        _derain_loaded = True
        logger.info("Attentive GAN 图像去雨模型加载完成: %s", model_path)
    return _thread_local.derain_model


def warmup_low_light_model():
    load_low_light_model()
    return threading.get_ident()


def warmup_yolo26_model(conf_thres=0.25, iou_thres=0.45):
    load_yolo26_model(conf_thres=conf_thres, iou_thres=iou_thres)
    return threading.get_ident()


def warmup_c2pnet_model():
    load_c2pnet_model()
    return threading.get_ident()


def warmup_lightweight_low_light_model():
    load_lightweight_low_light_model()
    return threading.get_ident()


def warmup_derain_model():
    load_derain_model()
    return threading.get_ident()


def enhance_low_light(image):
    result = enhance_low_light_raw(image)
    return {
        **result,
        "image_base64": cv2_to_base64(result["image"]),
    }


def enhance_low_light_raw(image):
    model = load_low_light_model()
    output_image, timing = model.predict(image, return_timing=True)
    return {
        "image": output_image,
        "timing_ms": timing,
        "image_shape": {
            "height": int(output_image.shape[0]),
            "width": int(output_image.shape[1]),
            "channels": int(output_image.shape[2]),
        },
    }


def enhance_lightweight_low_light(image):
    result = enhance_lightweight_low_light_raw(image)
    return {
        **result,
        "image_base64": cv2_to_base64(result["image"]),
    }


def enhance_lightweight_low_light_raw(image):
    model = load_lightweight_low_light_model()
    output_image, timing = model.predict(image, return_timing=True)
    return {
        "image": output_image,
        "timing_ms": timing,
        "image_shape": {
            "height": int(output_image.shape[0]),
            "width": int(output_image.shape[1]),
            "channels": int(output_image.shape[2]),
        },
    }


def enhance_low_light_batch(images):
    model = load_low_light_model()
    output_images, timing = model.predict_batch(images, return_timing=True)
    return {
        "images": output_images,
        "timing_ms": timing,
        "batch_supported": bool(timing.get("batch_supported", False)),
        "batch_size": int(timing.get("batch_size", len(images))),
    }


def low_light_batch_capability():
    model = load_low_light_model()
    return {
        "supported": model.supports_batch(),
        "max_batch_size": model.max_batch_size(),
        "input_shape": list(model.input_shape),
    }


def dehaze_c2pnet(image):
    result = dehaze_c2pnet_raw(image)
    return {
        **result,
        "image_base64": cv2_to_base64(result["image"]),
    }


def dehaze_c2pnet_raw(image):
    model = load_c2pnet_model()
    output_image, timing = model.predict(image, return_timing=True)
    return {
        "image": output_image,
        "timing_ms": timing,
        "image_shape": {
            "height": int(output_image.shape[0]),
            "width": int(output_image.shape[1]),
            "channels": int(output_image.shape[2]),
        },
    }


def derain_attentive_gan(image):
    result = derain_attentive_gan_raw(image)
    return {
        **result,
        "image_base64": cv2_to_base64(result["image"]),
    }


def derain_attentive_gan_raw(image):
    model = load_derain_model()
    output_image, timing = model.predict(image, return_timing=True)
    return {
        "image": output_image,
        "timing_ms": timing,
        "image_shape": {
            "height": int(output_image.shape[0]),
            "width": int(output_image.shape[1]),
            "channels": int(output_image.shape[2]),
        },
    }


def detect_yolo26(image, conf_thres=0.25, iou_thres=0.45):
    result = detect_yolo26_raw(image, conf_thres=conf_thres, iou_thres=iou_thres)
    return {
        **result,
        "image_base64": cv2_to_base64(result["image"]),
    }


def detect_yolo26_raw(image, conf_thres=0.25, iou_thres=0.45):
    model = load_yolo26_model(conf_thres=conf_thres, iou_thres=iou_thres)
    output_image, detections, timing = model.predict(image, return_timing=True)
    return {
        "image": output_image,
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
    yolo_path = get_static_model_path("yolo26_bdd100k", "my_yolo26.onnx")
    c2pnet_path = get_static_model_path("c2p", "c2pnet_outdoor_360x640.onnx")
    lightweight_low_light_path = get_static_model_path("low_light", "lyt_net_lolv2_real_640x360.onnx")
    derain_path = get_static_model_path("derain", "attentive_gan_derainnet_360x640.onnx")
    return [
        {
            "id": "low_light",
            "name": "Diffusion Low Light",
            "ready": os.path.exists(low_light_path),
            "loaded": _low_light_loaded,
            "model_path": low_light_path,
            "providers": get_ort_execution_providers(),
            "batch": low_light_batch_capability() if _low_light_loaded else None,
        },
        {
            "id": "yolo26_bdd100k",
            "name": "YOLO26 BDD100K",
            "ready": os.path.exists(yolo_path),
            "loaded": _yolo26_loaded,
            "model_path": yolo_path,
            "providers": get_ort_execution_providers(),
        },
        {
            "id": "c2pnet",
            "name": "C2PNet Dehaze",
            "ready": os.path.exists(c2pnet_path),
            "loaded": _c2pnet_loaded,
            "model_path": c2pnet_path,
            "providers": get_ort_execution_providers(),
        },
        {
            "id": "lightweight_low_light",
            "name": "Lightweight Low Light",
            "ready": os.path.exists(lightweight_low_light_path),
            "loaded": _lightweight_low_light_loaded,
            "model_path": lightweight_low_light_path,
            "providers": get_ort_execution_providers(),
        },
        {
            "id": "attentive_gan_derain",
            "name": "Attentive GAN Derain",
            "ready": os.path.exists(derain_path),
            "loaded": _derain_loaded,
            "model_path": derain_path,
            "providers": get_ort_execution_providers(),
        },
    ]
