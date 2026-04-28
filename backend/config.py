"""
配置文件 - 从环境变量读取数据库配置
"""
import os
from pathlib import Path


def load_env(env_path: str = None) -> None:
    """
    从 .env 文件加载环境变量。

    Args:
        env_path: 可选，指定 .env 文件路径，默认为 backend/ 同级的 .env
    """
    if env_path is None:
        # 尝试从 backend/ 上两级目录加载（项目根目录的 .env）
        base_dir = Path(__file__).resolve().parent.parent
        env_path = base_dir / ".env"
    else:
        env_path = Path(env_path)

    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        import warnings
        warnings.warn(f".env file not found at {env_path}，将使用系统环境变量或默认值。")


# 启动时自动加载 .env
load_env()

from dotenv import load_dotenv


class Config:
    """基础配置"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'caviar-crm-secret-key-2024')

    # MySQL 数据库配置（MySQL 不可用时自动降级为 SQLite）
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'caviar_crm')

    _using_mysql = bool(DB_PASSWORD)  # 有密码才尝试 MySQL

    if _using_mysql:
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@"
            f"{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
        )
    else:
        # 无 DB_PASSWORD 时使用 SQLite（仅用于本地测试）
        import pathlib
        _db_path = pathlib.Path(__file__).resolve().parent / "caviar_crm.db"
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{_db_path}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.getenv('SQLALCHEMY_ECHO', 'False').lower() == 'true'

    # 分页默认配置
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100

    # CORS 配置
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')

    # ── 邮件发送配置 ───────────────────────────────────
    EMAIL_SMTP_HOST = os.getenv('EMAIL_SMTP_HOST', '')
    EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', 587))
    EMAIL_SMTP_USER = os.getenv('EMAIL_SMTP_USER', '')
    EMAIL_SMTP_PASSWORD = os.getenv('EMAIL_SMTP_PASSWORD', '')
    EMAIL_FROM_NAME = os.getenv('EMAIL_FROM_NAME', 'Cerealia Caviar')
    EMAIL_FROM_ADDRESS = os.getenv('EMAIL_FROM_ADDRESS', 'noreply@cerealia.com')
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'true').lower() in ('true', '1', 'yes')
    EMAIL_DEFAULT_INTERVAL = int(os.getenv('EMAIL_DEFAULT_INTERVAL', 30))
    EMAIL_DAILY_LIMIT = int(os.getenv('EMAIL_DAILY_LIMIT', 200))


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
