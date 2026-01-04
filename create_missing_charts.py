import os
import django
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ministerios_elim.settings.base")
django.setup()

from graficos_interactivos.models import GraficoInteractivo

# 1. Diagrama: Jerarquía de la Iglesia
diagrama_data = {
    "nodes": [
        {"id": 1, "name": "Pastor General"},
        {"id": 2, "name": "Pastores Asociados"},
        {"id": 3, "name": "Diáconos"},
        {"id": 4, "name": "Obreros"},
        {"id": 5, "name": "Líderes de Grupo"},
        {"id": 6, "name": "Membresía"}
    ],
    "links": [
        {"source": 1, "target": 2},
        {"source": 2, "target": 3},
        {"source": 2, "target": 4},
        {"source": 3, "target": 5},
        {"source": 4, "target": 5},
        {"source": 5, "target": 6}
    ]
}

GraficoInteractivo.objects.get_or_create(
    slug='jerarquia-iglesia',
    defaults={
        'nombre': 'Jerarquía de la Iglesia',
        'tipo': 'diagrama',
        'descripcion': 'Estructura organizativa básica.',
        'datos_json': diagrama_data,
        'activo': True
    }
)
print("Diagrama 'Jerarquía de la Iglesia' created or already exists.")

# 2. Mapa: Primer Viaje de Pablo (Approximate coords)
# Antioquía: 36.2021, 36.1609
# Salamina: 35.1681, 33.9015
# Pafos: 34.7758, 32.4245
# Perge: 36.9602, 30.8524
# Iconio (Konya): 37.8746, 32.4932
# Listra: 37.5667, 32.2
# Derbe: 37.3486, 33.0567

mapa_data = {
    "center": [36.0, 33.0],
    "zoom": 6,
    "markers": [
        {"name": "Antioquía", "coords": [36.2021, 36.1609], "description": "Inicio del viaje"},
        {"name": "Salamina", "coords": [35.1681, 33.9015], "description": "Predicación en Chipre"},
        {"name": "Pafos", "coords": [34.7758, 32.4245], "description": "Encuentro con Elimas"},
        {"name": "Perge", "coords": [36.9602, 30.8524], "description": "Juan Marcos regresa"},
        {"name": "Iconio", "coords": [37.8746, 32.4932], "description": "Muchos creen"},
        {"name": "Listra", "coords": [37.5667, 32.2], "description": "Pablo apedreado"},
        {"name": "Derbe", "coords": [37.3486, 33.0567], "description": "Muchos discípulos"}
    ],
    "routes": [
        {
            "name": "Ruta de Ida",
            "color": "#d4af37",
            "coords": [
                [36.2021, 36.1609], # Antioquia
                [35.1681, 33.9015], # Salamina
                [34.7758, 32.4245], # Pafos
                [36.9602, 30.8524], # Perge
                [37.8746, 32.4932], # Iconio
                [37.5667, 32.2],    # Listra
                [37.3486, 33.0567]  # Derbe
            ]
        }
    ]
}

GraficoInteractivo.objects.get_or_create(
    slug='primer-viaje-pablo',
    defaults={
        'nombre': 'Primer Viaje Misionero de Pablo',
        'tipo': 'mapa',
        'descripcion': 'Recorrido del primer viaje apostólico.',
        'datos_json': mapa_data,
        'activo': True
    }
)
print("Mapa 'Primer Viaje Misionero de Pablo' created or already exists.")
