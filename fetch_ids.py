import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ministerios_elim.settings.dev")
django.setup()

from wagtail.models import Page

pages = Page.objects.filter(title__icontains='Básica')
for p in pages:
    print(f'Title: {p.title}, Slug: {p.slug}, ID: {p.id}, Type: {p.specific_class.__name__}')
