import os
import django
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ministerios_elim.settings.dev")
django.setup()

from graficos_interactivos.models import GraficoInteractivo

try:
    chart = GraficoInteractivo.objects.get(slug='genealogia-jesus-mateo')
    print("Node names found:")
    for node in chart.datos_json.get('nodes', []):
        print(f"ID: {node.get('id')}, Name: '{node.get('name')}'")
        if 'jes' in node.get('name', '').lower():
            print(f"--> Potential Match Found: {node.get('name')}")
except Exception as e:
    print(f"Error: {e}")
