from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.models import Page
from wagtail.fields import StreamField
from streams import blocks


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
        use_json_field=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel('custom_title'),
        FieldPanel('post_image'),
        FieldPanel('content'),
    ]



