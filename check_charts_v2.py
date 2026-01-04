import os
import django
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ministerios_elim.settings.base")
django.setup()

from graficos_interactivos.models import GraficoInteractivo

charts = GraficoInteractivo.objects.all()

if not charts:
    print("No interactive charts found.")
else:
    print(f"Found {charts.count()} charts:")
    for chart in charts:
        print(f"- Name: '{chart.nombre}', Type: '{chart.tipo}', Slug: '{chart.slug}'")
        # Check if data looks valid (simple check)
        if not chart.datos_json:
            print("  WARNING: Data is empty!")
        else:
            print(f"  Data keys: {list(chart.datos_json.keys())}")
            if chart.tipo == 'genealogia':
                print(f"  Nodes count: {len(chart.datos_json.get('nodes', []))}")
            elif chart.tipo == 'timeline':
                print(f"  Events count: {len(chart.datos_json.get('events', []))}")
