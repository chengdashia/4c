import os

from fastapi import APIRouter, File, Form, UploadFile
import cv2

from app.http import UploadFileStorage, error_response, success_response, validate_upload_file
from app.utils.image_processing import (
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

router = APIRouter(tags=["detections"])


@router.post("/detections/yolo26")
def detect_yolo26(
    file: UploadFile | None = File(None),
    conf_thres: float = Form(0.25),
    iou_thres: float = Form(0.45),
):
    upload_error = validate_upload_file(file)
    if upload_error:
        return upload_error

    upload_path = save_upload_file(UploadFileStorage(file), upload_folder)
    media_type = infer_media_type(file.filename, file.content_type)

    if media_type == "video":
        return _handle_video(upload_path, conf_thres, iou_thres, app_root)

    image = cv2.imread(upload_path)
    if image is None:
        return error_response("上传图片读取失败", 400)
    result = detect_yolo26_raw(image, conf_thres=conf_thres, iou_thres=iou_thres)

    result_filename = f"detected_{os.path.basename(upload_path)}"
    result_path = save_cv2_image(result["image"], result_folder, result_filename)

    return success_response(
        "目标检测成功",
        {
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
    )


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
        return error_response("上传视频读取失败", 400)

    return success_response(
        "视频目标检测成功",
        {
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
    )
