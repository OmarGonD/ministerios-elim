from django.db import models
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.core.models import Page
from wagtail.core.fields import StreamField
from streams import blocks
from wagtail.images.edit_handlers import ImageChooserPanel

# Create your models here.



class BlogListingPage(Page):
    
    custom_title = models.CharField(
        max_length=250,
        blank=False,
        null=False,
        help_text='Sobreescribe el título de la entrada'
    )

    content_panels = Page.content_panels + [
        FieldPanel('custom_title'),
    ]

    subpage_types = ['blog.BlogDetailPage']


    def get_context(self, request, *args, **kwargs):

        context = super().get_context(request, *args, **kwargs)
        context['posts'] = BlogDetailPage.objects.live().public()
        return context


class BlogDetailPage(Page):

    subpage_types = []

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
    )

    content_panels = Page.content_panels + [
        FieldPanel('custom_title'),
        ImageChooserPanel('post_image'),
        StreamFieldPanel('content'),
    ]



