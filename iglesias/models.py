from django.db import models
import re
from django.conf import settings
from django import forms

from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.search import index

from django_countries.fields import CountryField

# ==============================================================================
# Hierarchy Pages
# ==============================================================================

class CountryIndexPage(Page):
    """
    Root page for a Country (e.g., /peru/, /espana/).
    """
    country = CountryField(verbose_name="País")
    
    content_panels = Page.content_panels + [
        FieldPanel('country'),
    ]
    
    parent_page_types = ['home.HomePage']
    subpage_types = ['iglesias.CityIndexPage']

    class Meta:
        verbose_name = "País"
        verbose_name_plural = "Países"


class CityIndexPage(Page):
    """
    Page for a City (e.g., /peru/lima/).
    """
    # Simple description or intro for the city
    introduction = models.TextField(blank=True)
    
    content_panels = Page.content_panels + [
        FieldPanel('introduction'),
    ]
    
    parent_page_types = ['iglesias.CountryIndexPage']
    subpage_types = ['iglesias.IglesiaPage']

    class Meta:
        verbose_name = "Ciudad"
        verbose_name_plural = "Ciudades"


# ==============================================================================
# Iglesia Page (The main church site)
# ==============================================================================

class IglesiaPage(Page):
    """
    The main page for a specific church (e.g., /peru/lima/elim-central/).
    Managed by the Pastor (Owner) or delegated members.
    """
    # General Info
    address = models.CharField("Dirección", max_length=255)
    phone = models.CharField("Teléfono", max_length=50, blank=True)
    email = models.EmailField("Correo electrónico", blank=True)
    primary_language = models.CharField(
        "Idioma principal",
        max_length=10,
        choices=[
            ('es', 'Español'), ('en', 'English'), ('pt', 'Português'),
            ('fr', 'Français'), ('other', 'Otro'),
        ],
        default='es',
    )
    latitude = models.DecimalField(
        "Latitud", max_digits=9, decimal_places=6, null=True, blank=True,
        help_text="Coordenada para mostrar la iglesia en el mapa público.",
    )
    longitude = models.DecimalField(
        "Longitud", max_digits=9, decimal_places=6, null=True, blank=True,
        help_text="Coordenada para mostrar la iglesia en el mapa público.",
    )
    is_verified = models.BooleanField(
        "Información verificada", default=False,
        help_text="Indica que horarios, dirección y datos de contacto fueron revisados.",
    )
    
    # Hero/Branding
    # Uses the Page's built-in 'title' as the church name.
    # Uses the inherited 'owner' field as the Pastor in charge.
    
    hero_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Imagen Principal (Hero)"
    )
    
    logo = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Logo de la Iglesia"
    )

    # Content
    description = RichTextField("Sobre nosotros", blank=True)
    worship_schedule = RichTextField("Horarios de Culto", blank=True, help_text="Ej: Domingos 10am, Miércoles 7pm")
    
    # Location
    map_embed_code = models.TextField("Código de Mapa (Embed)", blank=True, help_text="Pegar el código <iframe> de Google Maps aquí")
    
    # Social Media
    facebook_url = models.URLField("Facebook", blank=True)
    instagram_url = models.URLField("Instagram", blank=True)
    youtube_url = models.URLField("YouTube", blank=True)
    tiktok_url = models.URLField("TikTok", blank=True)

    # Delegation (Permissions)
    # We can use a ManyToMany to User to allow specific members to edit this page
    # Note: Real permission handling requires custom logic in get_context or hooks, 
    # but storing the relationship here is the first step.
    delegated_editors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='editable_iglesias',
        verbose_name="Editores Delegados",
        help_text="Miembros a los que el Pastor ha dado permiso para editar esta página."
    )

    # Donation Info
    donation_qr_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Código QR para Donaciones"
    )
    bank_information = RichTextField("Información Bancaria", blank=True, help_text="Cuentas bancarias e instrucciones para ofrendar.")

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('hero_image'),
            FieldPanel('logo'),
            FieldPanel('address'),
            FieldPanel('phone'),
            FieldPanel('email'),
            FieldPanel('primary_language'),
            FieldPanel('latitude'),
            FieldPanel('longitude'),
            FieldPanel('is_verified'),
        ], heading="Información General"),
        
        FieldPanel('description'),
        FieldPanel('worship_schedule'),
        
        MultiFieldPanel([
            FieldPanel('map_embed_code'),
        ], heading="Ubicación"),
        
        MultiFieldPanel([
            FieldPanel('facebook_url'),
            FieldPanel('instagram_url'),
            FieldPanel('youtube_url'),
            FieldPanel('tiktok_url'),
        ], heading="Redes Sociales"),
        
        MultiFieldPanel([
            FieldPanel('donation_qr_image'),
            FieldPanel('bank_information'),
        ], heading="Diezmos y Ofrendas"),

        MultiFieldPanel([
            FieldPanel('delegated_editors', widget=forms.CheckboxSelectMultiple),
        ], heading="Delegación de Permisos"),
    ]

    parent_page_types = ['iglesias.CityIndexPage']
    subpage_types = ['iglesias.IglesiaEventPage']

    class Meta:
        verbose_name = "Iglesia"
        verbose_name_plural = "Iglesias"

    @property
    def country(self):
        # Find the CountryIndexPage ancestor
        country_page = self.get_ancestors().type(CountryIndexPage).specific().first()
        return country_page.country if country_page else None

    @property
    def city(self):
        return self.get_ancestors().type(CityIndexPage).specific().first()

    @property
    def whatsapp_url(self):
        number = re.sub(r'\D', '', self.phone or '')
        return f'https://wa.me/{number}' if number else ''

    @property
    def directions_url(self):
        from urllib.parse import quote_plus
        return f'https://www.google.com/maps/search/?api=1&query={quote_plus(self.address)}'

    @property
    def live_sermon(self):
        """Returns the first live sermon if exists."""
        return self.sermons.filter(is_live=True).first()

    @property
    def recent_sermons(self):
        """Returns the last 5 sermons."""
        return self.sermons.all()[:5]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        metric_key = f'metric_church_view_{self.pk}'
        if not getattr(request, 'in_preview_panel', False) and not request.session.get(metric_key):
            from home.analytics import record_metric
            from home.models import EngagementMetric
            record_metric(EngagementMetric.EVENT_CHURCH_VIEW, self.title)
            request.session[metric_key] = True
        # Check permissions for edit button visibility in template
        if request.user.is_authenticated:
            context['can_edit'] = (
                request.user == self.owner or 
                request.user.is_superuser or 
                self.delegated_editors.filter(id=request.user.id).exists()
            )
        # Add preach materials
        context['preach_materials'] = self.preach_materials.all().order_by('category', '-uploaded_at')
        return context

