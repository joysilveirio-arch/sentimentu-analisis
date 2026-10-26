import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'facebook_analytics.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Allow SQLite to wait for short-lived locks from concurrent app requests
    # or database inspection tools instead of failing immediately.
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"timeout": 30}}
    UPLOAD_FOLDER = str(BASE_DIR / "uploads")
    MODEL_FOLDER = str(BASE_DIR / "models")
    LOG_FOLDER = str(BASE_DIR / "logs")
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {"csv"}
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    ITEMS_PER_PAGE = 20
    ML_MAX_FEATURES = 5000
    ML_MIN_DF = 1
    ML_MAX_DF = 0.95
    ML_NGRAM_RANGE = (1, 2)
    ML_TEST_SIZE = 0.2
    ML_RANDOM_STATE = 42
    ML_MAX_DEPTH = 15

for _folder in [Config.UPLOAD_FOLDER, Config.MODEL_FOLDER, Config.LOG_FOLDER]:
    os.makedirs(_folder, exist_ok=True)
