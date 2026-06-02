"""
应用配置加载器（MySQL 专用）
- 统一从环境变量读取 MySQL 连接信息，生成 SQLALCHEMY_DATABASE_URI
- 支持使用完整的 DATABASE_URL（必须为 mysql+pymysql 前缀）
- 推荐在 .env 中配置以下变量：
  * DB_HOST：MySQL 主机，例如 127.0.0.1
  * DB_PORT：MySQL 端口，默认 3306
  * DB_USER：数据库用户名
  * DB_PASSWORD：数据库密码
  * DB_NAME：数据库名
  或者：
  * DATABASE_URL：完整连接串（例如 mysql+pymysql://user:pwd@host:3306/dbname）
"""
import os
import re


def _env_flag(name: str, default: str = "0") -> bool:
    """
    解析布尔环境变量，避免临时运行模式下因大小写或 true/yes 写法导致开关失效。
    """
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _redact_database_uri(db_url: str) -> str:
    """
    控制台输出数据库连接时隐藏密码，避免启动日志泄露本地或生产凭据。
    """
    return re.sub(r"(://[^:/@]+:)[^@]+@", r"\1***@", db_url)


def get_config():
    """
    加载配置。
    ENABLE_DATABASE=0 时服务不初始化 SQLAlchemy，也不会执行自动建表或实时入库。
    ENABLE_DATABASE=1 时优先使用 DATABASE_URL（必须为 mysql+pymysql 前缀），否则由 DB_* 变量拼接。
    """
    database_enabled = _env_flag("ENABLE_DATABASE", "0")
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        if database_enabled and not db_url.startswith("mysql+pymysql://"):
            raise RuntimeError("DATABASE_URL 必须使用 mysql+pymysql 前缀")
    else:
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_host = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT", "3306")
        db_name = os.getenv("DB_NAME")
        if all([db_user, db_password, db_host, db_name]):
            db_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        else:
            db_url = os.getenv("SQLITE_URL") or "sqlite:///./storage/app.db"
    data_root = os.getenv("DATA_ROOT", "./storage")
    secret_key = os.getenv("SECRET_KEY", "dev-secret")
    socket_cors = os.getenv("SOCKET_CORS_ORIGINS", "*")
    
    cfg = {
        "SECRET_KEY": secret_key,
        "SQLALCHEMY_DATABASE_URI": db_url,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "pool_pre_ping": True,
            "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "28000")),
        },
        "DATA_ROOT": data_root,
        "SOCKET_CORS_ORIGINS": socket_cors,
        "JSON_SORT_KEYS": False,
        "TESTING": os.getenv("TESTING", "0") == "1",
        "DATABASE_ENABLED": database_enabled,
    }
    if database_enabled:
        print("【最终数据库连接】", _redact_database_uri(cfg["SQLALCHEMY_DATABASE_URI"]))
    else:
        print("【数据库状态】已禁用，跳过 SQLAlchemy 初始化和实时入库")
    return cfg
