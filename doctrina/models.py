from django.db import models
from wagtail.models import Page, Orderable
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from django.contrib.auth.models import User
from wagtail.search import index
from wagtail.images.models import Image
from taggit.models import TaggedItemBase
from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from django import forms
from django.utils.text import slugify

# Base class for shared fields and settings
import django.utils.timezone
class DoctrinaBasePage(Page):
    introduction = RichTextField(blank=True, help_text="Introduction text for the page")
    image = models.ForeignKey(
        Image,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Header image for the category"
    )
    
    # ¡CORREGIDO! Incluye 'title' y hereda bien
    content_panels = Page.content_panels + [
        FieldPanel('image'),
        FieldPanel('introduction'),
    ]
    
    search_fields = Page.search_fields + [
        index.SearchField('introduction'),
    ]
    
    class Meta:
        abstract = True


# Doctrina Index Page
class DoctrinaIndexPage(DoctrinaBasePage):
    template = 'doctrina/doctrina_index_page.html'
    parent_page_types = ['home.HomePage']
    subpage_types = ['doctrina.DoctrinaBasicaPage', 'doctrina.DoctrinaIntermediaPage', 'doctrina.DoctrinaAvanzadaPage']

    def get_context(self, request):
        context = super().get_context(request)
        context['levels'] = self.get_children().live()
        # Note: We'll need to handle DoctrinaEntryPage specifically if it's not imported yet, 
        # but it's defined later in the same file.
        context['recent_entries'] = DoctrinaEntryPage.objects.live().descendant_of(self).order_by('-first_published_at')[:6]
        return context

    class Meta:
        verbose_name = "Doctrina Index"




# Doctrina Basica Page
class DoctrinaBasicaPage(DoctrinaBasePage):
    template = 'doctrina/doctrina_basica_page.html'
    parent_page_types = ['home.HomePage', 'doctrina.DoctrinaIndexPage']  # Allow migration/nested structure
    subpage_types = ['doctrina.DoctrinaEntryPage']

    class Meta:
        verbose_name = "Doctrina Basica"

# Doctrina Intermedia Page
class DoctrinaIntermediaPage(DoctrinaBasePage):
    template = 'doctrina/doctrina_intermedia_page.html'
    parent_page_types = ['home.HomePage', 'doctrina.DoctrinaIndexPage']
    subpage_types = ['doctrina.DoctrinaEntryPage']

    class Meta:
        verbose_name = "Doctrina Intermedia"

# Doctrina Avanzada Page
class DoctrinaAvanzadaPage(DoctrinaBasePage):
    template = 'doctrina/doctrina_avanzada_page.html'
    parent_page_types = ['home.HomePage', 'doctrina.DoctrinaIndexPage']
    subpage_types = ['doctrina.DoctrinaEntryPage']

    class Meta:
        verbose_name = "Doctrina Avanzada"
    
    def clean(self):
        super().clean()
        # Add any custom validation here if needed

# Entry Page for blog-like subpages


# ... (keep DoctrinaBasePage, DoctrinaBasicaPage, DoctrinaIntermediaPage, DoctrinaAvanzadaPage unchanged)

class DoctrinaEntryPageTag(TaggedItemBase):
    content_object = ParentalKey(
        'DoctrinaEntryPage',
        related_name='tagged_items',
        on_delete=models.CASCADE
    )


class DoctrinaYouTubeVideo(Orderable):
    """Model for storing YouTube video URLs related to a DoctrinaEntryPage."""
    page = ParentalKey(
        'DoctrinaEntryPage',
        on_delete=models.CASCADE,
        related_name='youtube_videos'
    )
    url = models.URLField(
        "URL de YouTube",
        help_text="Enlace completo del video de YouTube (ej: https://www.youtube.com/watch?v=...)"
    )
    title = models.CharField(
        "Título del video",
        max_length=255,
        blank=True,
        null=True,
        help_text="Título descriptivo del video (se obtiene automáticamente si lo dejas vacío)"
    )

    panels = [
        FieldPanel('url'),
        FieldPanel('title'),
    ]

    def save(self, *args, **kwargs):
        """Auto-fetch YouTube title if not provided."""
        if self.url and not self.title:
            try:
                import urllib.request
                import urllib.parse
                import json
                
                # Use YouTube oEmbed API to get video info
                oembed_url = f"https://www.youtube.com/oembed?url={urllib.parse.quote(self.url, safe='')}&format=json"
                with urllib.request.urlopen(oembed_url, timeout=5) as response:
                    data = json.loads(response.read().decode())
                    self.title = data.get('title', '')[:255]  # Limit to field max_length
            except Exception:
                pass  # If fetching fails, just leave title empty
        super().save(*args, **kwargs)

    class Meta(Orderable.Meta):
        verbose_name = "Video de YouTube"
        verbose_name_plural = "Videos de YouTube"

