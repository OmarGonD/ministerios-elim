# doctrina/apps.py
from django.apps import AppConfig

class DoctrinaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'doctrina'

    def ready(self):
        import doctrina.signals  # noqa