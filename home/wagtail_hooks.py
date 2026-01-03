from wagtail import hooks
from django.utils.text import slugify
from .models import ChurchPage

@hooks.register('register_page_model')
def register_church_page():
    return ChurchPage

@hooks.register('before_save_page')
def sanitize_all_slugs(request, page, **kwargs):
    """
    Ensure all pages have ASCII-only slugs (removes accents).
    Silent correction for better UX.
    """
    if page.slug:
        page.slug = slugify(page.slug)
    elif page.title:
        page.slug = slugify(page.title)
    return page
