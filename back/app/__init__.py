import logging
import os
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import JSONResponse

import config
import homepage_media
from app.http import error_response
from app.utils.image_codec import ImageDecodeError
from app.utils.model_loader import get_model_status
from app.utils.video_processing import VideoProcessingError


def create_app():
    app_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    app = FastAPI(
        title="Showcase Vision API",
        description="Low-light enhancement and YOLO26 detection services.",
        version="1.0",
    )
    app.state.app_root = app_root
    app.state.max_content_length = config.DevelopmentConfig.MAX_CONTENT_LENGTH

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    configure_logging(app, app_root)

    static_dir = os.path.join(app_root, "static")
    os.makedirs(static_dir, exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    register_routes(app, app_root)
    register_exception_handlers(app)

    @app.middleware("http")
    async def enforce_max_content_length(request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > app.state.max_content_length:
            return error_response("上传文件过大，最大支持 256MB", 413)
        return await call_next(request)

    app.logger.info("Showcase Vision API started")
    return app


def register_routes(app, app_root):
    from .routes.attentive_gan_derainnet import router as derain_router
    from .routes.c2pnet import router as c2pnet_router
    from .routes.dehaze_pipeline import router as dehaze_pipeline_router
    from .routes.derain_pipeline import router as derain_pipeline_router
    from .routes.lightweight_low_light import router as lightweight_low_light_router
    from .routes.lightweight_pipeline import router as lightweight_pipeline_router
    from .routes.low_light import router as low_light_router
    from .routes.pipeline import router as pipeline_router
    from .routes.yolo26_bdd100k import router as yolo26_router

    @app.get("/api/health")
    def health():
        models = get_model_status()
        return {
            "status": "ready",
            "message": "Showcase Vision API is ready.",
            "models": models,
            "model_loaded": any(model["loaded"] for model in models),
        }

    @app.get("/api/models")
    def models():
        return {"code": 200, "data": get_model_status()}

    @app.get("/api/homepage-media")
    def home_page_media():
        return {"code": 200, "data": homepage_media.get_home_page_media(app_root)}

    @app.get("/")
    def index():
        return {"code": 200, "message": "Showcase Vision API is running."}

    app.include_router(yolo26_router, prefix="/api")
    app.include_router(low_light_router, prefix="/api")
    app.include_router(lightweight_low_light_router, prefix="/api")
    app.include_router(c2pnet_router, prefix="/api")
    app.include_router(derain_router, prefix="/api")
    app.include_router(pipeline_router, prefix="/api")
    app.include_router(dehaze_pipeline_router, prefix="/api")
    app.include_router(derain_pipeline_router, prefix="/api")
    app.include_router(lightweight_pipeline_router, prefix="/api")


def register_exception_handlers(app):
    @app.exception_handler(ImageDecodeError)
    async def image_decode_error(_request, error):
        return error_response(str(error), 400)

    @app.exception_handler(VideoProcessingError)
    async def video_processing_error(_request, error):
        return error_response(str(error), 400)

    @app.exception_handler(FileNotFoundError)
    async def file_not_found(_request, error):
        return error_response(str(error), 500)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request, _error):
        return error_response("请求参数无效", 400)

    @app.exception_handler(HTTPException)
    async def http_error(_request, error):
        message = "请求的资源不存在" if error.status_code == 404 else str(error.detail)
        return error_response(message, error.status_code)

    @app.exception_handler(Exception)
    async def internal_error(_request, error):
        app.logger.exception("Server error: %s", error)
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "服务器内部错误"},
        )


def configure_logging(app, app_root):
    log_dir = os.path.join(app_root, "logs")
    os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
    )

    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "showcase-backend.log"),
        maxBytes=1024 * 1024,
        backupCount=5,
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    app.logger = logging.getLogger("showcase.backend")
    app.logger.setLevel(logging.INFO)
