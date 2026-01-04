import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ministerios_elim.settings.base")
django.setup()

from doctrina.models import DoctrinaEntryPage
from graficos_interactivos.models import GraficoInteractivo

# 1. Get a graph
try:
    # Prefer existing one, or any
    graph = GraficoInteractivo.objects.filter(tipo='genealogia').first()
    if not graph:
        graph = GraficoInteractivo.objects.first()
    
    if not graph:
        print("ERROR: No interactive charts found. Please run previous steps to generate them.")
        exit(1)

    print(f"Selected Graph: {graph.nombre} ({graph.tipo})")

    # 2. Get a page
    page = DoctrinaEntryPage.objects.live().first()
    
    if not page:
        print("WARNING: No live DoctrinaEntryPage found. Creating a dummy one...")
        # We need a parent. Try to find one.
        from doctrina.models import DoctrinaBasicaPage, DoctrinaIndexPage
        from home.models import HomePage
        
        parent = DoctrinaBasicaPage.objects.first()
        if not parent:
             # Try to find or create index/home path... this might be complex if empty DB.
             # Assume at least home exists
             home = HomePage.objects.first()
             if home:
                 # Create basic page under home
                 parent = DoctrinaBasicaPage(title="Doctrina Básica", slug="doctrina-basica")
                 home.add_child(instance=parent)
                 parent.save_revision().publish()
        
        if parent:
            page = DoctrinaEntryPage(
                title="Entrada de Prueba con Gráfico", 
                body="<p>Esta es una entrada para probar los gráficos interactivos.</p>",
                slug="entrada-prueba-grafico"
            )
            parent.add_child(instance=page)
            page.save_revision().publish()
    
    if not page:
         print("ERROR: Could not find or create a page.")
         exit(1)

    print(f"Selected Page: {page.title} (URL: {page.url})")

    # 3. Add graph to page
    page.graficos_embebidos.add(graph)
    page.graficos_position = 'after_body' # Explicitly set position
    page.save_revision().publish()
    
    print(f"SUCCESS: Added graph '{graph.nombre}' to page '{page.title}'")

except Exception as e:
    print(f"ERROR: {e}")
