from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from django.contrib.auth.models import User
from wagtail.search import index
from wagtail.images.models import Image
from taggit.models import TaggedItemBase
from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from django import forms

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

class DoctrinaEntryPage(Page):
    date = models.DateField(
        "Fecha de Publicación",
        default=django.utils.timezone.now,
        blank=True,
        null=True,
        help_text="Fecha de creación de la entrada"
    )
    body = RichTextField(
        blank=True,
        help_text="Main content of the entry"
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



    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('slug'),
        FieldPanel('body'),
        # Page.content_panels is usually just title? simpler to be explicit.
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