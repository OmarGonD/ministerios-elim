import os
from django.apps import AppConfig


class IglesiasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'iglesias'
    verbose_name = 'Iglesias'
    path = os.path.dirname(os.path.abspath(__file__))
