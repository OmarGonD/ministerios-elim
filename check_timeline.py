import os
import django
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ministerios_elim.settings.base")
django.setup()

from graficos_interactivos.models import GraficoInteractivo

try:
    charts = GraficoInteractivo.objects.filter(tipo='timeline')
    for g in charts:
        print(f"Chart: {g.nombre}")
        events = g.datos_json.get('events', [])
        print(f"Event count: {len(events)}")
        for e in events:
            print(f"- {e.get('name')} (Type: {e.get('type')})")
except Exception as e:
    print(f"Error: {e}")
