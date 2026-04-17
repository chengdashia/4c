# FastAPI Backend Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Flask Web layer with FastAPI, switch the frontend to RESTful API paths, and preserve the existing successful response envelope.

**Architecture:** Keep model and media-processing utilities intact. Replace `flask-restx` resources with FastAPI `APIRouter` endpoints that call the same inference functions and return the same business payloads. Mount static files at `/static`, keep permissive CORS, and use FastAPI's `/docs`.

**Tech Stack:** Python, FastAPI, Uvicorn, Starlette TestClient, Vue/Vite frontend service module.

---

## File Structure

- Modify `.gitignore`: ignore local worktrees and Python cache files.
- Create `back/app/http.py`: response helpers, upload validation, and Flask-compatible upload adapter for existing save helpers.
- Modify `back/app/__init__.py`: create and configure the FastAPI app, static mount, routers, logging, and exception handlers.
- Modify `back/run.py`: run the FastAPI app with Uvicorn.
- Modify `back/config.py`: rename Flask-specific config values to framework-neutral settings.
- Modify `back/requirements.txt`: replace Flask dependencies with FastAPI dependencies.
- Rewrite `back/app/routes/*.py`: convert feature routes from `flask-restx` resources to FastAPI routers.
- Modify `front/src/services/api.js`: point client calls to the new RESTful paths.
- Create `test/test_fastapi_contract.py`: backend contract tests.
- Create `test/test_frontend_api_paths.py`: frontend endpoint mapping tests.

## Task 1: Contract Tests

**Files:**
- Create: `test/test_fastapi_contract.py`
- Create: `test/test_frontend_api_paths.py`

- [ ] **Step 1: Write failing backend contract tests**

```python
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
```

- [ ] **Step 2: Write failing frontend path tests**

```python
from pathlib import Path


API_JS = Path("front/src/services/api.js").read_text(encoding="utf-8")


def test_frontend_uses_restful_backend_paths():
    expected_paths = [
        "/pipeline_file/process",
        "/yolo26_bdd100k_file/detect",
    ]
    for path in expected_paths:
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
```

- [ ] **Step 3: Verify tests fail before implementation**

Run:

```bash
PYTHONPATH=back pytest test/test_fastapi_contract.py test/test_frontend_api_paths.py -q
```

Expected: FAIL because FastAPI dependencies/routes are not implemented yet and frontend still uses old paths.

## Task 2: FastAPI App Shell

**Files:**
- Create: `back/app/http.py`
- Modify: `back/app/__init__.py`
- Modify: `back/config.py`
- Modify: `back/run.py`
- Modify: `back/requirements.txt`

- [ ] **Step 1: Implement shared HTTP helpers**

Create helpers for response envelopes, upload validation, and adapting FastAPI `UploadFile` to the existing `save_upload_file()` helper that expects `filename`, `content_type`, and `save(path)`.

- [ ] **Step 2: Replace Flask app creation with FastAPI app creation**

`create_app()` should return `FastAPI(title="Showcase Vision API", version="1.0")`, add CORS middleware, mount static files, register routers, and add exception handlers.

- [ ] **Step 3: Update local startup**

`back/run.py` should expose `app = create_app()` and run `uvicorn.run("run:app", host="0.0.0.0", port=5001, reload=True)` when executed directly.

- [ ] **Step 4: Update dependencies**

`back/requirements.txt` should include `fastapi`, `uvicorn`, and `python-multipart`, and remove Flask packages.

- [ ] **Step 5: Verify app imports**

Run:

```bash
PYTHONPATH=back python -c "from app import create_app; app = create_app(); print(app.title)"
```

Expected: prints `Showcase Vision API`.

## Task 3: Feature Routes

**Files:**
- Modify: `back/app/routes/yolo26_bdd100k.py`
- Modify: `back/app/routes/low_light.py`
- Modify: `back/app/routes/lightweight_low_light.py`
- Modify: `back/app/routes/c2pnet.py`
- Modify: `back/app/routes/attentive_gan_derainnet.py`
- Modify: `back/app/routes/pipeline.py`
- Modify: `back/app/routes/dehaze_pipeline.py`
- Modify: `back/app/routes/derain_pipeline.py`
- Modify: `back/app/routes/lightweight_pipeline.py`

- [ ] **Step 1: Convert single-stage feature routes**

Convert detection and enhancement modules to export `router = APIRouter()` and define endpoints at:

- `/detections/yolo26`
- `/enhancements/low-light`
- `/enhancements/low-light/lightweight`
- `/enhancements/dehaze`
- `/enhancements/derain`

Each endpoint should call the same existing raw model functions and return the same `data` payloads as before.

- [ ] **Step 2: Convert pipeline routes**

Convert pipeline modules to export `router = APIRouter()` and define endpoints at:

- `/pipelines/low-light-detect`
- `/pipelines/lightweight-low-light-detect`
- `/pipelines/dehaze-detect`
- `/pipelines/derain-detect`

Each endpoint should preserve current image/video payload keys.

- [ ] **Step 3: Verify backend contract tests pass**

Run:

```bash
PYTHONPATH=back pytest test/test_fastapi_contract.py -q
```

Expected: PASS.

## Task 4: Frontend API Paths

**Files:**
- Modify: `front/src/services/api.js`

- [ ] **Step 1: Replace old endpoint strings**

Update `runPipelineRequest()` callers to use the RESTful paths specified in the design.

- [ ] **Step 2: Verify frontend path test passes**

Run:

```bash
pytest test/test_frontend_api_paths.py -q
```

Expected: PASS.

## Task 5: Final Verification

**Files:**
- All changed files

- [ ] **Step 1: Run Python compile check**

Run:

```bash
python -m compileall -q back/app back/run.py back/config.py test
```

Expected: exit code 0.

- [ ] **Step 2: Run targeted tests**

Run:

```bash
PYTHONPATH=back pytest test/test_fastapi_contract.py test/test_frontend_api_paths.py -q
```

Expected: all tests pass.

- [ ] **Step 3: Inspect changed files**

Run:

```bash
git diff --stat
git status --short
```

Expected: only migration-related files are modified.

