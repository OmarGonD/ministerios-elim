import os
import django
import datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ministerios_elim.settings.dev")
django.setup()

from django.contrib.auth import get_user_model
from doctrina.models import DoctrinaBasicaPage, DoctrinaEntryPage
from graficos_interactivos.models import GraficoInteractivo

def create_page():
    User = get_user_model()
    
    # 1. Fetch Dependencies
    try:
        user = User.objects.get(username='pastor_demo')
    except User.DoesNotExist:
        print("Error: User 'pastor_demo' not found.")
        return

    try:
        parent = DoctrinaBasicaPage.objects.get(slug='doctrina-basica')
    except DoctrinaBasicaPage.DoesNotExist:
        print("Error: Parent page 'Doctrina Básica' not found.")
        return

    try:
        chart = GraficoInteractivo.objects.filter(tipo='genealogia').first()
        if not chart:
            print("Error: Genealogia chart not found.")
            return
    except Exception as e:
        print(f"Error finding chart: {e}")
        return

    # 2. Define Content
    title = "La Genealogía del Mesías: Cumplimiento de las Promesas"
    
    body_html = """
    <h2>Introducción</h2>
    <p>La genealogía de Jesucristo no es simplemente una lista de nombres; es el mapa histórico del cumplimiento de las promesas de Dios. A través de los siglos, Dios prometió que el Salvador vendría de un linaje específico, demostrando que Él es el Señor de la historia.</p>
    
    <h2>1. La Promesa a Abraham</h2>
    <p>Dios llamó a Abraham y le prometió que en su simiente serían benditas todas las familias de la tierra.</p>
    <blockquote>
        "En tu simiente serán benditas todas las naciones de la tierra, por cuanto obedeciste a mi voz." 
        <br><strong>(Génesis 22:18)</strong>
    </blockquote>
    <p><strong>Cumplimiento:</strong> El Evangelio de Mateo comienza estableciendo esta conexión vital:</p>
    <blockquote>
        "Libro de la genealogía de Jesucristo, hijo de David, hijo de Abraham."
        <br><strong>(Mateo 1:1)</strong>
    </blockquote>

    <h2>2. La Tribu de Judá</h2>
    <p>De los doce hijos de Jacob, la profecía señaló específicamente a la tribu de Judá como la portadora del cetro real.</p>
    <blockquote>
        "No será quitado el cetro de Judá, Y el legislador de entre sus pies, Hasta que venga Siloh; Y a él se congregarán los pueblos."
        <br><strong>(Génesis 49:10)</strong>
    </blockquote>
    <p><strong>Cumplimiento:</strong> El autor de Hebreos confirma la descendencia del Señor:</p>
    <blockquote>
        "Porque manifiesto es que nuestro Señor vino de la tribu de Judá, de la cual nada habló Moisés tocante al sacerdocio."
        <br><strong>(Hebreos 7:14)</strong>
    </blockquote>

    <h2>3. El Pacto Davídico</h2>
    <p>La promesa más específica se hizo al Rey David: su trono sería establecido para siempre mediante un descendiente eterno.</p>
    <blockquote>
        "Y cuando tus días sean cumplidos, y duermas con tus padres, yo levantaré después de ti a uno de tu linaje... y afirmaré el trono de su reino para siempre."
        <br><strong>(2 Samuel 7:12-13)</strong>
    </blockquote>
    <p><strong>Cumplimiento:</strong> El ángel Gabriel anunció a María:</p>
    <blockquote>
        "Éste será grande, y será llamado Hijo del Altísimo; y el Señor Dios le dará el trono de David su padre."
        <br><strong>(Lucas 1:32)</strong>
    </blockquote>

    <h2>Conclusión</h2>
    <p>La genealogía presenta la evidencia legal y biológica de que Jesús es el Mesías prometido, el León de la tribu de Judá y la Raíz de David. Explora el gráfico interactivo a continuación para ver visualmente este linaje sagrado.</p>
    """

    # 3. Create Page Object
    page = DoctrinaEntryPage(
        title=title,
        slug='genealogia-del-mesias', # Explicit slug
        body=body_html,
        date=datetime.date.today(),
        created_by=user,
        owner=user, # Important for Wagtail ownership
        abstract="Un estudio sobre cómo la genealogía de Jesús cumple las profecías del Antiguo Testamento dado a Abraham, Judá y David.",
        graficos_position='after_body' # Explicitly set position
    )

    # 4. Add to Tree
    parent.add_child(instance=page)
    
    # 5. Add Many-to-Many Relationship (Must be done after saving/adding to tree)
    page.save() # Ensure ID exists
    page.graficos_embebidos.add(chart)
    page.save()
    
    # 6. Publish
    page.save_revision().publish()
    
    print(f"Successfully created page: '{title}' (ID: {page.id}) under '{parent.title}'")

if __name__ == "__main__":
    create_page()
