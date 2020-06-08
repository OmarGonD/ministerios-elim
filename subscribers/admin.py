from django.contrib import admin

from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    modeladmin_register,
)

from .models import Subscriber

# Register your models here.

class SubscriberAdmin(ModelAdmin):

    model = Subscriber
    menu_label = "Suscritos"
    menu_icon = "placeholder"
    menu_order = 290
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ("email", "full_name",)
    search_field = ("email", "full_name",)


modeladmin_register(SubscriberAdmin)