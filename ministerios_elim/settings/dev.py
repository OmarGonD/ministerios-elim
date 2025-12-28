# settings/dev.py

from .base import *
import os


# Email en consola
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Asegura carpetas
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'media'
os.makedirs(STATIC_ROOT, exist_ok=True)
os.makedirs(MEDIA_ROOT, exist_ok=True)

# Carga local.py si existe
try:
    from .local import *
except ImportError:
    pass


# Desarrollo
DEBUG = True  # ← ¡IMPORTANTE!

# Permitir todos los hosts en desarrollo
ALLOWED_HOSTS = ['*']

# CSRF Trusted Origins due to strict checking in recent Django versions
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]