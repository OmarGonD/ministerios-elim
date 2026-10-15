from .base import *
import os

# Security
DEBUG = False
SECRET_KEY = os.environ['SECRET_KEY']

# Allowed Hosts
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

# Static Files
# On PythonAnywhere, you generally map /static/ to your STATIC_ROOT in the dashboard
# But WhiteNoise is often easier or used as a fallback
try:
    import whitenoise
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
    STORAGES['staticfiles'] = {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    }
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
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True') == 'True'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '31536000'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
X_FRAME_OPTIONS = 'DENY'

CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if origin.strip()
]
WAGTAILADMIN_BASE_URL = os.environ.get('WAGTAILADMIN_BASE_URL', 'https://' + ALLOWED_HOSTS[0])
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', '')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', '')

try:
    from .local import *
except ImportError:
    pass
