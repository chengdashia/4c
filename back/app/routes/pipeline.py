import os

import cv2
from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource

from app.utils.image_codec import decode_base64_to_image
from app.utils.image_processing import allowed_file, allowed_mime_type, save_cv2_image, save_upload_file
from app.utils.model_loader import detect_yolo26, enhance_low_light
from app.utils.path_utils import convert_to_url_path

app_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
upload_folder = os.path.join(app_root, "static", "images", "pipeline", "uploads")
enhanced_folder = os.path.join(app_root, "static", "images", "pipeline", "enhanced")
result_folder = os.path.join(app_root, "static", "images", "pipeline", "results")

pipeline_file_ns = Namespace("pipeline_file", description="enhance then detect pipeline api")


def _average_confidence(detections):
    if not detections:
        return 0
    return round(sum(item["score"] for item in detections) / len(detections), 4)


def _extract_total_timing(timing):
    if isinstance(timing, dict):
        return round(float(timing.get("total_ms", 0)), 2)
    return round(float(timing), 2)


def _scene_analysis(detections):
    if not detections:
        return ["当前未识别到目标，请调整图片内容或检测阈值后重试。"]

    labels = [item["class_name"] for item in detections]
    unique_labels = sorted(set(labels))
    insights = [f"共识别到 {len(detections)} 个目标，涉及 {len(unique_labels)} 类场景对象。"]

    if "person" in labels:
        insights.append("画面中存在行人目标，建议重点关注近距离通行风险。")
    if "car" in labels or "bus" in labels or "truck" in labels:
        insights.append("检测到机动车目标，增强后有助于观察车道中的主要交通参与者。")
    if len(insights) == 1:
        insights.append("当前结果以常见道路目标为主，可继续结合阈值微调提升检出稳定性。")

    return insights


@pipeline_file_ns.route("/process", methods=["POST"])
class VisionPipelineResource(Resource):
    @pipeline_file_ns.doc(
        description="上传图片后先做低照度增强，再进行目标检测，并返回全过程结果",
        responses={200: "处理成功", 400: "无效输入", 500: "服务器内部错误"},
    )
    def post(self):
        if "file" not in request.files:
            return make_response(jsonify({"code": 400, "message": "没有文件被上传"}), 400)

        file = request.files["file"]
        if file.filename == "":
            return make_response(jsonify({"code": 400, "message": "没有选择文件"}), 400)
        if not allowed_file(file.filename):
            return make_response(jsonify({"code": 400, "message": "不允许的文件类型"}), 400)
        if not allowed_mime_type(file.content_type):
            return make_response(jsonify({"code": 400, "message": "不允许的MIME类型"}), 400)

        conf_thres = float(request.form.get("conf_thres", 0.25))
        iou_thres = float(request.form.get("iou_thres", 0.45))

        upload_path = save_upload_file(file, upload_folder)
        image = cv2.imread(upload_path)
        if image is None:
            return make_response(jsonify({"code": 400, "message": "上传图片读取失败"}), 400)

        enhance_result = enhance_low_light(image)
        enhanced_image = decode_base64_to_image(enhance_result["image_base64"])
        enhanced_filename = f"enhanced_{os.path.basename(upload_path)}"
        enhanced_path = save_cv2_image(enhanced_image, enhanced_folder, enhanced_filename)

        detect_result = detect_yolo26(enhanced_image, conf_thres=conf_thres, iou_thres=iou_thres)
        detected_image = decode_base64_to_image(detect_result["image_base64"])
        result_filename = f"detected_{os.path.basename(upload_path)}"
        result_path = save_cv2_image(detected_image, result_folder, result_filename)

        detections = detect_result["detections"]
        enhance_total_ms = _extract_total_timing(enhance_result["timing_ms"])
        detect_total_ms = _extract_total_timing(detect_result["timing_ms"])
        total_timing_ms = round(enhance_total_ms + detect_total_ms, 2)

        return make_response(
            jsonify(
                {
                    "code": 200,
                    "message": "图像增强与目标检测成功",
                    "data": {
                        "upload_image": convert_to_url_path(upload_path, app_root),
                        "enhanced_image": convert_to_url_path(enhanced_path, app_root),
                        "result_image": convert_to_url_path(result_path, app_root),
                        "detections": detections,
                        "count": detect_result["count"],
                        "image_shape": enhance_result["image_shape"],
                        "thresholds": detect_result["thresholds"],
                        "timing_ms": {
                            "enhance": {
                                **enhance_result["timing_ms"],
                                "total_ms": enhance_total_ms,
                            },
                            "detect": {
                                **detect_result["timing_ms"],
                                "total_ms": detect_total_ms,
                            },
                            "total": total_timing_ms,
                        },
                        "summary": {
                            "target_count": detect_result["count"],
                            "avg_confidence": _average_confidence(detections),
                            "latency_ms": total_timing_ms,
                        },
                        "scene_analysis": _scene_analysis(detections),
                    },
                }
            ),
            200,
        )
