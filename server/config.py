"""配置层：集中管理数据库、密钥与启动参数，全部从 server/.env 读取。"""
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# 加载同目录下的 .env
load_dotenv(BASE_DIR / ".env")


def _env_bool(key, default=False):
    """把环境变量转成布尔值。"""
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


class Config:
    """项目配置。同名的环境变量优先级最高。"""

    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "yunmo")
    DB_CHARSET = os.getenv("DB_CHARSET", "utf8mb4")

    # 未配置时随机生成，保证开发环境可用（生产环境必须固定，否则已签发的 token 会立即失效）
    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)
    TOKEN_EXPIRE_SECONDS = int(os.getenv("TOKEN_EXPIRE_SECONDS", str(7 * 24 * 3600)))

    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # 邮件服务：用于发送注册 / 换绑邮箱的验证码
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.qq.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "465"))
    MAIL_USE_SSL = _env_bool("MAIL_USE_SSL", True)
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "番剧同好会")
    # 未配置发信账号时不发信，验证码改为输出到后端控制台，保证本地也能跑通注册流程
    MAIL_ENABLED = bool(MAIL_USERNAME and MAIL_PASSWORD)

    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5000"))
    DEBUG = _env_bool("DEBUG", True)