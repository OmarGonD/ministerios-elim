# Ejemplo de context processor
from doctrina.models import DoctrinaBasicaPage, DoctrinaIntermediaPage, DoctrinaAvanzadaPage

def doctrinas_pages(request):
    return {
        'doctrina_basica_page': DoctrinaBasicaPage.objects.live().first(),
        'doctrina_intermedia_page': DoctrinaIntermediaPage.objects.live().first(),
        'doctrina_avanzada_page': DoctrinaAvanzadaPage.objects.live().first(),
    }

