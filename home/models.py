from django.db import models

from wagtail.core.models import Page, Orderable
from wagtail.core.fields import RichTextField, StreamField
from wagtail.admin.edit_handlers import FieldPanel, MultiFieldPanel, PageChooserPanel, StreamFieldPanel,InlinePanel
from wagtail.images.edit_handlers import ImageChooserPanel

from modelcluster.fields import ParentalKey

from streams import blocks



class HomePageCarouseImages(Orderable):
    '''Entre 1 y 5 imágenes para un carousel'''
    page = ParentalKey("home.HomePage", related_name="carousel_images")
    carousel_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    panels = [
        ImageChooserPanel("carousel_image")
    ]




class HomePage(Page):
    templates = 'home/home_page.html'
    max_count = 1 #Solo puede haber una instancia de home en el sitio
    #Falta añadir una ContactPage
    subpage_types = ['doctrina.DoctrinaPage', 'flex.FlexPage', 'blog.BlogListingPage', 
    'iglesias.IglesiasListingPage', 'ministros.PastorPage']

    banner_title = models.CharField(max_length=100, blank=True, null=True)
    banner_subtitle = RichTextField(features=['bold', 'italic'], blank=True, null=True)
    banner_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    banner_cta = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'

    )

    content = StreamField(
        [
            ("cta", blocks.CTABlock()),
        ],
        null=True,
        blank=True,
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('banner_title'),
            FieldPanel('banner_subtitle'),
            ImageChooserPanel('banner_image'),
            FieldPanel('banner_cta'),
        ], heading="Opciones de banners"),
        
        MultiFieldPanel([
            InlinePanel('carousel_images', max_num=5, min_num=1, label="Escoge una imagen"),
        ], heading='Carousel Images'),
        StreamFieldPanel('content'),
        
    ]

    class Meta:
        verbose_name = "Home Page"
       
