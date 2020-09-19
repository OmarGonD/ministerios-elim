import os
import sys

import dotenv
from django.core.wsgi import get_wsgi_application

dotenv.read_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))


path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print("##########")
print("WSGI")
print(path)
print("##########")

if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

application = get_wsgi_application()
