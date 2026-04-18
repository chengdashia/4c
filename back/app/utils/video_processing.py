import math
import os
import platform
import shutil
import subprocess
import threading
from atexit import register as register_atexit
from concurrent.futures import ThreadPoolExecutor
from time import perf_counter

import cv2
import numpy as np


DEFAULT_VIDEO_FPS = 25.0
DEFAULT_MAX_VIDEO_WORKERS = min(4, os.cpu_count() or 1)
DEFAULT_GPU_VIDEO_WORKERS = 2
DEFAULT_IN_FLIGHT_FACTOR = 2
DEFAULT_VIDEO_CODECS = ("avc1", "H264", "mp4v")
WINDOWS_VIDEO_CODECS = ("mp4v",)
_EXECUTOR_LOCK = threading.Lock()
_EXECUTORS = {}


class VideoProcessingError(ValueError):
    pass


def open_video_capture(video_path):
    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        raise VideoProcessingError("无法读取上传视频")
    return capture


def get_video_metadata(capture):
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)

    if not math.isfinite(fps) or fps <= 0:
        fps = DEFAULT_VIDEO_FPS

    duration_sec = round(frame_count / fps, 3) if frame_count > 0 and fps > 0 else None

    return {
        "width": width,
        "height": height,
        "fps": round(fps, 3),
        "frame_count": frame_count,
        "duration_sec": duration_sec,
    }


def build_output_video_path(save_dir, filename_prefix):
    os.makedirs(save_dir, exist_ok=True)
    return os.path.join(save_dir, f"{filename_prefix}.mp4")


def get_ffmpeg_executable():
    configured = os.getenv("FFMPEG_BINARY", "").strip()
    if configured:
        return configured

    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass

    return shutil.which("ffmpeg")


class FFmpegVideoWriter:
    def __init__(self, video_path, width, height, fps, ffmpeg_executable):
        if width <= 0 or height <= 0:
            raise VideoProcessingError("结果视频保存失败，视频宽高无效")

        self.video_path = video_path
        self.width = int(width)
        self.height = int(height)
        self.fps = float(fps) if fps and math.isfinite(float(fps)) else DEFAULT_VIDEO_FPS
        self._closed = False

        command = [
            ffmpeg_executable,
            "-y",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-vcodec",
            "rawvideo",
            "-pix_fmt",
            "bgr24",
            "-s",
            f"{self.width}x{self.height}",
            "-r",
            f"{self.fps:.6f}",
            "-i",
            "-",
            "-an",
            "-vcodec",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            self.video_path,
        ]
        self._process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

    def write(self, frame):
        if self._closed:
            raise VideoProcessingError("结果视频保存失败，写入器已关闭")
        if self._process.stdin is None:
            raise VideoProcessingError("结果视频保存失败，FFmpeg 输入不可用")
        if frame.shape[:2] != (self.height, self.width):
            raise VideoProcessingError("结果视频保存失败，输出帧尺寸与视频尺寸不一致")
        if frame.dtype != np.uint8:
            frame = np.clip(frame, 0, 255).astype(np.uint8)

        try:
            self._process.stdin.write(np.ascontiguousarray(frame).tobytes())
        except BrokenPipeError as exc:
            raise VideoProcessingError("结果视频保存失败，FFmpeg 写入中断") from exc

    def release(self):
        if self._closed:
            return
        self._closed = True

        if self._process.stdin is not None:
            self._process.stdin.close()
        stderr = self._process.stderr.read() if self._process.stderr is not None else b""
        return_code = self._process.wait()
        if return_code != 0:
            message = stderr.decode("utf-8", errors="ignore").strip()
            if message:
                raise VideoProcessingError(f"结果视频保存失败，FFmpeg 编码失败: {message}")
            raise VideoProcessingError("结果视频保存失败，FFmpeg 编码失败")


def create_video_writer(video_path, width, height, fps):
    ffmpeg_executable = get_ffmpeg_executable()
    if ffmpeg_executable:
        try:
            return FFmpegVideoWriter(video_path, width, height, fps, ffmpeg_executable), "libx264"
        except OSError:
            pass

    codecs = WINDOWS_VIDEO_CODECS if platform.system() == "Windows" else DEFAULT_VIDEO_CODECS
    for codec in codecs:
        fourcc = cv2.VideoWriter_fourcc(*codec)
        writer = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
        if writer.isOpened():
            return writer, codec
        writer.release()
    raise VideoProcessingError("结果视频保存失败，未找到可用的视频编码器")


def get_video_worker_count():
    raw = os.getenv("VIDEO_PROCESS_WORKERS", "").strip()
    if raw:
        try:
            value = int(raw)
            if value > 0:
                return value
        except ValueError:
            pass

    try:
        from app.utils.model_loader import is_gpu_accelerated

        if is_gpu_accelerated():
            return DEFAULT_GPU_VIDEO_WORKERS
    except Exception:
        pass

    return DEFAULT_MAX_VIDEO_WORKERS


def _shutdown_video_executors():
    with _EXECUTOR_LOCK:
        executors = list(_EXECUTORS.values())
        _EXECUTORS.clear()

    for executor in executors:
        executor.shutdown(wait=False, cancel_futures=False)


register_atexit(_shutdown_video_executors)


def get_shared_video_executor(max_workers):
    worker_count = max(int(max_workers), 1)
    with _EXECUTOR_LOCK:
        executor = _EXECUTORS.get(worker_count)
        if executor is None:
            executor = ThreadPoolExecutor(
                max_workers=worker_count,
                thread_name_prefix=f"video-worker-{worker_count}",
            )
            _EXECUTORS[worker_count] = executor
        return executor


def _warmup_video_workers(executor, worker_count, warmup_fn):
    if warmup_fn is None:
        return 0

    warmed_threads = set()
    futures = [executor.submit(warmup_fn) for _ in range(worker_count)]
    for future in futures:
        warmed_threads.add(future.result())
    return len(warmed_threads)


def process_video_in_parallel(
    capture,
    worker_fn,
    on_result,
    max_workers=None,
    max_in_flight=None,
    warmup_fn=None,
):
    worker_count = max_workers or get_video_worker_count()
    in_flight_limit = max_in_flight or max(worker_count * DEFAULT_IN_FLIGHT_FACTOR, 1)
    executor = get_shared_video_executor(worker_count)

    submitted = {}
    next_frame_index = 0
    write_index = 0
    start_time = perf_counter()

    def flush_next_ready():
        nonlocal write_index
        future = submitted.pop(write_index)
        result = future.result()
        on_result(result)
        write_index += 1

    warmup_workers = _warmup_video_workers(executor, worker_count, warmup_fn)

    while True:
        ok, frame = capture.read()
        if not ok:
            break

        submitted[next_frame_index] = executor.submit(worker_fn, next_frame_index, frame)
        next_frame_index += 1

        while len(submitted) >= in_flight_limit and write_index in submitted:
            flush_next_ready()

    while write_index in submitted:
        flush_next_ready()

    elapsed_ms = (perf_counter() - start_time) * 1000
    return {
        "workers": worker_count,
        "warmup_workers": warmup_workers,
        "frames_submitted": next_frame_index,
        "elapsed_ms": round(elapsed_ms, 2),
    }
