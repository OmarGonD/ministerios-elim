from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.views.decorators.http import require_POST
from wagtail.models import Page
from wagtail.images.models import Image
from wagtail.documents.models import Document

from .models import (
    DoctrinaBasicaPage, DoctrinaIntermediaPage, DoctrinaAvanzadaPage,
    DoctrinaEntryPage, DoctrinaProgress, DoctrinaYouTubeVideo, DoctrinaDocument
)
from .forms import DoctrinaEntryForm


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SECTION_MAP = {
    'basica': DoctrinaBasicaPage,
    'intermedia': DoctrinaIntermediaPage,
    'avanzada': DoctrinaAvanzadaPage,
}


def _get_parent_page(section):
    """Return the live parent page for a given section key."""
    model = SECTION_MAP.get(section)
    if model is None:
        return None
    return model.objects.live().first()


def _user_is_pastor_or_above(user):
    """True when the user has a pastores_profile OR is superuser."""
    return hasattr(user, 'pastores_profile') or user.is_superuser


def _user_can_edit_entry(user, entry):
    """Check if user can edit the given entry."""
    if user.is_superuser:
        return True
    if not hasattr(user, 'pastores_profile'):
        return False
    # Privileged roles can edit any entry
    privileged = {'Apostol', 'Pastor de Pastores'}
    if user.groups.filter(name__in=privileged).exists():
        return True
    # Regular pastors can only edit their own entries
    return entry.owner == user


@login_required
@require_POST
def toggle_progress(request, entry_id):
    """Mark a doctrine lesson complete, or make it pending again."""
    entry = get_object_or_404(DoctrinaEntryPage.objects.live(), pk=entry_id)
    progress = DoctrinaProgress.objects.filter(user=request.user, page=entry)
    if progress.exists():
        progress.delete()
        messages.info(request, 'La lección volvió a quedar pendiente.')
    else:
        DoctrinaProgress.objects.create(user=request.user, page=entry)
        from home.analytics import record_metric
        from home.models import EngagementMetric
        record_metric(EngagementMetric.EVENT_LESSON_COMPLETED, entry.title)
        messages.success(request, 'Lección marcada como completada.')
    return redirect(entry.url)


def _populate_entry_from_form(entry, form, user, image_file=None):
    """Apply cleaned form data onto a DoctrinaEntryPage instance."""
    entry.title = form.cleaned_data['title']
    entry.subtitle = form.cleaned_data.get('subtitle', '')
    entry.abstract = form.cleaned_data.get('abstract', '')
    entry.body = form.cleaned_data['body']
    entry.references = form.cleaned_data.get('references', '')
    entry.image_display_style = form.cleaned_data.get('image_display_style', 'hero')

    # Handle uploaded image
    if image_file:
        wagtail_image = Image(title=image_file.name, file=image_file)
        wagtail_image.save()
        entry.image = wagtail_image

    entry.last_modified_by = user


def _sync_youtube_videos(entry, urls):
    """Replace all YouTube videos with the provided URL list."""
    entry.youtube_videos.all().delete()
    for url in urls:
        if url:
            DoctrinaYouTubeVideo.objects.create(page=entry, url=url)


def _sync_documents(entry, files):
    """Save new files as Wagtail Documents and link them to the entry."""
    for f in files:
        if f:
            doc = Document(title=f.name, file=f)
            doc.save()
            DoctrinaDocument.objects.create(page=entry, document=doc)


# ---------------------------------------------------------------------------
# Legacy view (redirect to Wagtail admin) — kept for backward-compatibility
# ---------------------------------------------------------------------------

@login_required
def create_doctrina_entry(request, section):
    """
    Redirect pastors to Wagtail admin to create a new doctrina entry.
    Section can be: 'basica', 'intermedia', 'avanzada'
    """
    if not _user_is_pastor_or_above(request.user):
        messages.error(request, 'Solo los pastores o administradores pueden crear entradas de doctrina.')
        return redirect('/')

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
        doctrina_page = section_mapping[section]['model'].objects.live().first()
        if not doctrina_page:
            messages.error(request, f'No se encontró la página de doctrina {section}.')
            return redirect('/')

        wagtail_add_url = reverse('wagtailadmin_pages:add', args=[
            'doctrina',
            'doctrinaentrypage',
            doctrina_page.id
        ])
        return redirect(wagtail_add_url)

    except Exception as e:
        messages.error(request, f'Error al crear entrada: {str(e)}')
        return redirect('/')


# ---------------------------------------------------------------------------
# NEW  —  Frontend Create
# ---------------------------------------------------------------------------