class DoctrinaEntryPage(Page):
    date = models.DateField(
        "Fecha de Publicación",
        default=django.utils.timezone.now,
        blank=True,
        null=True,
        help_text="Fecha de creación de la entrada"
    )
    body = RichTextField(
        "Contenido",
        blank=True,
        help_text="Contenido principal de la lección"
    )
    subtitle = models.CharField(
        "Subtítulo",
        max_length=255,
        blank=True,
        null=True,
        help_text="Subtítulo opcional para la lección"
    )
    image = models.ForeignKey(
        Image,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Optional image to accompany the entry"
    )
    abstract = RichTextField(
        blank=True,
        help_text="A brief summary of the entry (optional)"
    )
    tags = ClusterTaggableManager(
        through=DoctrinaEntryPageTag,
        blank=True,
        help_text="Tags to categorize the entry (e.g., theology, doctrine)"
    )
    references = RichTextField(
        blank=True,
        help_text="Citations or references for the entry (optional)"
    )
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='doctrina_entries_created',
        help_text="User who created this entry"
    )
    last_modified_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='doctrina_entries_modified',
        help_text="User who last modified this entry"
    )
    last_modified_date = models.DateTimeField(
        auto_now=True,
        help_text="Date the entry was last modified"
    )
    apostle_last_edit_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date when the Apostle last edited this entry"
    )



    content_panels = Page.content_panels + [
        FieldPanel('subtitle'),
        FieldPanel('body'),
        InlinePanel('youtube_videos', label="Videos de YouTube", heading="Videos Relacionados"),
        # Slug is auto-generated from title, no need to show it
    ]
    # content_panels = Page.content_panels + [
    #     MultiFieldPanel(
    #         [
    #             FieldPanel('slug'), # Debugging: Expose slug to check for validation
    #             FieldPanel('image'),
    #             FieldPanel('abstract'),
    #             FieldPanel('tags'),
    #             FieldPanel('body'),
    #             FieldPanel('references'),
    #         ],
    #         heading="Contenido",
    #     ),
    #     MultiFieldPanel(
    #         [
    #             FieldPanel('date'),
    #             FieldPanel('created_by', read_only=True),
    #             FieldPanel('last_modified_by', read_only=True),
    #             # FieldPanel('last_modified_date', read_only=True),
    #             FieldPanel('apostle_last_edit_date', read_only=True),
    #         ],
    #         heading="Metadatos",
    #     ),
    # ]

    # Set default values for required fields
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.show_in_menus:
            self.show_in_menus = True  # Default to showing in menus

    def full_clean(self, *args, **kwargs):
        """
        Auto-generate slug from title if not set.
        Handle duplicates by appending incremental numbers.
        """
        # Auto-generate slug from title if empty or not set
        if self.title and (not self.slug or self.slug == ''):
            base_slug = slugify(self.title)
            if not base_slug:
                base_slug = 'entrada'
            
            # Check for existing slugs and make unique
            slug = base_slug
            counter = 1
            
            # Get sibling pages (same parent)
            siblings = Page.objects.filter(path__startswith=self.path[:len(self.path)-4] if self.path else '').exclude(pk=self.pk)
            existing_slugs = set(siblings.values_list('slug', flat=True))
            
            # Also check globally for safety
            all_slugs = set(Page.objects.exclude(pk=self.pk).values_list('slug', flat=True))
            existing_slugs = existing_slugs.union(all_slugs)
            
            while slug in existing_slugs:
                counter += 1
                slug = f"{base_slug}-{counter}"
            
            self.slug = slug
        
        super().full_clean(*args, **kwargs)

    search_fields = Page.search_fields + [
        index.SearchField('body'),
        index.SearchField('abstract'),
        index.SearchField('references'),
        index.FilterField('tags'),
    ]

    parent_page_types = [
        'doctrina.DoctrinaBasicaPage',
        'doctrina.DoctrinaIntermediaPage',
        'doctrina.DoctrinaAvanzadaPage',
    ]

    template = 'doctrina/doctrina_entry_page.html'

    class Meta:
        verbose_name = "Doctrina Entry"