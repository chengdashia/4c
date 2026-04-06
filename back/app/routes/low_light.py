import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
import cv2

from app.utils.image_processing import allowed_file, allowed_mime_type, save_cv2_image, save_upload_file
from app.utils.model_loader import enhance_low_light
from app.utils.path_utils import convert_to_url_path
from app.utils.image_codec import decode_base64_to_image

app_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
upload_folder = os.path.join(app_root, "static", "images", "low_light", "uploads")
result_folder = os.path.join(app_root, "static", "images", "low_light", "results")

low_light_file_ns = Namespace("low_light_file", description="low light enhancement file api")


@low_light_file_ns.route("/enhance", methods=["POST"])
class LowLightEnhanceResource(Resource):
    @low_light_file_ns.doc(
        description="上传图片文件并返回增强结果图片地址",
        responses={200: "图像增强成功", 400: "无效输入", 500: "服务器内部错误"},
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

        upload_path = save_upload_file(file, upload_folder)
        image = cv2.imread(upload_path)
        if image is None:
            return make_response(jsonify({"code": 400, "message": "上传图片读取失败"}), 400)
        result = enhance_low_light(image)

        result_filename = f"enhanced_{os.path.basename(upload_path)}"
        result_image = decode_base64_to_image(result["image_base64"])
        result_path = save_cv2_image(result_image, result_folder, result_filename)

        return make_response(
            jsonify(
                {
                    "code": 200,
                    "message": "图像增强成功",
                    "data": {
                        "upload_image": convert_to_url_path(upload_path, app_root),
                        "result_image": convert_to_url_path(result_path, app_root),
                        "timing_ms": result["timing_ms"],
                        "image_shape": result["image_shape"],
                    },
                }
            ),
            200,
        )
