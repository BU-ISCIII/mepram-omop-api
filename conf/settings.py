from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("MEPRAM_API_SECRET_KEY", "dev-only-mepram-api")
DEBUG = os.environ.get("MEPRAM_API_DEBUG", "true").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "MEPRAM_API_ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0"
    ).split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "core.apps.CoreConfig",
]

MIDDLEWARE = [
    "core.api.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "conf.urls"
WSGI_APPLICATION = "conf.wsgi.application"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": [],
        "OPTIONS": {"context_processors": []},
    }
]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "HOST": os.environ.get("MEPRAM_DB_HOST", "localhost"),
        "PORT": os.environ.get("MEPRAM_DB_PORT", "3306"),
        "NAME": os.environ.get("MEPRAM_DB_NAME", "mepram_api"),
        "USER": os.environ.get("MEPRAM_DB_USER", "mepram"),
        "PASSWORD": os.environ.get("MEPRAM_DB_PASSWORD", "mepram_password"),
        "OPTIONS": {"charset": "utf8mb4"},
    }
}

MEPRAM_DASHBOARD_SCHEMA = os.environ.get(
    "MEPRAM_DASHBOARD_SCHEMA", DATABASES["default"]["NAME"]
)
MEPRAM_CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "MEPRAM_CORS_ALLOWED_ORIGINS",
        "http://127.0.0.1:3000,http://localhost:3000",
    ).split(",")
    if origin.strip()
]

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "UNAUTHENTICATED_USER": None,
    "UNAUTHENTICATED_TOKEN": None,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "MePRAM API",
    "DESCRIPTION": "Read-only API for aggregated MePRAM dashboard data.",
    "VERSION": None,
    "SERVE_INCLUDE_SCHEMA": True,
    "SCHEMA_PATH_PREFIX": "/v[0-9]+",
    "SCHEMA_PATH_PREFIX_TRIM": True,
    "SERVERS": [{"url": "/v1", "description": "MePRAM API v1"}],
    "SORT_OPERATIONS": False,
}
