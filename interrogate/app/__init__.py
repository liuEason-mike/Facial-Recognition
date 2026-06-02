"""
应用工厂与引导
- 加载 .env 与配置
- 初始化 SQLAlchemy
- 注册 API 路由
- 配置滚动文件日志（DATA_ROOT/logs/app.log）
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from .config import get_config
from .extensions import db
from .events import ApiError
from .utils.responses import ok, error
from .constants.codes import Code


def create_app():
    """
    Flask 应用工厂，加载 .env，初始化数据库、蓝图与全局异常处理
    """
    root_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)))
    base_env_path = os.path.join(root_dir, ".env")
    profile = os.getenv("APP_PROFILE")
    profile_env_path = os.path.join(root_dir, f".env.{profile}") if profile else None
    env_file = os.getenv("ENV_FILE")

    try:
        from dotenv import load_dotenv

        if os.path.exists(base_env_path):
            load_dotenv(base_env_path, override=False)

        if env_file:
            env_file_path = env_file if os.path.isabs(env_file) else os.path.join(root_dir, env_file)
            if os.path.exists(env_file_path):
                load_dotenv(env_file_path, override=True)
        elif profile_env_path and os.path.exists(profile_env_path):
            load_dotenv(profile_env_path, override=True)
    except Exception:
        pass

    app = Flask("Interrogate")
    cfg = get_config()
    app.config.from_mapping(cfg)

    if app.config.get("DATABASE_ENABLED"):
        db.init_app(app)

    _register_routes(app)

    @app.get("/health")
    def health():
        return ok({"status": "ok"})

    @app.errorhandler(404)
    def not_found(e):
        return error(Code.NOT_FOUND, "not_found", http_status=404)

    @app.errorhandler(ApiError)
    def handle_api_error(e: ApiError):
        return error(Code.INTERNAL_ERROR, e.message, http_status=e.status_code)

    @app.errorhandler(Exception)
    def handle_error(e):
        app.logger.exception("Unhandled exception")
        return error(Code.INTERNAL_ERROR, "internal_error", http_status=500)

    _configure_logging(app)
    _ensure_storage(app)

    if app.config.get("DATABASE_ENABLED"):
        with app.app_context():
            db.create_all()
    else:
        app.logger.warning("DATABASE_ENABLED=0，跳过数据库初始化与自动建表")

    return app


def _register_routes(app: Flask):
    """
    统一注册 HTTP 蓝图。
    """
    from .routes.api.asr_diarization import asr_diarization_bp
    from .routes.api.asr_keywords import asr_keywords_bp

    app.register_blueprint(asr_diarization_bp)
    app.register_blueprint(asr_keywords_bp)


def _ensure_storage(app: Flask):
    data_root = app.config.get("DATA_ROOT") or "./storage"
    os.makedirs(data_root, exist_ok=True)
    os.makedirs(os.path.join(data_root, "logs"), exist_ok=True)


def _configure_logging(app: Flask):
    level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
    app.logger.setLevel(level)
    log_dir = os.path.join(app.config.get("DATA_ROOT", "./storage"), "logs")
    os.makedirs(log_dir, exist_ok=True)
    fh = RotatingFileHandler(os.path.join(log_dir, "app.log"), maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    )
    fh.setFormatter(fmt)
    fh.setLevel(level)
    app.logger.addHandler(fh)
