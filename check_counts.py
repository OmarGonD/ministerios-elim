import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ministerios_elim.settings.base")
django.setup()

from graficos_interactivos.models import GraficoInteractivo

types = ['genealogia', 'timeline', 'diagrama', 'mapa']
for t in types:
    count = GraficoInteractivo.objects.filter(tipo=t).count()
    print(f"{t}: {count}")
