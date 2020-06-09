from __future__ import absolute_import, unicode_literals
from .base import *
import dj_database_url
import os

env = os.environ.copy()
SECRET_KEY = env['SECRET_KEY']

DEBUG = False

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

COMPRESS_OFFLINE = True

COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter',
]


#Parse databse configuration from $DATABASE_URL
DATABASES['default'] = dj_database_url.config()

#Honor the 'X-Forwareded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWAREDED_PROTO', 'http')

ALLOWED_HOSTS = ['*']


try:
    from .local import *
except ImportError:
    pass
