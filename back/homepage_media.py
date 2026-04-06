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


def _static_file_exists(app_root, src):
    if not isinstance(src, str) or not src.startswith("/static/"):
        return False
    relative_path = src.removeprefix("/static/")
    return Path(app_root, "static", relative_path).is_file()


def get_home_page_media(app_root):
    resolved = []

    for index, default_item in enumerate(DEFAULT_HOME_PAGE_MEDIA):
        configured_item = HOME_PAGE_MEDIA[index] if index < len(HOME_PAGE_MEDIA) else {}
        merged = deepcopy(default_item)
        merged.update({key: value for key, value in configured_item.items() if value not in (None, "")})

        if not _static_file_exists(app_root, merged["src"]):
            merged["media_type"] = default_item["media_type"]
            merged["src"] = default_item["src"]

        resolved.append(merged)

    return resolved
