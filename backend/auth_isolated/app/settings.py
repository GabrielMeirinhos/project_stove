from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[3]
DOTENV_PATH = ROOT_DIR / ".env"
load_dotenv(DOTENV_PATH, override=False)

MODULE_DIR = ROOT_DIR / "backend" / "auth_isolated"
DATA_DIR = MODULE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = Path(os.getenv("AUTH_DB_PATH", str(DATA_DIR / "auth.sqlite3")))
APP_NAME = "Gaia Auth System"
APP_BASE_URL = os.getenv("AUTH_APP_BASE_URL", "http://localhost:5173")
API_PREFIX = "/api"
SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "change-me")
TOKEN_TTL_MINUTES = int(os.getenv("AUTH_TOKEN_TTL_MINUTES", "720"))
INVITE_TTL_HOURS = int(os.getenv("AUTH_INVITE_TTL_HOURS", "72"))
RESET_TTL_HOURS = int(os.getenv("AUTH_RESET_TTL_HOURS", "12"))
FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
DEFAULT_ADMIN_NAME = os.getenv("DEFAULT_ADMIN_NAME", "Administrador Gaia")
DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@gaia.com")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "gaia123")
DEFAULT_USER_NAME = os.getenv("DEFAULT_USER_NAME", "Usuario Gaia")
DEFAULT_USER_EMAIL = os.getenv("DEFAULT_USER_EMAIL", "usuario@gaia.com")
DEFAULT_USER_PASSWORD = os.getenv("DEFAULT_USER_PASSWORD", "gaia123")
