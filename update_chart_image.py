import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ministerios_elim.settings.dev")
django.setup()

from graficos_interactivos.models import GraficoInteractivo

def update_chart_image():
    try:
        chart = GraficoInteractivo.objects.get(slug='genealogia-jesus-mateo')
        data = chart.datos_json
        
        updated = False
        for node in data.get('nodes', []):
            if node.get('name') == "JESUCRISTO":
                node['img'] = '/media/jesus_genealogia.png'
                updated = True
                break
        
        if updated:
            chart.datos_json = data
            chart.save()
            print("Successfully updated Jesus image in genealogy chart.")
        else:
            print("Jesus node not found in chart data.")
            
    except GraficoInteractivo.DoesNotExist:
        print("Chart not found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_chart_image()
