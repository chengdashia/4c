from copy import deepcopy
from pathlib import Path


DEFAULT_HOME_PAGE_MEDIA = [
    {
        "key": "raw",
        "step": "Stage 01",
        "title": "原始输入",
        "media_type": "image",
        "src": "/posters/raw-scene.svg",
    },
    {
        "key": "enhanced",
        "step": "Stage 02",
        "title": "增强输出",
        "media_type": "image",
        "src": "/posters/enhanced-scene.svg",
    },
    {
        "key": "detected",
        "step": "Stage 03",
        "title": "检测输出",
        "media_type": "image",
        "src": "/posters/detected-scene.svg",
    },
]

HOME_PAGE_MEDIA = [
    {
        "key": "raw",
        "step": "Stage 01",
        "title": "原始输入",
        "description": "",
        "note": "",
        "media_type": "image",
        "src": "/static/showcase/home/raw.jpg",
    },
    {
        "key": "enhanced",
        "step": "Stage 02",
        "title": "增强输出",
        "description": "",
        "note": "",
        "media_type": "image",
        "src": "/static/showcase/home/enhanced.jpg",
    },
    {
        "key": "detected",
        "step": "Stage 03",
        "title": "检测输出",
        "description": "",
        "note": "",
        "media_type": "image",
        "src": "/static/showcase/home/detected.jpg",
    },
]


PIPELINE_VIDEO_DIRS = {
    "raw": "images/pipeline/uploads",
    "enhanced": "images/pipeline/enhanced",
    "detected": "images/pipeline/results",
}
VIDEO_SUFFIXES = {".mp4", ".mov", ".webm", ".m4v", ".avi"}


def _static_file_exists(app_root, src):
    if not isinstance(src, str) or not src.startswith("/static/"):
        return False
    relative_path = src.removeprefix("/static/")
    return Path(app_root, "static", relative_path).is_file()


def _latest_pipeline_video_src(app_root, key):
    relative_dir = PIPELINE_VIDEO_DIRS.get(key)
    if not relative_dir:
        return None

    media_dir = Path(app_root, "static", relative_dir)
    if not media_dir.is_dir():
        return None

    candidates = [
        path
        for path in media_dir.iterdir()
        if path.is_file() and path.suffix.lower() in VIDEO_SUFFIXES
    ]
    if not candidates:
        return None

    latest_video = max(candidates, key=lambda path: (path.stat().st_mtime, path.name))
    return f"/static/{relative_dir}/{latest_video.name}"


def get_home_page_media(app_root):
    resolved = []

    for index, default_item in enumerate(DEFAULT_HOME_PAGE_MEDIA):
        configured_item = HOME_PAGE_MEDIA[index] if index < len(HOME_PAGE_MEDIA) else {}
        merged = deepcopy(default_item)
        merged.update({key: value for key, value in configured_item.items() if value not in (None, "")})

        pipeline_video_src = _latest_pipeline_video_src(app_root, merged["key"])
        if pipeline_video_src:
            merged["media_type"] = "video"
            merged["src"] = pipeline_video_src

        if not _static_file_exists(app_root, merged["src"]):
            merged["media_type"] = default_item["media_type"]
            merged["src"] = default_item["src"]

        resolved.append(merged)

    return resolved
