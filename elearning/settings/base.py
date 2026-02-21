"""Base Django settings shared across all environments."""
from pathlib import Path

from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("DJANGO_SECRET_KEY")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "markdownify.apps.MarkdownifyConfig",
    # Local apps
    "apps.accounts",
    "apps.quizzes",
    "apps.enrolments",
    "apps.reporting",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "elearning.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "elearning.wsgi.application"

# Custom user model
AUTH_USER_MODEL = "accounts.User"

# Authentication URLs
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/quizzes/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Media files (uploaded images)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Internationalisation
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Authentication backends — ModelBackend is needed for Django admin and
# for the manual login() call in the OAuth callback view.
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

# Platform identity (shown on certificates)
PLATFORM_NAME = config("PLATFORM_NAME", default="E-Learning Platform")

# Microsoft Entra ID OAuth credentials
ENTRA_CLIENT_ID = config("ENTRA_CLIENT_ID", default="")
ENTRA_CLIENT_SECRET = config("ENTRA_CLIENT_SECRET", default="")
ENTRA_TENANT_ID = config("ENTRA_TENANT_ID", default="")

# django-markdownify: allowed HTML tags/attrs when rendering Markdown
MARKDOWNIFY = {
    "default": {
        "WHITELIST_TAGS": [
            "h1", "h2", "h3", "h4", "h5", "h6",
            "p", "a", "abbr", "b", "blockquote", "br",
            "code", "em", "i", "li", "ol", "pre",
            "strong", "ul", "img", "hr", "table",
            "thead", "tbody", "tr", "th", "td",
        ],
        "WHITELIST_ATTRS": ["href", "src", "alt", "title", "class"],
        "WHITELIST_PROTOCOLS": ["http", "https"],
        "STRIP": True,
        "MARKDOWN_EXTENSIONS": ["fenced_code", "codehilite", "tables"],
        "BLEACH": True,
    }
}
