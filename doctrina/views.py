from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from wagtail.models import Page
from .models import DoctrinaBasicaPage, DoctrinaIntermediaPage, DoctrinaAvanzadaPage, DoctrinaEntryPage

@login_required
def create_doctrina_entry(request, section):
    """
    Redirect pastors to Wagtail admin to create a new doctrina entry.
    Section can be: 'basica', 'intermedia', 'avanzada'
    """
    # Check if user is a pastor or superuser
    if not (hasattr(request.user, 'pastores_profile') or request.user.is_superuser):
        messages.error(request, 'Solo los pastores o administradores pueden crear entradas de doctrina.')
        return redirect('/')

    # Map section names to page models and Wagtail model names
    section_mapping = {
        'basica': {
            'model': DoctrinaBasicaPage,
            'wagtail_name': 'doctrinabasicapage'
        },
        'intermedia': {
            'model': DoctrinaIntermediaPage,
            'wagtail_name': 'doctrinaintermediapage'
        },
        'avanzada': {
            'model': DoctrinaAvanzadaPage,
            'wagtail_name': 'doctrinaavanzadapage'
        }
    }

    if section not in section_mapping:
        messages.error(request, 'Sección de doctrina no válida.')
        return redirect('/')

    try:
        # Get the doctrina page for this section
        doctrina_page = section_mapping[section]['model'].objects.live().first()
        if not doctrina_page:
            messages.error(request, f'No se encontró la página de doctrina {section}.')
            return redirect('/')

        # Redirect to Wagtail admin to create a new DoctrinaEntryPage as child
        wagtail_add_url = reverse('wagtailadmin_pages:add', args=[
            'doctrina',  # app_label
            'doctrinaentrypage',  # model_name
            doctrina_page.id  # parent_page_id
        ])

        return redirect(wagtail_add_url)

    except Exception as e:
        messages.error(request, f'Error al crear entrada: {str(e)}')
        return redirect('/')
