from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

from wagtail.admin.panels import (
    FieldPanel,
    FieldRowPanel,
    InlinePanel,
    MultiFieldPanel,
    PageChooserPanel,
    FieldPanel,
)
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Collection, Page
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from django.conf import settings
from django.db import models

from streams import blocks


from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models


def get_sentinel_user():
    return get_user_model().objects.get_or_create(username='deleted')[0]

# Create your models here.


class PastorPage(Page):

    template = 'ministros/pastor_page.html'

    #parent_page_types = ['home.IglesiasListingPage']

    #subpage_types = ['iglesias.IglesiaEventosPage']

    user = models.ForeignKey( 
        settings.AUTH_USER_MODEL,
        blank=False,
        null=False,
        related_name="+",
        on_delete=models.SET(get_sentinel_user),

    )

    iglesia  = models.ForeignKey( 
        "iglesias.IglesiaPage",
        blank=True,
        null=True,
        related_name="+",
        on_delete=models.SET_NULL,
    )

    #pastor_wife = models.ImageField(upload_to='marriage_pics', default='marriage_pics/default_pastor_with_white_pic.png')
    pastor_wife = models.CharField(
        max_length=250,
        blank=True,
        null=True,
        help_text='Nombre de la esposa del pastor'
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
        FieldPanel('content'),
        FieldPanel('user'),
        FieldPanel('iglesia'),
        FieldPanel('pastor_wife'),
        #ImageChooserPanel('pastor_with_wife'),
    ]

    def get_context(self, request, *args, **kwargs):

        context = super().get_context(request, *args, **kwargs)

        pastor = self.user

        context['pastor'] = pastor
        return context



    class Meta:
        verbose_name = 'Pastor'
        verbose_name_plural = 'Pastores'
