from django.db import models

from wagtail.models import Page, Orderable
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, PageChooserPanel,InlinePanel


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
        FieldPanel("carousel_image")
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
        use_json_field=True,

    )

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

    class Meta:
        verbose_name = "Home Page"
       
