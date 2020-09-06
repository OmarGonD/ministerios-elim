from __future__ import absolute_import, unicode_literals
from .base import *
import dj_database_url
import os
from decouple import config





STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

COMPRESS_OFFLINE = True

COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter',
]


#Honor the 'X-Forwareded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWAREDED_PROTO', 'http')

ALLOWED_HOSTS = ['127.0.0.1', 'ministerios-elim.herokuapp.com']

MEDIA_URL = "https://%s/" % AWS_S3_CUSTOM_DOMAIN
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'


try:
    from .local import *
except ImportError:
    pass



