import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ministerios_elim.settings.base")
django.setup()

from doctrina.models import DoctrinaEntryPage

page = DoctrinaEntryPage.objects.get(title="Los Dones del Espíritu Santo")
graphs = page.graficos_embebidos.all()
print(f"Page: {page.title}")
print(f"Graphs count: {graphs.count()}")
for g in graphs:
    print(f"- {g.nombre} ({g.tipo})")
