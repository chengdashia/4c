from pathlib import Path


API_JS = Path("front/src/services/api.js").read_text(encoding="utf-8")


def test_frontend_uses_restful_backend_paths():
    old_paths = [
        "/pipeline_file/process",
        "/yolo26_bdd100k_file/detect",
    ]
    for path in old_paths:
        assert path not in API_JS

    new_paths = [
        "/pipelines/low-light-detect",
        "/detections/yolo26",
        "/enhancements/low-light",
        "/enhancements/low-light/lightweight",
        "/enhancements/derain",
        "/enhancements/dehaze",
        "/pipelines/dehaze-detect",
        "/pipelines/derain-detect",
        "/pipelines/lightweight-low-light-detect",
    ]
    for path in new_paths:
        assert path in API_JS
