from django import template

from ..models import Menu # 1 punto mismo directorio, 2 puntos sube un directorio

register = template.Library()

@register.simple_tag()
def get_menu(slug):
    return Menu.objects.get(slug=slug)
