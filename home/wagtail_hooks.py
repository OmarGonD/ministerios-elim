from wagtail import hooks
from .models import ChurchPage

@hooks.register('register_page_model')
def register_church_page():
    return ChurchPage
