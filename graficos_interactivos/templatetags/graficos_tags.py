from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from graficos_interactivos.models import GraficoInteractivo
import json

register = template.Library()


@register.simple_tag
def grafico(slug, height='500px', width='100%'):
    """
    Renderiza un gráfico interactivo por su slug.
    
    Uso: {% grafico "genealogia-jesus" height="600px" %}
    """
    try:
        grafico_obj = GraficoInteractivo.objects.get(slug=slug, activo=True)
        template_name = grafico_obj.get_template_name()
        
        context = {
            'grafico': grafico_obj,
            'datos_json': json.dumps(grafico_obj.datos_json),
            'height': height,
            'width': width,
            'unique_id': f"grafico-{grafico_obj.slug.replace('-', '_')}",
        }
        
        html = render_to_string(template_name, context)
        return mark_safe(html)
    except GraficoInteractivo.DoesNotExist:
        return mark_safe(f'<div class="alert alert-warning">Gráfico "{slug}" no encontrado</div>')


@register.inclusion_tag('graficos_interactivos/embed_wrapper.html')
def grafico_con_descripcion(slug, height='500px'):
    """
    Renderiza un gráfico con su descripción.
    
    Uso: {% grafico_con_descripcion "genealogia-jesus" %}
    """
    try:
        grafico_obj = GraficoInteractivo.objects.get(slug=slug, activo=True)
        return {
            'grafico': grafico_obj,
            'datos_json': json.dumps(grafico_obj.datos_json),
            'height': height,
            'unique_id': f"grafico-{grafico_obj.slug.replace('-', '_')}",
        }
    except GraficoInteractivo.DoesNotExist:
        return {'grafico': None, 'slug': slug}
