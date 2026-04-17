import os


class BaseConfig:
    SECRET_KEY = os.getenv("APP_SECRET_KEY", "showcase-backend")
    MAX_CONTENT_LENGTH = 256 * 1024 * 1024


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False
