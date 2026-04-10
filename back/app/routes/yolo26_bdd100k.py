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
from app.utils.model_loader import detect_yolo26_raw, warmup_yolo26_model
from app.utils.path_utils import convert_to_url_path
from app.utils.video_processing import (
    build_output_video_path,
    create_video_writer,
    get_video_metadata,
    open_video_capture,
    process_video_in_parallel,
)

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
        media_type = infer_media_type(file.filename, file.content_type)

        if media_type == "video":
            return self._handle_video(upload_path, conf_thres, iou_thres, app_root)

        image = cv2.imread(upload_path)
        if image is None:
            return make_response(jsonify({"code": 400, "message": "上传图片读取失败"}), 400)
        result = detect_yolo26_raw(image, conf_thres=conf_thres, iou_thres=iou_thres)

        result_filename = f"detected_{os.path.basename(upload_path)}"
        result_path = save_cv2_image(result["image"], result_folder, result_filename)

        return make_response(
            jsonify(
                {
                    "code": 200,
                    "message": "目标检测成功",
                    "data": {
                        "media_type": "image",
                        "upload_image": convert_to_url_path(upload_path, app_root),
                        "upload_media": convert_to_url_path(upload_path, app_root),
                        "result_image": convert_to_url_path(result_path, app_root),
                        "result_media": convert_to_url_path(result_path, app_root),
                        "detections": result["detections"],
                        "count": result["count"],
                        "timing_ms": result["timing_ms"],
                        "thresholds": result["thresholds"],
                    },
                }
            ),
            200,
        )

    @staticmethod
    def _handle_video(upload_path, conf_thres, iou_thres, app_root):
        capture = open_video_capture(upload_path)
        metadata = get_video_metadata(capture)
        result_prefix = f"detected_{os.path.splitext(os.path.basename(upload_path))[0]}"
        result_path = build_output_video_path(result_folder, result_prefix)
        writer, codec = create_video_writer(
            result_path,
            metadata["width"],
            metadata["height"],
            metadata["fps"],
        )

        total_timing_ms = 0.0
        frames_processed = 0
        total_detections = 0
        max_frame_detections = 0
        last_detections = []

        try:
            def process_frame(_frame_index, frame):
                return detect_yolo26_raw(frame, conf_thres=conf_thres, iou_thres=iou_thres)

            def handle_result(result):
                nonlocal total_timing_ms, frames_processed, total_detections, max_frame_detections, last_detections
                writer.write(result["image"])
                total_timing_ms += float(result["timing_ms"]["total_ms"])
                frames_processed += 1
                total_detections += int(result["count"])
                max_frame_detections = max(max_frame_detections, int(result["count"]))
                if result["detections"]:
                    last_detections = result["detections"]

            parallel_stats = process_video_in_parallel(
                capture,
                process_frame,
                handle_result,
                warmup_fn=lambda: warmup_yolo26_model(
                    conf_thres=conf_thres,
                    iou_thres=iou_thres,
                ),
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
                    "message": "视频目标检测成功",
                    "data": {
                        "media_type": "video",
                        "upload_image": convert_to_url_path(upload_path, app_root),
                        "upload_media": convert_to_url_path(upload_path, app_root),
                        "result_image": convert_to_url_path(result_path, app_root),
                        "result_media": convert_to_url_path(result_path, app_root),
                        "detections": last_detections,
                        "count": len(last_detections),
                        "thresholds": {
                            "conf_thres": conf_thres,
                            "iou_thres": iou_thres,
                        },
                        "timing_ms": {
                            "total_ms": round(total_timing_ms, 2),
                            "avg_frame_ms": round(total_timing_ms / frames_processed, 2),
                            "wall_ms": parallel_stats["elapsed_ms"],
                            "workers": parallel_stats["workers"],
                            "warmup_workers": parallel_stats["warmup_workers"],
                        },
                        "video_meta": {
                            **metadata,
                            "processed_frames": frames_processed,
                            "codec": codec,
                        },
                        "summary": {
                            "total_detections": total_detections,
                            "max_frame_detections": max_frame_detections,
                            "avg_detections_per_frame": round(total_detections / frames_processed, 3),
                            "parallel_workers": parallel_stats["workers"],
                        },
                    },
                }
            ),
            200,
        )
