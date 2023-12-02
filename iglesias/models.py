from django.db import models

# Create your models here.
from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.models import Page
from wagtail.fields import StreamField
from streams import blocks
from wagtail.admin.panels import FieldPanel
#from wagtailgmaps.edit_handlers import MapFieldPanel

from wagtail.admin.panels import (
    MultiFieldPanel,
    InlinePanel,
    FieldPanel,
    PageChooserPanel
)

from django.conf import settings

# Create your models here.

from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.models import Page
from wagtail.fields import StreamField
from streams import blocks

from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager

from taggit.models import TaggedItemBase


# Create your models here.

class IglesiasListingPage(Page): #Muestra todas las iglesias en Perú

    '''Lista las categorías de doctrina: básica, intermedia y avanzada'''

    template = 'iglesias/iglesias_listing_page.html'
    max_count = 1 # Solo se puede añadir 1 vez al sitio
    subpage_types = ['iglesias.IglesiaPage']
   
    # @todo add streamfields
    '''El primer argumento no tiene que hacer match con nada, es solo para referencia interna de Wagtail'''
    content = StreamField(
        [
            ("title_and_text", blocks.TitleAndTextBlock(classname='text_and_title')),
            ("full_richtext", blocks.RichtextBlock()),
            ("simple_richtext", blocks.SimpleRichtextBlock()),
            ("cards", blocks.CardBlock()),
            ("cta", blocks.CTABlock()),
        ],
        null=True,
        blank=True,
        use_json_field=True,
    )


    subtitle = models.CharField(max_length=100, null=True, blank=True)


    content_panels = Page.content_panels + [
        FieldPanel('subtitle'),
        FieldPanel('content'),
    ]

    def get_context(self, request, *args, **kwargs):

        context = super().get_context(request, *args, **kwargs)

        all_churches = IglesiaPage.objects.child_of(self).live().public()

        if request.GET.get('tag', None):
            tags = request.GET.get('tag')
            all_churches = all_churches.filter(tags__slug__in=[tags])

        context['iglesias_totales'] = all_churches
        return context

    class Meta:
        verbose_name = "Iglesias"
        verbose_name_plural = "Iglesias"





class IglesiaPage(Page): # Modelo de cada iglesia individual: pastor, direccion, etc.

    template = 'iglesias/iglesia_page.html'

    parent_page_types = ['iglesias.IglesiasListingPage']

    subpage_types = ['iglesias.IglesiaEventosPage']
    
    custom_title = models.CharField(
        max_length=250,
        blank=False,
        null=False,
        help_text='Sobreescribe el título de la entrada'
    )

    pastor  = models.ForeignKey( 
        "ministros.PastorPage",
        blank=False,
        null=True,
        related_name="+",
        on_delete=models.SET_NULL,

    )


    church_image = models.ForeignKey( #imagen del nivel de doctrina: basico, int, avanzado
        "wagtailimages.Image",
        blank=True,
        null=True,
        related_name="+",
        on_delete=models.SET_NULL,

    )

    address = models.CharField(
        max_length=250,
        blank=False,
        null=False,
        help_text='Dirección de la iglesia'
    )


    address_reference = models.CharField(
        max_length=250,
        blank=True,
        null=True,
        help_text='Referencia de la dirección de la iglesia (opcional).'
    )

    formatted_address = models.CharField(max_length=255)
    latlng_address = models.CharField(max_length=255)

    phone = models.CharField(
        max_length=250,
        blank=True,
        null=True,
        help_text='Teléfono de la iglesia'
    )

    
    email = models.EmailField(
        max_length=250,
        blank=True,
        null=True,
        help_text='Correo electrónico de la iglesia'
    )

    content = StreamField(
        [
            ("title_and_text", blocks.TitleAndTextBlock(classname='text_and_title')),
            ("full_richtext", blocks.RichtextBlock()),
            ("simple_richtext", blocks.SimpleRichtextBlock()),
            ("cards", blocks.CardBlock()),
            ("cta", blocks.CTABlock()),
        ],
        null=True,
        blank=True,
        use_json_field=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel('custom_title'),
        FieldPanel('pastor'),
        FieldPanel('address'),
        FieldPanel('address_reference'),
        FieldPanel('phone'),
        FieldPanel('email'),
        FieldPanel('church_image'),
        FieldPanel('content'),
    ]

    


    def get_context(self, request, *args, **kwargs):

        context = super().get_context(request, *args, **kwargs)

        all_church_events = IglesiaEventosPage.objects.child_of(self).live().public()


        if request.GET.get('tag', None):
            tags = request.GET.get('tag')
            all_church_events = all_church_events.filter(tags__slug__in=[tags])

        pastor = self.pastor

        context['iglesia_eventos'] = all_church_events
        context['pastor'] = pastor
        context['WAGTAIL_ADDRESS_MAP_KEY'] = settings.WAGTAIL_ADDRESS_MAP_KEY
        return context




class IglesiaPageTag(TaggedItemBase):
    content_object = ParentalKey(
        'IglesiaEventosPage',
        related_name='tagged_items',
        on_delete=models.CASCADE,
    )



class IglesiaEventosPage(Page): # Eventos de la iglesia

    subpage_types = []
    tags = ClusterTaggableManager(through=IglesiaPageTag, blank=True)

    parent_page_types = ['iglesias.IglesiaPage']

    custom_title = models.CharField(
        max_length=250,
        blank=False,
        null=False,
        help_text='Sobreescribe el título de la entrada'
    )

    event_image = models.ForeignKey(
        "wagtailimages.Image",
        blank=False,
        null=True,
        related_name="+",
        on_delete=models.SET_NULL,

    )

    content = StreamField(
        [
            ("title_and_text", blocks.TitleAndTextBlock(classname='text_and_title')),
            ("full_richtext", blocks.RichtextBlock()),
            ("simple_richtext", blocks.SimpleRichtextBlock()),
            ("cards", blocks.CardBlock()),
            ("cta", blocks.CTABlock()),
        ],
        null=True,
        blank=True,
        use_json_field=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel('custom_title'),
        FieldPanel('tags'),
        FieldPanel('event_image'),
        FieldPanel('content'),
    ]



