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
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "core.apps.CoreConfig",
]

MIDDLEWARE = [
    "core.api.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "conf.urls"
WSGI_APPLICATION = "conf.wsgi.application"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": [],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
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
        "NAME": os.environ.get("MEPRAM_DB_NAME", "mepram_omop_api"),
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

MEPRAM_AUTH_REQUIRED = os.environ.get("MEPRAM_AUTH_REQUIRED", "true").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
MEPRAM_DOCS_REQUIRE_STAFF = os.environ.get(
    "MEPRAM_DOCS_REQUIRE_STAFF", "true"
).lower() in {"1", "true", "yes", "on"}
MEPRAM_CREATE_DEFAULT_SUPERUSER = os.environ.get(
    "MEPRAM_CREATE_DEFAULT_SUPERUSER", "false"
).lower() in {"1", "true", "yes", "on"}
DJANGO_SUPERUSER_USERNAME = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
DJANGO_SUPERUSER_EMAIL = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.org")
DJANGO_SUPERUSER_PASSWORD = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "admin_pass")
MEPRAM_KEYCLOAK_ISSUER = os.environ.get("MEPRAM_KEYCLOAK_ISSUER", "")
MEPRAM_KEYCLOAK_JWKS_URL = os.environ.get("MEPRAM_KEYCLOAK_JWKS_URL", "")
MEPRAM_KEYCLOAK_AUDIENCE = os.environ.get("MEPRAM_KEYCLOAK_AUDIENCE", "mepram-api")
MEPRAM_KEYCLOAK_CLIENT_ID = os.environ.get("MEPRAM_KEYCLOAK_CLIENT_ID", "pathocore-web")
MEPRAM_KEYCLOAK_JWKS_CACHE_TTL_SECONDS = int(
    os.environ.get("MEPRAM_KEYCLOAK_JWKS_CACHE_TTL_SECONDS", "300")
)
MEPRAM_KEYCLOAK_JWKS_TIMEOUT_SECONDS = int(
    os.environ.get("MEPRAM_KEYCLOAK_JWKS_TIMEOUT_SECONDS", "5")
)

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        ["core.api.authentication.KeycloakJWTAuthentication"]
        if MEPRAM_AUTH_REQUIRED
        else []
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        ["rest_framework.permissions.IsAuthenticated"]
        if MEPRAM_AUTH_REQUIRED
        else ["rest_framework.permissions.AllowAny"]
    ),
    "UNAUTHENTICATED_USER": None,
    "UNAUTHENTICATED_TOKEN": None,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '500/hour',
        'user': '500/hour'
    }
}

SPECTACULAR_SETTINGS = {
    "TITLE": "MePRAM API",
    "DESCRIPTION": (
        "Read-only API for aggregated MePRAM dashboard data. "
        "Data endpoints are protected with Bearer JWT authentication when "
        "MEPRAM_AUTH_REQUIRED is enabled."
    ),
    "VERSION": None,
    "SERVE_INCLUDE_SCHEMA": True,
    "SCHEMA_PATH_PREFIX": "/v[0-9]+",
    "SCHEMA_PATH_PREFIX_TRIM": True,
    "SERVERS": [{"url": "/v1", "description": "MePRAM API v1"}],
    "SORT_OPERATIONS": False,
    "SECURITY": [{"bearerAuth": []}] if MEPRAM_AUTH_REQUIRED else [],
}

STATIC_ROOT = BASE_DIR / "static"
LOGIN_URL = "/admin/login/"
