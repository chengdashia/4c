import os


class BaseConfig:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "showcase-backend")
    JSON_AS_ASCII = False
    RESTX_MASK_SWAGGER = False
    SWAGGER_UI_DOC_EXPANSION = "list"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False
