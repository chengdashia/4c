# FastAPI Backend Migration Design

## Goal

Replace the current Flask backend with a FastAPI backend while keeping the computer-vision inference behavior stable. The migration should make the Web layer idiomatic FastAPI, use RESTful endpoint names, and keep the successful response envelope as `{ "code": 200, "message": "...", "data": ... }` so the frontend business logic stays predictable.

## Current State

The backend lives under `back/`. `back/app/__init__.py` creates the Flask app, configures CORS and logging, registers `flask-restx` namespaces, exposes health/model/homepage endpoints, and serves static files from `back/static`. Feature endpoints are implemented as `flask_restx.Resource` classes under `back/app/routes/`.

The frontend calls the backend from `front/src/services/api.js`. It expects:

- An API origin defaulting to `http://127.0.0.1:5001`.
- Successful payloads wrapped in `{ code, message, data }`.
- Static media paths returned as `/static/...`.
- Multipart uploads with fields `file`, `conf_thres`, and `iou_thres`.

The model and media-processing logic lives mostly in `back/app/utils/` and `back/app/models/`. Those pieces should remain intact during this migration.

## Chosen Approach

Use a FastAPI-native Web layer with `FastAPI`, `APIRouter`, `UploadFile`, `File`, and `Form`. Do not preserve the old `*_file` route names. Do preserve the success response envelope.

This is not a compatibility wrapper around Flask. Flask, Flask-Cors, and flask-restx should be removed from runtime dependencies. FastAPI, Uvicorn, and python-multipart should be added.

## Endpoint Design

The backend should expose:

- `GET /api/health`
- `GET /api/models`
- `GET /api/homepage-media`
- `POST /api/detections/yolo26`
- `POST /api/enhancements/low-light`
- `POST /api/enhancements/low-light/lightweight`
- `POST /api/enhancements/dehaze`
- `POST /api/enhancements/derain`
- `POST /api/pipelines/low-light-detect`
- `POST /api/pipelines/lightweight-low-light-detect`
- `POST /api/pipelines/dehaze-detect`
- `POST /api/pipelines/derain-detect`

`/docs` should be FastAPI's generated OpenAPI UI.

## Architecture

`back/app/__init__.py` should expose `create_app()` returning a configured `FastAPI` instance. It should:

- Configure CORS with the same permissive development behavior.
- Mount `back/static` at `/static`.
- Configure logging using the existing rotating file and console handlers.
- Register routers under `/api`.
- Register exception handlers for upload size, media decode, video processing, missing files, 404, and unexpected server errors.

Feature route modules should be rewritten around `APIRouter`. Each upload endpoint should accept:

- `file: UploadFile = File(...)`
- `conf_thres: float = Form(0.25)` where detection is involved
- `iou_thres: float = Form(0.45)` where detection is involved

The current inference and video-processing functions should stay in place and be called from the FastAPI routes.

## Response Contract

Successful responses should keep this shape:

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {}
}
```

Validation and runtime errors should return meaningful HTTP status codes and preserve the existing Chinese `message` strings where possible:

```json
{
  "code": 400,
  "message": "没有文件被上传"
}
```

This keeps frontend unwrapping simple while still making HTTP status codes useful.

## Frontend Changes

`front/src/services/api.js` should point to the new RESTful routes:

- `runVisionPipeline` -> `/api/pipelines/low-light-detect`
- `runDirectDetect` -> `/api/detections/yolo26`
- `runLowLightEnhance` -> `/api/enhancements/low-light`
- `runLightweightLowLightEnhance` -> `/api/enhancements/low-light/lightweight`
- `runDerainOnly` -> `/api/enhancements/derain`
- `runDehazeOnly` -> `/api/enhancements/dehaze`
- `runDehazePipeline` -> `/api/pipelines/dehaze-detect`
- `runDerainPipeline` -> `/api/pipelines/derain-detect`
- `runLightweightPipeline` -> `/api/pipelines/lightweight-low-light-detect`

The frontend unwrap logic can remain based on `{ code, message, data }`.

## Startup And Dependencies

`back/run.py` should run the FastAPI app with Uvicorn for local development. A module target such as `app:create_app` or an `app` variable should be available for command-line starts.

`back/requirements.txt` should replace Flask dependencies with:

- `fastapi`
- `uvicorn`
- `python-multipart`

Existing model dependencies such as numpy, OpenCV, onnxruntime, Pillow, and ultralytics should remain.

## Testing

Before changing production code, add focused tests for the new route contract where practical:

- `GET /api/health` returns a ready response with the expected envelope fields.
- Missing upload file on a representative endpoint returns a normalized HTTP 400 response with `{ "code": 400, "message": "没有文件被上传" }`.
- The frontend service endpoints point to the new RESTful paths.

After implementation, run backend import/startup checks and targeted frontend checks. Because the real inference endpoints require large model files and media assets, full model execution can be verified with a small existing sample only if the local dependencies and model files are available.

## Out Of Scope

This migration should not rewrite model inference code, change output image/video formats, reorganize generated static assets, add authentication, or introduce persistent storage. It should not preserve the old Flask route paths unless explicitly requested later.