# ==============================================================================
# Events
# ==============================================================================

class IglesiaEventPage(Page):
    """
    Event page for a specific church (e.g., Retreats, Baptisms).
    """
    date = models.DateTimeField("Fecha y Hora")
    location = models.CharField("Lugar", max_length=255, default="Auditorio Principal")
    description = RichTextField("Descripción")
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name="Imagen del Evento"
    )

    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('jovenes', 'Jóvenes'),
    ]
    category = models.CharField(
        "Categoría", 
        max_length=20, 
        choices=CATEGORY_CHOICES, 
        default='general'
    )

    content_panels = Page.content_panels + [
        FieldPanel('title'),
        FieldPanel('category'),
        FieldPanel('date'),
        FieldPanel('location'),
        FieldPanel('description'),
        FieldPanel('image'),
    ]

    parent_page_types = ['iglesias.IglesiaPage']
    subpage_types = []

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"

# Sermon model for YouTube sermons
class Sermon(models.Model):
    """Model for storing YouTube sermon links for a church."""
    iglesia = models.ForeignKey('IglesiaPage', on_delete=models.CASCADE, related_name='sermons')
    title = models.CharField('Título', max_length=255)
    youtube_url = models.URLField('URL de YouTube')
    speaker = models.CharField('Predicador', max_length=150, blank=True)
    topic = models.CharField('Tema', max_length=120, blank=True, db_index=True)
    series = models.CharField('Serie', max_length=120, blank=True, db_index=True)
    related_doctrine = models.ForeignKey(
        'doctrina.DoctrinaEntryPage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_sermons',
        verbose_name='Doctrina relacionada',
    )
    preached_at = models.DateField('Fecha de predicación', null=True, blank=True)
    is_live = models.BooleanField('En Vivo', default=False)
    date_added = models.DateTimeField('Fecha de publicación', auto_now_add=True)

    class Meta:
        verbose_name = "Predicación"
        verbose_name_plural = "Predicaciones"
        ordering = ['-date_added']

    def __str__(self):
        return f"{self.title} ({'Live' if self.is_live else 'Recorded'})"

    @property
    def youtube_id(self):
        """Extract a YouTube video id without making a network request."""
        if not self.youtube_url:
            return ''
        match = re.search(
            r'(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})',
            self.youtube_url,
        )
        return match.group(1) if match else ''

