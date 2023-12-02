from django.db import models

from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
# Create your models here.

@register_setting
class SocialMediaSettings(BaseSiteSetting):
    '''Social media settings for our custom website'''
    facebook = models.URLField(blank=True, null=True, help_text='Facebook URL')
    twitter = models.URLField(blank=True, null=True, help_text='Twitter handle')
    youtube = models.URLField(blank=True, null=True, help_text='Canal de Youtube')

    panels = [
        MultiFieldPanel([
            FieldPanel('facebook'),
            FieldPanel('twitter'),
            FieldPanel('youtube'),
        ], heading="Configuraciones Social Media")
    ]