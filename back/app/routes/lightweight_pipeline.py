import os

import cv2
from fastapi import APIRouter, File, Form, UploadFile

from app.http import UploadFileStorage, error_response, success_response, validate_upload_file
from app.utils.image_processing import infer_media_type, save_cv2_image, save_upload_file
from app.utils.model_loader import (
    detect_yolo26_raw,
    enhance_lightweight_low_light_raw,
    warmup_lightweight_low_light_model,
    warmup_yolo26_model,
)
from app.utils.path_utils import convert_to_url_path
from app.utils.video_processing import (
    build_output_video_path,
    create_video_writer,
    get_video_metadata,
    open_video_capture,
    process_video_in_parallel,
)

app_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
upload_folder = os.path.join(app_root, "static", "images", "lightweight_pipeline", "uploads")
enhanced_folder = os.path.join(app_root, "static", "images", "lightweight_pipeline", "enhanced")
result_folder = os.path.join(app_root, "static", "images", "lightweight_pipeline", "results")

router = APIRouter(tags=["pipelines"])


def _average_confidence(detections):
    if not detections:
        return 0
    return round(sum(item["score"] for item in detections) / len(detections), 4)


def _extract_total_timing(timing):
    if isinstance(timing, dict):
        return round(float(timing.get("total_ms", 0)), 2)
    return round(float(timing), 2)


def _empty_video_timing():
    return {
        "preprocess_ms": 0.0,
        "inference_ms": 0.0,
        "postprocess_ms": 0.0,
        "total_ms": 0.0,
    }


def _accumulate_timing(total_timing, timing):
    for key in total_timing:
        total_timing[key] += float(timing.get(key, 0.0))


def _scene_analysis(detections):
    if not detections:
        return ["当前未识别到目标，请调整图片内容或检测阈值后重试。"]

    labels = [item["class_name"] for item in detections]
    unique_labels = sorted(set(labels))
    insights = [f"轻量化增强后共识别到 {len(detections)} 个目标，涉及 {len(unique_labels)} 类场景对象。"]

    if "person" in labels:
        insights.append("画面中存在行人目标，建议重点关注近距离通行风险。")
    if "car" in labels or "bus" in labels or "truck" in labels:
        insights.append("检测到机动车目标，轻量化增强后有助于观察车道中的主要交通参与者。")
    if len(insights) == 1:
        insights.append("当前结果以常见道路目标为主，可继续结合阈值微调提升检出稳定性。")

    return insights


