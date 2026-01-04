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
    for chart in charts:
        print(f"Chart: {chart.nombre} (Type: {chart.tipo})")
        print(f"Data: {json.dumps(chart.datos_json, indent=2)}")
        print("-" * 20)