@login_required
def frontend_create_entry(request, section):
    """
    Render a friendly frontend form to create a DoctrinaEntryPage.
    """
    if not _user_is_pastor_or_above(request.user):
        messages.error(request, 'Solo los pastores pueden crear entradas de doctrina.')
        return redirect('/')

    parent = _get_parent_page(section)
    if parent is None:
        messages.error(request, 'Sección de doctrina no válida.')
        return redirect('/')

    if request.method == 'POST':
        form = DoctrinaEntryForm(request.POST, request.FILES)
        if form.is_valid():
            entry = DoctrinaEntryPage()
            _populate_entry_from_form(
                entry, form, request.user,
                image_file=request.FILES.get('image'),
            )
            entry.owner = request.user
            entry.created_by = request.user

            action = request.POST.get('action', 'publish')

            # Add as child of the section page
            parent.add_child(instance=entry)

            # Sync YouTube videos
            yt_urls = form.cleaned_data.get('youtube_urls', [])
            _sync_youtube_videos(entry, yt_urls)

            # Sync Documents
            doc_files = request.FILES.getlist('study_materials')
            _sync_documents(entry, doc_files)

            if action == 'draft':
                # Unpublish (the page was auto-published by add_child on live parent)
                entry.unpublish()
                entry.save_revision(user=request.user)
                messages.success(request, f'✏️ Borrador guardado: "{entry.title}"')
            else:
                entry.save_revision(user=request.user).publish()
                messages.success(request, f'🚀 Artículo publicado: "{entry.title}"')

            return redirect('doctrina:mis_articulos')
    else:
        form = DoctrinaEntryForm()

    return render(request, 'doctrina/frontend_form.html', {
        'form': form,
        'section': section,
        'parent': parent,
        'is_edit': False,
    })


# ---------------------------------------------------------------------------
# NEW  —  Frontend Edit
# ---------------------------------------------------------------------------

@login_required
def frontend_edit_entry(request, entry_id):
    """
    Render a friendly frontend form to edit an existing DoctrinaEntryPage.
    """
    entry = get_object_or_404(DoctrinaEntryPage, pk=entry_id)

    if not _user_can_edit_entry(request.user, entry):
        raise PermissionDenied("No tienes permiso para editar esta entrada.")

    if request.method == 'POST':
        form = DoctrinaEntryForm(request.POST, request.FILES)
        if form.is_valid():
            _populate_entry_from_form(
                entry, form, request.user,
                image_file=request.FILES.get('image'),
            )

            action = request.POST.get('action', 'publish')
            yt_urls = form.cleaned_data.get('youtube_urls', [])
            _sync_youtube_videos(entry, yt_urls)

            # Sync Documents
            doc_files = request.FILES.getlist('study_materials')
            _sync_documents(entry, doc_files)

            if action == 'draft':
                if entry.live:
                    entry.unpublish()
                entry.save_revision(user=request.user)
                messages.success(request, f'✏️ Borrador guardado: "{entry.title}"')
            else:
                entry.save_revision(user=request.user).publish()
                messages.success(request, f'✅ Artículo actualizado: "{entry.title}"')

            return redirect('doctrina:mis_articulos')
    else:
        # Pre-populate form with existing data
        yt_urls = ','.join(v.url for v in entry.youtube_videos.all())
        form = DoctrinaEntryForm(initial={
            'title': entry.title,
            'subtitle': entry.subtitle or '',
            'abstract': entry.abstract or '',
            'body': entry.body or '',
            'references': entry.references or '',
            'image_display_style': entry.image_display_style or 'hero',
            'youtube_urls': yt_urls,
        })

    return render(request, 'doctrina/frontend_form.html', {
        'form': form,
        'section': None,
        'parent': entry.get_parent(),
        'is_edit': True,
        'entry': entry,
    })


# ---------------------------------------------------------------------------
# NEW  —  Dashboard "Mis Artículos"
# ---------------------------------------------------------------------------

@login_required
def mis_articulos(request):
    """
    Show a dashboard with the current user's doctrine articles.
    Apostol/Pastor de Pastores can see ALL articles.
    """
    user = request.user

    if not _user_is_pastor_or_above(user):
        messages.error(request, 'Solo los pastores pueden acceder a esta página.')
        return redirect('/')

    # Check if user is privileged (can see all)
    is_privileged = user.is_superuser or user.groups.filter(
        name__in={'Apostol', 'Pastor de Pastores'}
    ).exists()

    if is_privileged:
        entries = DoctrinaEntryPage.objects.all().order_by('-latest_revision_created_at')
    else:
        entries = DoctrinaEntryPage.objects.filter(owner=user).order_by('-latest_revision_created_at')

    # Separate live vs drafts
    live_entries = [e for e in entries if e.live]
    draft_entries = [e for e in entries if not e.live]

    return render(request, 'doctrina/mis_articulos.html', {
        'live_entries': live_entries,
        'draft_entries': draft_entries,
        'is_privileged': is_privileged,
        'total': entries.count(),
    })


# ---------------------------------------------------------------------------
# NEW  —  Delete entry
# ---------------------------------------------------------------------------

@login_required
def frontend_delete_entry(request, entry_id):
    """Delete a DoctrinaEntryPage from the frontend."""
    entry = get_object_or_404(DoctrinaEntryPage, pk=entry_id)

    if not _user_can_edit_entry(request.user, entry):
        raise PermissionDenied("No tienes permiso para eliminar esta entrada.")

    if request.method == 'POST':
        title = entry.title
        entry.delete()
        messages.success(request, f'🗑️ Entrada eliminada: "{title}"')
        return redirect('doctrina:mis_articulos')

    return render(request, 'doctrina/confirm_delete.html', {
        'entry': entry,
    })
