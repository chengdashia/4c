import os

from flask import jsonify, make_response, request
from flask_restx import Namespace, Resource
import cv2

from app.utils.image_processing import (
    allowed_file,
    allowed_mime_type,
    infer_media_type,
    save_cv2_image,
    save_upload_file,
)
from app.utils.model_loader import enhance_low_light_raw, warmup_low_light_model
from app.utils.path_utils import convert_to_url_path
from app.utils.video_processing import (
    build_output_video_path,
    create_video_writer,
    get_video_metadata,
    open_video_capture,
    process_video_in_parallel,
)

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
        media_type = infer_media_type(file.filename, file.content_type)

        if media_type == "video":
            return self._handle_video(upload_path, app_root)

        image = cv2.imread(upload_path)
        if image is None:
            return make_response(jsonify({"code": 400, "message": "上传图片读取失败"}), 400)
        result = enhance_low_light_raw(image)

        result_filename = f"enhanced_{os.path.basename(upload_path)}"
        result_path = save_cv2_image(result["image"], result_folder, result_filename)

        return make_response(
            jsonify(
                {
                    "code": 200,
                    "message": "图像增强成功",
                    "data": {
                        "media_type": "image",
                        "upload_image": convert_to_url_path(upload_path, app_root),
                        "upload_media": convert_to_url_path(upload_path, app_root),
                        "result_image": convert_to_url_path(result_path, app_root),
                        "result_media": convert_to_url_path(result_path, app_root),
                        "timing_ms": result["timing_ms"],
                        "image_shape": result["image_shape"],
                    },
                }
            ),
            200,
        )

    @staticmethod
    def _handle_video(upload_path, app_root):
        capture = open_video_capture(upload_path)
        metadata = get_video_metadata(capture)
        result_prefix = f"enhanced_{os.path.splitext(os.path.basename(upload_path))[0]}"
        result_path = build_output_video_path(result_folder, result_prefix)
        writer, codec = create_video_writer(
            result_path,
            metadata["width"],
            metadata["height"],
            metadata["fps"],
        )

        total_timing_ms = 0.0
        frames_processed = 0

        try:
            def process_frame(_frame_index, frame):
                return enhance_low_light_raw(frame)

            def handle_result(result):
                nonlocal total_timing_ms, frames_processed
                writer.write(result["image"])
                total_timing_ms += float(result["timing_ms"]["total_ms"])
                frames_processed += 1

            parallel_stats = process_video_in_parallel(
                capture,
                process_frame,
                handle_result,
                warmup_fn=warmup_low_light_model,
            )
        finally:
            capture.release()
            writer.release()

        if frames_processed == 0:
            return make_response(jsonify({"code": 400, "message": "上传视频读取失败"}), 400)

        return make_response(
            jsonify(
                {
                    "code": 200,
                    "message": "视频增强成功",
                    "data": {
                        "media_type": "video",
                        "upload_image": convert_to_url_path(upload_path, app_root),
                        "upload_media": convert_to_url_path(upload_path, app_root),
                        "result_image": convert_to_url_path(result_path, app_root),
                        "result_media": convert_to_url_path(result_path, app_root),
                        "video_meta": {
                            **metadata,
                            "processed_frames": frames_processed,
                            "codec": codec,
                        },
                        "timing_ms": {
                            "total_ms": round(total_timing_ms, 2),
                            "avg_frame_ms": round(total_timing_ms / frames_processed, 2),
                            "wall_ms": parallel_stats["elapsed_ms"],
                            "workers": parallel_stats["workers"],
                            "warmup_workers": parallel_stats["warmup_workers"],
                        },
                    },
                }
            ),
            200,
        )
