import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
import cv2

from app.utils.image_processing import allowed_file, allowed_mime_type, save_cv2_image, save_upload_file
from app.utils.model_loader import detect_yolo26
from app.utils.path_utils import convert_to_url_path
from app.utils.image_codec import decode_base64_to_image

app_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
upload_folder = os.path.join(app_root, "static", "images", "yolo26_bdd100k", "uploads")
result_folder = os.path.join(app_root, "static", "images", "yolo26_bdd100k", "results")

yolo26_file_ns = Namespace("yolo26_bdd100k_file", description="yolo26 bdd100k file detection api")


@yolo26_file_ns.route("/detect", methods=["POST"])
class Yolo26DetectResource(Resource):
    @yolo26_file_ns.doc(
        description="上传图片文件并返回检测结果图片地址",
        responses={200: "检测成功", 400: "无效输入", 500: "服务器内部错误"},
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
        result = detect_yolo26(image, conf_thres=conf_thres, iou_thres=iou_thres)

        result_filename = f"detected_{os.path.basename(upload_path)}"
        result_image = decode_base64_to_image(result["image_base64"])
        result_path = save_cv2_image(result_image, result_folder, result_filename)

        return make_response(
            jsonify(
                {
                    "code": 200,
                    "message": "目标检测成功",
                    "data": {
                        "upload_image": convert_to_url_path(upload_path, app_root),
                        "result_image": convert_to_url_path(result_path, app_root),
                        "detections": result["detections"],
                        "count": result["count"],
                        "timing_ms": result["timing_ms"],
                        "thresholds": result["thresholds"],
                    },
                }
            ),
            200,
        )
