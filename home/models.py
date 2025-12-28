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
    template = "home/home_page.html"
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
        default=[],  # Provide default empty list to avoid validation errors
    )
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('banner_title'),
            FieldPanel('banner_subtitle'),
            FieldPanel('banner_image'),
            FieldPanel('banner_cta'),
        ], heading="Banner Section"),
        #MultiFieldPanel([
        #    InlinePanel('carousel_images', max_num=5, min_num=1, label="Escoge una imagen"),
        #], heading='Carousel Images'),
        # FieldPanel('content'),  # Commented out - StreamField has no block types defined
        FieldPanel('body'),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        from iglesias.models import PreachMaterial, IglesiaPage, CountryIndexPage
        from pastores.models import UserProfile
        
        context['recent_materials'] = PreachMaterial.objects.all().order_by('-uploaded_at')[:6]
        context['church_count'] = IglesiaPage.objects.live().count()
        context['pastor_count'] = UserProfile.objects.filter(role='pastor_elim').count()
        context['country_count'] = CountryIndexPage.objects.live().count()
        
        return context
    parent_page_types = ['wagtailcore.Page']  # Allow HomePage to be created under Root
    
    subpage_types = [
        'doctrina.DoctrinaIndexPage',
        'doctrina.DoctrinaBasicaPage',
        'doctrina.DoctrinaIntermediaPage',
        'doctrina.DoctrinaAvanzadaPage',
        'home.ChurchPage',
        'home.WhoWeArePage'
    ]

    edit_handler = TabbedInterface([
        ObjectList(content_panels, heading='Content'),
        ObjectList(Page.promote_panels, heading='Promote'),
        ObjectList(Page.settings_panels, heading='Settings'),
    ])

    def get_template(self, request):
        return "home/home_page.html"




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


class WhoWeArePage(Page):
    template = "home/who_we_are_page.html"
    
    introduction_title = models.CharField(max_length=255, default="Quiénes Somos")
    introduction_text = RichTextField(blank=True, verbose_name="Texto de Introducción")
    
    apostle_title = models.CharField(max_length=255, default="Apóstol Jorge Fuentes")
    apostle_subtitle = models.CharField(max_length=255, default="Fundador y Cobertura Espiritual")
    apostle_bio = RichTextField(blank=True, verbose_name="Biografía del Apóstol")
    apostle_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Imagen del Apóstol"
    )
    apostle_quote = models.TextField(blank=True, verbose_name="Cita / Pensamiento")
    
    hierarchy_title = models.CharField(max_length=255, default="Nuestra Estructura Ministerial")
    hierarchy_description = models.TextField(blank=True, verbose_name="Descripción de la Jerarquía")

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('introduction_title'),
            FieldPanel('introduction_text'),
        ], heading="Introducción"),
        
        MultiFieldPanel([
            FieldPanel('apostle_title'),
            FieldPanel('apostle_subtitle'),
            FieldPanel('apostle_bio'),
            FieldPanel('apostle_image'),
            FieldPanel('apostle_quote'),
        ], heading="Perfil del Apóstol"),
        
        MultiFieldPanel([
            FieldPanel('hierarchy_title'),
            FieldPanel('hierarchy_description'),
        ], heading="Estructura Jerárquica"),
    ]

    max_count = 1
    parent_page_types = ['home.HomePage']
    subpage_types = []

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        from pastores.models import UserProfile
        
        # Apostle
        apostle = UserProfile.objects.filter(is_apostle=True).first()
        context['apostle_profile'] = apostle
        
        # Superpastors (Supervisors)
        superpastors = UserProfile.objects.filter(is_superpastor=True).order_by('user__first_name')
        context['superpastors'] = superpastors
        
        return context