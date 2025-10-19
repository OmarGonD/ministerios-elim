from django.apps import AppConfig


class ForosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'foros'
    verbose_name = 'Foros / Debates'
    
    def ready(self):
        # Import signal handlers to ensure they are registered
        try:
            from . import signals  # noqa: F401
        except Exception:
            # Avoid crashing import-time if signals fail during test/discovery
            pass
