from django import forms
from .models import DoctrinaComment, DoctrinaEntryPage
from wagtail.images.models import Image


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class DoctrinaCommentForm(forms.ModelForm):
    class Meta:
        model = DoctrinaComment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Escribe tu comentario aquí...'
            }),
        }


class DoctrinaEntryForm(forms.Form):
    """
    Frontend-friendly form for creating and editing DoctrinaEntryPage.
    Avoids Wagtail admin entirely -- creates/updates a Wagtail Page via code.
    """

    title = forms.CharField(
        label="Título",
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Ej: La Justificación por la Fe',
            'autofocus': True,
        }),
    )

    subtitle = forms.CharField(
        label="Subtítulo",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Subtítulo opcional',
        }),
    )

    slug = forms.SlugField(
        label="URL amigable (Slug)",
        help_text="Se genera automáticamente. No usar tildes ni espacios.",
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'ej-titulo-de-lexion',
        }),
    )

    abstract = forms.CharField(
        label="Resumen introductorio",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Breve resumen que aparece al inicio del artículo...',
        }),
    )

    body = forms.CharField(
        label="Contenido principal",
        widget=forms.Textarea(attrs={
            'class': 'form-control richtext-editor',
            'rows': 15,
            'placeholder': 'Escribe el contenido de tu artículo aquí...',
        }),
    )

    image = forms.ImageField(
        label="Imagen principal",
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
        }),
    )

    image_display_style = forms.ChoiceField(
        label="Estilo de imagen",
        choices=DoctrinaEntryPage.IMAGE_DISPLAY_CHOICES,
        initial='hero',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        }),
    )

    references = forms.CharField(
        label="Fuentes y Referencias",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Citas bíblicas, libros, etc...',
        }),
    )

    study_materials = forms.FileField(
        label="Materiales de Estudio",
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'multiple': True,
            'accept': '.doc,.docx,.ppt,.pptx,.pdf',
        }),
        help_text="Formatos: Word, PowerPoint, PDF."
    )

    youtube_urls = forms.CharField(
        label="Videos de YouTube",
        required=False,
        widget=forms.HiddenInput(),
        help_text="URLs de YouTube separadas por comas",
    )

    def clean_youtube_urls(self):
        """Parse YouTube URLs from comma-separated string."""
        raw = self.cleaned_data.get('youtube_urls', '')
        if not raw.strip():
            return []
        urls = [u.strip() for u in raw.split(',') if u.strip()]
        return urls
