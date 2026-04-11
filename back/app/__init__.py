import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify, render_template, request
from jinja2 import TemplateNotFound
from flask_cors import CORS
from flask_restx import Api

import config
import homepage_media
from app.utils.image_codec import ImageDecodeError
from app.utils.model_loader import get_model_status
from app.utils.video_processing import VideoProcessingError

api = Api(
    version="1.0",
    title="Showcase Vision API",
    description="Low-light enhancement and YOLO26 detection services.",
    doc="/docs",
)


def create_app():
    app_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    app = Flask(
        __name__,
        static_folder=os.path.join(app_root, "static"),
        static_url_path="/static",
        template_folder=os.path.join(app_root, "templates"),
    )
    app.config.from_object(config.DevelopmentConfig)
    app.json.ensure_ascii = False

    CORS(app)
    configure_logging(app, app_root)
    api.init_app(app)

    from .routes.c2pnet import c2pnet_file_ns
    from .routes.attentive_gan_derainnet import derain_file_ns
    from .routes.dehaze_pipeline import dehaze_pipeline_file_ns
    from .routes.derain_pipeline import derain_pipeline_file_ns
    from .routes.lightweight_low_light import lightweight_low_light_file_ns
    from .routes.lightweight_pipeline import lightweight_pipeline_file_ns
    from .routes.low_light import low_light_file_ns
    from .routes.pipeline import pipeline_file_ns
    from .routes.yolo26_bdd100k import yolo26_file_ns

    api.add_namespace(c2pnet_file_ns, path="/api/c2pnet_file")
    api.add_namespace(derain_file_ns, path="/api/derain_file")
    api.add_namespace(dehaze_pipeline_file_ns, path="/api/dehaze_pipeline_file")
    api.add_namespace(derain_pipeline_file_ns, path="/api/derain_pipeline_file")
    api.add_namespace(lightweight_low_light_file_ns, path="/api/lightweight_low_light_file")
    api.add_namespace(lightweight_pipeline_file_ns, path="/api/lightweight_pipeline_file")
    api.add_namespace(low_light_file_ns, path="/api/low_light_file")
    api.add_namespace(yolo26_file_ns, path="/api/yolo26_bdd100k_file")
    api.add_namespace(pipeline_file_ns, path="/api/pipeline_file")

    @app.get("/api/health")
    def health():
        models = get_model_status()
        return jsonify(
            {
                "status": "ready",
                "message": "Showcase Vision API is ready.",
                "models": models,
                "model_loaded": any(model["loaded"] for model in models),
            }
        )

    @app.get("/api/models")
    def models():
        return jsonify({"code": 200, "data": get_model_status()})

    @app.get("/api/homepage-media")
    def home_page_media():
        return jsonify({"code": 200, "data": homepage_media.get_home_page_media(app_root)})

    @app.get("/")
    def index():
        try:
            return render_template("main.html")
        except TemplateNotFound:
            return jsonify({"code": 200, "message": "Showcase Vision API is running."})

    @app.errorhandler(413)
    def file_too_large(_error):
        return jsonify({"code": 413, "message": "上传文件过大，最大支持 256MB"}), 413

    @app.errorhandler(ImageDecodeError)
    def image_decode_error(error):
        return jsonify({"code": 400, "message": str(error)}), 400

    @app.errorhandler(VideoProcessingError)
    def video_processing_error(error):
        return jsonify({"code": 400, "message": str(error)}), 400

    @app.errorhandler(FileNotFoundError)
    def file_not_found(error):
        return jsonify({"code": 500, "message": str(error)}), 500

    @app.errorhandler(404)
    def not_found_error(_error):
        app.logger.warning("Page not found: %s", request.url)
        try:
            return render_template("404.html"), 404
        except TemplateNotFound:
            return jsonify({"code": 404, "message": "请求的资源不存在"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.exception("Server error: %s", error)
        try:
            return render_template("500.html"), 500
        except TemplateNotFound:
            return jsonify({"code": 500, "message": "服务器内部错误"}), 500

    return app


def configure_logging(app, app_root):
    del app.logger.handlers[:]

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

    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info("Showcase Vision API started")
