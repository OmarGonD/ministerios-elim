from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'm6za9i-lu-)!#)a_u6r%9!_$k&67mzz^t@07ea0bl@ntv0j^)j'

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ['*'] 

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'



INTERNAL_IPS = ("127.0.0.1")

try:
    from .local import *
except ImportError:
    pass
