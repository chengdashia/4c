import os

from fastapi import APIRouter, File, UploadFile

from app.http import UploadFileStorage, error_response, success_response, validate_upload_file
from app.utils.image_processing import (
    infer_media_type,
    read_image_bgr,
    save_cv2_image,
    save_upload_file,
)
from app.utils.model_loader import dehaze_c2pnet_raw, warmup_c2pnet_model
from app.utils.path_utils import convert_to_url_path
from app.utils.video_processing import (
    build_output_video_path,
    create_video_writer,
    get_video_metadata,
    open_video_capture,
    process_video_in_parallel,
)

app_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
upload_folder = os.path.join(app_root, "static", "images", "c2pnet", "uploads")
result_folder = os.path.join(app_root, "static", "images", "c2pnet", "results")

router = APIRouter(tags=["enhancements"])


@router.post("/enhancements/dehaze")
def dehaze(file: UploadFile | None = File(None)):
    upload_error = validate_upload_file(file)
    if upload_error:
        return upload_error

    upload_path = save_upload_file(UploadFileStorage(file), upload_folder)
    media_type = infer_media_type(file.filename, file.content_type)

    if media_type == "video":
        return _handle_video(upload_path, app_root)

    image = read_image_bgr(upload_path)
    if image is None:
        return error_response("上传图片读取失败", 400)
    result = dehaze_c2pnet_raw(image)

    result_filename = f"dehazed_{os.path.basename(upload_path)}"
    result_path = save_cv2_image(result["image"], result_folder, result_filename)

    return success_response(
        "图像去雾成功",
        {
            "media_type": "image",
            "upload_image": convert_to_url_path(upload_path, app_root),
            "upload_media": convert_to_url_path(upload_path, app_root),
            "result_image": convert_to_url_path(result_path, app_root),
            "result_media": convert_to_url_path(result_path, app_root),
            "timing_ms": result["timing_ms"],
            "image_shape": result["image_shape"],
        },
    )


def _handle_video(upload_path, app_root):
    capture = open_video_capture(upload_path)
    metadata = get_video_metadata(capture)
    result_prefix = f"dehazed_{os.path.splitext(os.path.basename(upload_path))[0]}"
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
            return dehaze_c2pnet_raw(frame)

        def handle_result(result):
            nonlocal total_timing_ms, frames_processed
            writer.write(result["image"])
            total_timing_ms += float(result["timing_ms"]["total_ms"])
            frames_processed += 1

        parallel_stats = process_video_in_parallel(
            capture,
            process_frame,
            handle_result,
            warmup_fn=warmup_c2pnet_model,
        )
    finally:
        capture.release()
        writer.release()

    if frames_processed == 0:
        return error_response("上传视频读取失败", 400)

    return success_response(
        "视频去雾成功",
        {
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
    )