@router.post("/pipelines/lightweight-low-light-detect")
def process_lightweight_pipeline(
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

    enhance_result = enhance_lightweight_low_light_raw(image)
    enhanced_image = enhance_result["image"]
    enhanced_filename = f"enhanced_{os.path.basename(upload_path)}"
    enhanced_path = save_cv2_image(enhanced_image, enhanced_folder, enhanced_filename)

    detect_result = detect_yolo26_raw(enhanced_image, conf_thres=conf_thres, iou_thres=iou_thres)
    detected_image = detect_result["image"]
    result_filename = f"detected_{os.path.basename(upload_path)}"
    result_path = save_cv2_image(detected_image, result_folder, result_filename)

    detections = detect_result["detections"]
    enhance_total_ms = _extract_total_timing(enhance_result["timing_ms"])
    detect_total_ms = _extract_total_timing(detect_result["timing_ms"])
    total_timing_ms = round(enhance_total_ms + detect_total_ms, 2)

    return success_response(
        "轻量化图像增强与目标检测成功",
        {
            "media_type": "image",
            "upload_image": convert_to_url_path(upload_path, app_root),
            "upload_media": convert_to_url_path(upload_path, app_root),
            "enhanced_image": convert_to_url_path(enhanced_path, app_root),
            "enhanced_media": convert_to_url_path(enhanced_path, app_root),
            "result_image": convert_to_url_path(result_path, app_root),
            "result_media": convert_to_url_path(result_path, app_root),
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
    )


def _handle_video(upload_path, conf_thres, iou_thres, app_root):
    capture = open_video_capture(upload_path)
    metadata = get_video_metadata(capture)

    base_name = os.path.splitext(os.path.basename(upload_path))[0]
    enhanced_path = build_output_video_path(enhanced_folder, f"enhanced_{base_name}")
    result_path = build_output_video_path(result_folder, f"detected_{base_name}")
    enhanced_writer, enhanced_codec = create_video_writer(
        enhanced_path,
        metadata["width"],
        metadata["height"],
        metadata["fps"],
    )
    result_writer, result_codec = create_video_writer(
        result_path,
        metadata["width"],
        metadata["height"],
        metadata["fps"],
    )

    enhance_timing = _empty_video_timing()
    detect_timing = _empty_video_timing()
    frames_processed = 0
    total_detections = 0
    max_frame_detections = 0
    last_detections = []
    detected_labels = []

    try:
        def process_frame(_frame_index, frame):
            enhance_result = enhance_lightweight_low_light_raw(frame)
            enhanced_frame = enhance_result["image"]
            detect_result = detect_yolo26_raw(
                enhanced_frame,
                conf_thres=conf_thres,
                iou_thres=iou_thres,
            )
            return enhance_result, detect_result

        def handle_result(result_pair):
            nonlocal frames_processed, total_detections, max_frame_detections, last_detections, detected_labels
            enhance_result, detect_result = result_pair
            enhanced_writer.write(enhance_result["image"])
            _accumulate_timing(enhance_timing, enhance_result["timing_ms"])

            result_writer.write(detect_result["image"])
            _accumulate_timing(detect_timing, detect_result["timing_ms"])

            frames_processed += 1
            total_detections += int(detect_result["count"])
            max_frame_detections = max(max_frame_detections, int(detect_result["count"]))
            if detect_result["detections"]:
                last_detections = detect_result["detections"]
                detected_labels.extend(item["class_name"] for item in detect_result["detections"])

        parallel_stats = process_video_in_parallel(
            capture,
            process_frame,
            handle_result,
            warmup_fn=lambda: (
                warmup_lightweight_low_light_model(),
                warmup_yolo26_model(conf_thres=conf_thres, iou_thres=iou_thres),
            )[-1],
        )
    finally:
        capture.release()
        enhanced_writer.release()
        result_writer.release()

    if frames_processed == 0:
        return error_response("上传视频读取失败", 400)

    enhance_total_ms = round(enhance_timing["total_ms"], 2)
    detect_total_ms = round(detect_timing["total_ms"], 2)
    total_timing_ms = round(enhance_total_ms + detect_total_ms, 2)

    avg_confidence = _average_confidence(last_detections)
    scene_labels = [{"class_name": label, "score": 1.0} for label in sorted(set(detected_labels))]

    return success_response(
        "轻量化视频增强与目标检测成功",
        {
            "media_type": "video",
            "upload_image": convert_to_url_path(upload_path, app_root),
            "upload_media": convert_to_url_path(upload_path, app_root),
            "enhanced_image": convert_to_url_path(enhanced_path, app_root),
            "enhanced_media": convert_to_url_path(enhanced_path, app_root),
            "result_image": convert_to_url_path(result_path, app_root),
            "result_media": convert_to_url_path(result_path, app_root),
            "detections": last_detections,
            "count": len(last_detections),
            "thresholds": {
                "conf_thres": conf_thres,
                "iou_thres": iou_thres,
            },
            "video_meta": {
                **metadata,
                "processed_frames": frames_processed,
                "enhanced_codec": enhanced_codec,
                "result_codec": result_codec,
            },
            "timing_ms": {
                "enhance": {
                    **{key: round(value, 2) for key, value in enhance_timing.items()},
                    "avg_frame_ms": round(enhance_total_ms / frames_processed, 2),
                },
                "detect": {
                    **{key: round(value, 2) for key, value in detect_timing.items()},
                    "avg_frame_ms": round(detect_total_ms / frames_processed, 2),
                },
                "total": total_timing_ms,
                "avg_frame_total_ms": round(total_timing_ms / frames_processed, 2),
                "wall_ms": parallel_stats["elapsed_ms"],
                "workers": parallel_stats["workers"],
                "warmup_workers": parallel_stats["warmup_workers"],
            },
            "summary": {
                "target_count": total_detections,
                "avg_confidence": avg_confidence,
                "latency_ms": total_timing_ms,
                "max_frame_detections": max_frame_detections,
                "avg_detections_per_frame": round(total_detections / frames_processed, 3),
                "parallel_workers": parallel_stats["workers"],
            },
            "scene_analysis": _scene_analysis(scene_labels),
        },
    )
