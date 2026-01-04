import os
import django
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ministerios_elim.settings.base")
django.setup()

from graficos_interactivos.models import GraficoInteractivo

try:
    g = GraficoInteractivo.objects.get(tipo='genealogia')
    print(f"Chart: {g.nombre}")
    nodes = g.datos_json.get('nodes', [])
    print(f"Node count: {len(nodes)}")
    print("Nodes:")
    for n in nodes:
        print(f"- {n.get('name')} (ID: {n.get('id')}, Parent: {n.get('parent_id')})")
except GraficoInteractivo.DoesNotExist:
    print("No genealogy chart found.")
except Exception as e:
    print(f"Error: {e}")