# PreachMaterial model for PPTs and related documents
class PreachMaterial(models.Model):
    """Model for pastors to upload preaching materials (PPTs, docs)"""
    iglesia = models.ForeignKey('IglesiaPage', on_delete=models.CASCADE, related_name='preach_materials')
    title = models.CharField('Título', max_length=255)
    CATEGORY_CHOICES = [
        ('amor_de_dios', 'El Amor de Dios'),
        ('salvacion', 'La Salvación'),
        ('bautismo', 'El Bautismo'),
        ('espiritu_santo', 'El Espíritu Santo y sus dones'),
        ('otros', 'Otros'),
    ]
    category = models.CharField('Categoría', max_length=30, choices=CATEGORY_CHOICES, default='otros')
    ppt_file = models.FileField('PPT', upload_to='preach_materials/ppts/')
    extra_file = models.FileField('Archivo extra', upload_to='preach_materials/extra/', blank=True, null=True)
    youtube_links = models.TextField('Enlaces de YouTube', blank=True, help_text='One URL per line')
    description = models.TextField('Descripción', blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='materials_created',
        verbose_name='Creado por'
    )
    uploaded_at = models.DateTimeField('Fecha de subida', auto_now_add=True)
    updated_at = models.DateTimeField('Última modificación', auto_now=True)

    class Meta:
        verbose_name = "Material de Predicación"
        verbose_name_plural = "Materiales de Predicación"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"

# Legacy Iglesia model (Django-only) - retained for existing data/compatibility
class Iglesia(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='iglesias')
    nombre = models.CharField(max_length=255)
    
    # Redefine fields from original model to match exact schema if possible,
    # or finding the file content from previous step to restore exact fields is better.
    # Since I don't have the original file content in memory perfectly (it was shown in view_file),
    # I should try to preserve the fields as I saw them or just use the original file content?
    # I replaced the file entirely. I need to redefine the fields exactly as they were to avoiding schema changes on the old model if possible,
    # OR since I am in dev, I can just let it be a new model definition if I am careful.
    # BUT wait, if I define it here, Django will try to generate migrations.
    # If the fields differ, it will make a schema migration.
    # To avoid breakage, I should probably copy the definition from my `view_file` output in Step 640.

    address = models.CharField(max_length=255, blank=True)
    
    # Nuevos campos de horarios con más detalle
    culto_oracion_dia = models.CharField(max_length=20, choices=[
        ('lunes', 'Lunes'), ('martes', 'Martes'), ('miercoles', 'Miércoles'),
        ('jueves', 'Jueves'), ('viernes', 'Viernes'), ('sabado', 'Sábado'), ('domingo', 'Domingo')
    ], blank=True, null=True, verbose_name='Día - Culto de Oración')
    culto_oracion_hora = models.TimeField(blank=True, null=True, verbose_name='Hora - Culto de Oración')
    
    estudio_biblico_dia = models.CharField(max_length=20, choices=[
        ('lunes', 'Lunes'), ('martes', 'Martes'), ('miercoles', 'Miércoles'),
        ('jueves', 'Jueves'), ('viernes', 'Viernes'), ('sabado', 'Sábado'), ('domingo', 'Domingo')
    ], blank=True, null=True, verbose_name='Día - Estudio Bíblico')
    estudio_biblico_hora = models.TimeField(blank=True, null=True, verbose_name='Hora - Estudio Bíblico')
    
    culto_general_dia = models.CharField(max_length=20, choices=[
        ('lunes', 'Lunes'), ('martes', 'Martes'), ('miercoles', 'Miércoles'),
        ('jueves', 'Jueves'), ('viernes', 'Viernes'), ('sabado', 'Sábado'), ('domingo', 'Domingo')
    ], blank=True, null=True, verbose_name='Día - Culto General')
    culto_general_hora = models.TimeField(blank=True, null=True, verbose_name='Hora - Culto General')
    
    # Campos antiguos (mantener por compatibilidad)
    culto_oracion = models.CharField(max_length=10, choices=[('a. m.', 'a. m.'), ('p. m.', 'p. m.')], blank=True, null=True)
    estudio_biblico = models.CharField(max_length=10, choices=[('a. m.', 'a. m.'), ('p. m.', 'p. m.')], blank=True, null=True)
    culto_general = models.CharField(max_length=10, choices=[('a. m.', 'a. m.'), ('p. m.', 'p. m.')], blank=True, null=True)
    
    telefono = models.CharField(max_length=50, blank=True)
    country = CountryField(blank=True, null=True, help_text='País donde está ubicada la iglesia')
    foto = models.ForeignKey('wagtailimages.Image', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Iglesia'
        verbose_name_plural = 'Iglesias'

    def __str__(self):
        return f"{self.nombre} ({self.owner})"
