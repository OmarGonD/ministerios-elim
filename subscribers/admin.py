from django.contrib import admin

from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import Subscriber

# Register your models here.

class SubscriberViewSet(SnippetViewSet):

    model = Subscriber
    menu_label = "Suscritos"
    icon = "placeholder"
    menu_order = 290
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("email", "full_name",)
    search_field = ("email", "full_name",)

register_snippet(SubscriberViewSet)
