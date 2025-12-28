from .base import *
import os

# Security
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-prod-key-overwrite-me')

# Allowed Hosts
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

# Static Files
# On PythonAnywhere, you generally map /static/ to your STATIC_ROOT in the dashboard
# But WhiteNoise is often easier or used as a fallback
try:
    import whitenoise
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
except ImportError:
    pass

# Email Backends (Optional setup for later)
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Database
# PythonAnywhere provides connection strings or specific host/port details
# Here we keep default SQLite unless DB_NAME env var is present (for MySQL/Postgres)
if os.environ.get('DB_NAME'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('DB_NAME'),
            'USER': os.environ.get('DB_USER'),
            'PASSWORD': os.environ.get('DB_PASSWORD'),
            'HOST': os.environ.get('DB_HOST'),
            'PORT': '3306',
        }
    }

# HTTPS redirection (Recommended for Prod)
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False') == 'True'
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False') == 'True'
CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE', 'False') == 'True'

try:
    from .local import *
except ImportError:
    pass
