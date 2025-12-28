"""
Base settings for ministerios-elim project.
Common configuration shared by all environments.
"""

import os
from pathlib import Path

# ----------------------------------------------------------------------
# Build paths
# ----------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_DIR = Path(__file__).resolve().parent

# ----------------------------------------------------------------------
# Security (will be overridden in dev/prod)
# ----------------------------------------------------------------------
SECRET_KEY = "replace-me-with-a-real-secret-key"
DEBUG = False
ALLOWED_HOSTS = []

# ----------------------------------------------------------------------
# Application definition
# ----------------------------------------------------------------------
INSTALLED_APPS = [
    # Django core
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Wagtail
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",

    # Third-party
    "modelcluster",
    "taggit",
    "django_filters",
    "django_countries",
    "social_django",

    # Local apps
    "doctrina.apps.DoctrinaConfig",
    "home",
    "search",
    "iglesias.apps.IglesiasConfig",
    "pastores.apps.PastoresConfig",
    "miembros.apps.MiembrosConfig",
    "foros.apps.ForosConfig",
]

# ----------------------------------------------------------------------
# Middleware
# ----------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

# ----------------------------------------------------------------------
# URLs
# ----------------------------------------------------------------------
ROOT_URLCONF = "ministerios_elim.urls"

# ----------------------------------------------------------------------
# Templates
# ----------------------------------------------------------------------
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
                "django.template.context_processors.i18n",
                "doctrina.context_processors.doctrinas_pages",
                "home.context_processors.countries_list",
            ],
        },
    },
]

WSGI_APPLICATION = "ministerios_elim.wsgi.application"

# ----------------------------------------------------------------------
# Database (default SQLite – override in dev/prod if needed)
# ----------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ----------------------------------------------------------------------
# Password validation
# ----------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ----------------------------------------------------------------------
# Internationalization
# ----------------------------------------------------------------------
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = True

# ----------------------------------------------------------------------
# Static files (CSS, JavaScript, Images)
# ----------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# ----------------------------------------------------------------------
# Media files
# ----------------------------------------------------------------------
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ----------------------------------------------------------------------
# Storages (use Manifest only in prod – dev overrides this)
# ----------------------------------------------------------------------
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# ----------------------------------------------------------------------
# Wagtail settings
# ----------------------------------------------------------------------
WAGTAIL_SITE_NAME = "Ministerios Elim"
WAGTAILADMIN_BASE_URL = "http://localhost:8000"
WAGTAILADMIN_USER_AVATAR = None  # Disable Gravatar

WAGTAILSEARCH_BACKENDS = {
    "default": {"BACKEND": "wagtail.search.backends.database"}
}

WAGTAILDOCS_EXTENSIONS = [
    "csv", "docx", "key", "odt", "pdf", "pptx", "rtf", "txt", "xlsx", "zip"
]
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10_000

# ----------------------------------------------------------------------
# Social Auth
# ----------------------------------------------------------------------
AUTHENTICATION_BACKENDS = (
    "social_core.backends.google.GoogleOAuth2",
    "django.contrib.auth.backends.ModelBackend",
)

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = "TU_CLIENT_ID"
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = "TU_CLIENT_SECRET"
LOGIN_URL = "login"
LOGOUT_URL = "logout"
LOGIN_REDIRECT_URL = "/"

# ----------------------------------------------------------------------
# Content Security Policy (optional – can be overridden)
# ----------------------------------------------------------------------
CSP_DEFAULT_SRC = ("'self'",)
CSP_IMG_SRC = ("'self'", "data:", "https://secure.gravatar.com")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_SRC = ("'self'",)
CSP_OBJECT_SRC = ("'none'",)