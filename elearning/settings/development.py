"""Development settings — DEBUG on, SQLite optional fallback."""
from decouple import config

from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Use a fixed secret key in development for convenience; override via .env if desired
SECRET_KEY = config("DJANGO_SECRET_KEY", default="dev-insecure-secret-key-change-in-production")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="elearning_db"),
        "USER": config("DB_USER", default="elearning_user"),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

# In development, media/static files are served by Django's dev server
INTERNAL_IPS = ["127.0.0.1"]
