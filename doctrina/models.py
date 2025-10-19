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
class DoctrinaBasePage(Page):
    introduction = RichTextField(blank=True, help_text="Introduction text for the page")
    
    content_panels = Page.content_panels + [
        FieldPanel('introduction'),
    ]
    
    search_fields = Page.search_fields + [
        index.SearchField('introduction'),
    ]
    
    class Meta:
        abstract = True


# Doctrina Basica Page
class DoctrinaBasicaPage(DoctrinaBasePage):
    template = 'doctrina/doctrina_basica_page.html'
    subpage_types = ['doctrina.DoctrinaEntryPage']

    class Meta:
        verbose_name = "Doctrina Basica"

# Doctrina Intermedia Page
class DoctrinaIntermediaPage(DoctrinaBasePage):
    template = 'doctrina/doctrina_intermedia_page.html'
    subpage_types = ['doctrina.DoctrinaEntryPage']

    class Meta:
        verbose_name = "Doctrina Intermedia"

# Doctrina Avanzada Page
class DoctrinaAvanzadaPage(DoctrinaBasePage):
    template = 'doctrina/doctrina_avanzada_page.html'
    subpage_types = ['doctrina.DoctrinaEntryPage']

    class Meta:
        verbose_name = "Doctrina Avanzada"

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
        "Post date",
        default=None,  # Will be set in clean() method
        blank=True,
        null=True,  # Allow NULL in database
        help_text="Date the entry was created"
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

    def get_parent(self, *args, **kwargs):
        # Only override if we have dummy path values during form validation
        if hasattr(self, '_skip_parent_validation') and self._skip_parent_validation:
            return None
        return super().get_parent(*args, **kwargs)

    def full_clean(self, *args, **kwargs):
        # Handle validation when path/depth are not set (during form validation)
        if not self.path or not self.depth or self.path.startswith('9999'):
            # Mark that we should skip parent validation
            self._skip_parent_validation = True

            try:
                # Call the parent validation without path validation
                super().full_clean(*args, **kwargs)
            finally:
                # Clean up the flag
                if hasattr(self, '_skip_parent_validation'):
                    delattr(self, '_skip_parent_validation')
        else:
            super().full_clean(*args, **kwargs)

    content_panels = Page.content_panels + [
        FieldPanel('title'),
        MultiFieldPanel(
            [
                FieldPanel('image'),
                FieldPanel('abstract'),
                FieldPanel('tags', widget=forms.CheckboxSelectMultiple),
                FieldPanel('body'),
                FieldPanel('references'),
            ],
            heading="Content",
        ),
        MultiFieldPanel(
            [
                FieldPanel('date'),
                FieldPanel('created_by', read_only=True),
                FieldPanel('last_modified_by', read_only=True),
                FieldPanel('last_modified_date', read_only=True),
            ],
            heading="Entry Details",
        ),
    ]

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