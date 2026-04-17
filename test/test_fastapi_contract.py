from fastapi.testclient import TestClient

from app import create_app


client = TestClient(create_app())


def test_health_returns_existing_envelope():
    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["message"] == "Showcase Vision API is ready."
    assert "models" in payload
    assert "model_loaded" in payload


def test_missing_upload_returns_normalized_400():
    response = client.post("/api/detections/yolo26", data={"conf_thres": "0.25"})

    assert response.status_code == 400
    assert response.json() == {"code": 400, "message": "没有文件被上传"}
