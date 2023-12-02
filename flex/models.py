from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.models import Page
from wagtail.fields import StreamField
from streams import blocks

# Create your models here.

class FlexPage(Page):
    template = 'flex/flex_page.html'

    subtype_types = ['flex.FlexPage']
   
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

    class Meta:
        verbose_name = "Flex Page"
        verbose_name_plural = "Flex Pages"
