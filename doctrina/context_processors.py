# Ejemplo de context processor
from doctrina.models import DoctrinaBasicaPage, DoctrinaIntermediaPage, DoctrinaAvanzadaPage, DoctrinaIndexPage

def doctrinas_pages(request):
    return {
        'doctrina_index_page': DoctrinaIndexPage.objects.live().first(),
        'doctrina_basica_page': DoctrinaBasicaPage.objects.live().first(),
        'doctrina_intermedia_page': DoctrinaIntermediaPage.objects.live().first(),
        'doctrina_avanzada_page': DoctrinaAvanzadaPage.objects.live().first(),
    }

