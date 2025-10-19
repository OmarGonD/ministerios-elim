from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import Panel, FieldPanel, MultiFieldPanel, InlinePanel, TabbedInterface, ObjectList
from django.urls import reverse
from modelcluster.fields import ParentalKey
from wagtail.images.models import Image
from django.conf import settings
from django.db import models as dj_models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django_countries.fields import CountryField

class HomePageCarouselImages(models.Model):
    page = ParentalKey('home.HomePage', related_name='carousel_images', on_delete=models.CASCADE)
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    panels = [
        FieldPanel('image'),
    ]

    class Meta:
        verbose_name = "Home Page Carousel Image"

class HomePage(Page):
    banner_title = models.CharField(max_length=100, blank=True, null=True)
    banner_subtitle = RichTextField(features=['bold', 'italic'], blank=True, null=True)
    banner_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    banner_cta = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    content = StreamField(
        [],
        null=True,
        blank=True,
        use_json_field=True,
    )
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('banner_title'),
            FieldPanel('banner_subtitle'),
            FieldPanel('banner_image'),
            FieldPanel('banner_cta'),
        ], heading="Opciones de banners"),
        MultiFieldPanel([
            InlinePanel('carousel_images', max_num=5, min_num=1, label="Escoge una imagen"),
        ], heading='Carousel Images'),
        FieldPanel('content'),
    ]

    subpage_types = [
        'doctrina.DoctrinaBasicaPage',
        'doctrina.DoctrinaIntermediaPage',
        'doctrina.DoctrinaAvanzadaPage',
        'home.ChurchPage'
    ]

    edit_handler = TabbedInterface([
        ObjectList(content_panels, heading='Content'),
        ObjectList(Page.promote_panels, heading='Promote'),
        ObjectList(Page.settings_panels, heading='Settings'),
    ])




class ChurchPage(Page):
    pastor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='churches')
    church_name = models.CharField(max_length=200, help_text="Nombre de la iglesia")
    description = RichTextField(blank=True, help_text="Descripción de la iglesia")
    address = models.TextField(blank=True, help_text="Dirección completa")
    contact_phone = models.CharField(max_length=20, blank=True, help_text="Teléfono de contacto")
    church_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Foto de la iglesia"
    )
    facebook_url = models.URLField(blank=True, help_text="URL de Facebook")
    instagram_url = models.URLField(blank=True, help_text="URL de Instagram")
    tiktok_url = models.URLField(blank=True, help_text="URL de TikTok")
    twitter_url = models.URLField(blank=True, help_text="URL de X (Twitter)")

    content_panels = Page.content_panels + [
        FieldPanel('pastor'),
        FieldPanel('church_name'),
        FieldPanel('description'),
        FieldPanel('address'),
        FieldPanel('contact_phone'),
        FieldPanel('church_image'),
        MultiFieldPanel([
            FieldPanel('facebook_url'),
            FieldPanel('instagram_url'),
            FieldPanel('tiktok_url'),
            FieldPanel('twitter_url'),
        ], heading="Redes Sociales"),
    ]

    parent_page_types = ['home.HomePage']
    subpage_types = []

    def __str__(self):
        return self.church_name