from django.db import models

# Create your models here.
from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.models import Page
from wagtail.fields import StreamField
from streams import blocks


from wagtail.admin.panels import (
    MultiFieldPanel,
    InlinePanel,
    FieldPanel,
    PageChooserPanel
)

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

class DoctrinaPage(Page):

    '''Lista las categorías de doctrina: básica, intermedia y avanzada'''

    template = 'doctrina/doctrina_page.html'
    max_count = 1
    subpage_types = ['doctrina.DoctrinaLevelPage']
   
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
        use_json_field=True
    )

    link_page_doctrina_basica = models.ForeignKey(
        "doctrina.DoctrinaLevelPage", #app y modelo de tu proyecto
        blank=True, 
        null=True,
        related_name="+",
        on_delete=models.SET_NULL,
    )

    link_page_doctrina_intermedia = models.ForeignKey(
        "doctrina.DoctrinaLevelPage", #app y modelo de tu proyecto
        blank=True, 
        null=True,
        related_name="+",
        on_delete=models.SET_NULL,
    )

    link_page_doctrina_avanzada = models.ForeignKey(
        "doctrina.DoctrinaLevelPage", #app y modelo de tu proyecto
        blank=True, 
        null=True,
        related_name="+",
        on_delete=models.SET_NULL,
    )

    subtitle = models.CharField(max_length=100, null=True, blank=True)


    content_panels = Page.content_panels + [
        FieldPanel('subtitle'),
        FieldPanel('content'),
        PageChooserPanel("link_page_doctrina_basica"),
        PageChooserPanel("link_page_doctrina_intermedia"),
        PageChooserPanel("link_page_doctrina_avanzada"),
    ]




    class Meta:
        verbose_name = "Doctrina"
        verbose_name_plural = "Doctrinas"





class DoctrinaLevelPage(Page):

    template = 'doctrina/doctrina_listing_page.html'

    parent_page_types = ['doctrina.DoctrinaPage']
    
    custom_title = models.CharField(
        max_length=250,
        blank=False,
        null=False,
        help_text='Sobreescribe el título de la entrada'
    )

    level_image = models.ForeignKey( #imagen del nivel de doctrina: basico, int, avanzado
        "wagtailimages.Image",
        blank=False,
        null=True,
        related_name="+",
        on_delete=models.SET_NULL,

    )

    tema = models.ForeignKey(
        "wagtailcore.Page", #app y modelo de tu proyecto
        blank=True, 
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
        FieldPanel('level_image'),
        FieldPanel('content'),
    ]

    subpage_types = ['doctrina.DoctrinaDetailPage']
   
    
    def latest_published_date(self):
        latest_published_date = DoctrinaDetailPage.objects.child_of(self).live().public().latest('last_published_at').last_published_at
        return latest_published_date

    def get_context(self, request, *args, **kwargs):

        context = super().get_context(request, *args, **kwargs)

        all_doctrina_posts = DoctrinaDetailPage.objects.child_of(self).live().public()
    
        if request.GET.get('tag', None):
            tags = request.GET.get('tag')
            all_doctrina_posts = all_doctrina_posts.filter(tags__slug__in=[tags])

        context['doctrina_posts'] = all_doctrina_posts
        
        return context




class DoctrinaPageTag(TaggedItemBase):
    content_object = ParentalKey(
        'DoctrinaDetailPage',
        related_name='tagged_items',
        on_delete=models.CASCADE,
    )



class DoctrinaDetailPage(Page):

    subpage_types = []
    tags = ClusterTaggableManager(through=DoctrinaPageTag, blank=True)

    parent_page_types = ['doctrina.DoctrinaLevelPage']

    custom_title = models.CharField(
        max_length=250,
        blank=False,
        null=False,
        help_text='Sobreescribe el título de la entrada'
    )

    post_image = models.ForeignKey(
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
        FieldPanel('post_image'),
        FieldPanel('content'),
    ]



