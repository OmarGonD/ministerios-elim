from django.db import models
from wagtail.snippets.models import register_snippet
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import RichTextField


@register_snippet
class GraficoInteractivo(models.Model):
    """
    Modelo para gráficos interactivos que se pueden embeber en entradas de doctrina.
    Los datos se almacenan en JSON para máxima flexibilidad.
    """
    TIPO_CHOICES = [
        ('genealogia', 'Árbol Genealógico'),
        ('timeline', 'Línea de Tiempo'),
        ('diagrama', 'Diagrama de Relaciones'),
        ('mapa', 'Mapa Bíblico'),
        ('chiastic', 'Estructura Quiástica'),
        ('tabernaculo', 'Explorador del Tabernáculo'),
        ('armonia', 'Armonía de los Evangelios'),
    ]
    
    nombre = models.CharField(
        "Nombre del Gráfico",
        max_length=200,
        help_text="Ej: Genealogía de Jesús según Mateo"
    )
    slug = models.SlugField(
        "Identificador URL",
        unique=True,
        help_text="Identificador único para referencias (ej: genealogia-jesus)"
    )
    tipo = models.CharField(
        "Tipo de Gráfico",
        max_length=50,
        choices=TIPO_CHOICES,
        default='diagrama'
    )
    descripcion = RichTextField(
        "Descripción",
        blank=True,
        help_text="Breve descripción que aparecerá sobre el gráfico"
    )
    datos_json = models.JSONField(
        "Datos del Gráfico",
        default=dict,
        help_text="Datos estructurados en formato JSON para renderizar el gráfico"
    )
    activo = models.BooleanField(
        "Activo",
        default=True,
        help_text="Desactiva para ocultar sin eliminar"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    panels = [
        MultiFieldPanel([
            FieldPanel('nombre'),
            FieldPanel('slug'),
            FieldPanel('tipo'),
            FieldPanel('activo'),
        ], heading="Información Básica"),
        FieldPanel('descripcion'),
        FieldPanel('datos_json'),
    ]
    
    class Meta:
        verbose_name = "Gráfico Interactivo"
        verbose_name_plural = "Gráficos Interactivos"
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"
    
    def get_template_name(self):
        """Retorna el template específico según el tipo de gráfico."""
        templates = {
            'genealogia': 'graficos_interactivos/tipos/genealogia.html',
            'timeline': 'graficos_interactivos/tipos/timeline.html',
            'diagrama': 'graficos_interactivos/tipos/diagrama.html',
            'mapa': 'graficos_interactivos/tipos/mapa.html',
            'chiastic': 'graficos_interactivos/tipos/chiastic.html',
            'tabernaculo': 'graficos_interactivos/tipos/tabernacle.html',
            'armonia': 'graficos_interactivos/tipos/harmony.html',
        }
        return templates.get(self.tipo, 'graficos_interactivos/tipos/diagrama.html')
