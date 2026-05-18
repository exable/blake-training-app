import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


def _normalize_db_url(url: str | None) -> str:
    if not url:
        return "sqlite:///blake.db"
    # Railway / Render often expose postgres:// — SQLAlchemy needs postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    JWT_SECRET_KEY = SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=30)
    SQLALCHEMY_DATABASE_URI = _normalize_db_url(os.getenv("DATABASE_URL"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL = "claude-sonnet-4-20250514"

    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")

    BLAKE_USERNAME = "blake"
    BLAKE_PASSWORD = os.getenv("BLAKE_PASSWORD", "")
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")
