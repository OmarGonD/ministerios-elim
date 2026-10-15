from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from urllib.parse import urlencode
from django.template.response import TemplateResponse
from django.utils.html import strip_tags
from wagtail.models import Page

from doctrina.models import DoctrinaEntryPage
from foros.models import Topic
from home.analytics import record_metric
from home.models import EngagementMetric
from iglesias.models import IglesiaEventPage, IglesiaPage, PreachMaterial, Sermon


TYPE_CHOICES = [
    ('', 'Todo'), ('iglesias', 'Iglesias'), ('doctrina', 'Doctrina'),
    ('eventos', 'Eventos'), ('predicaciones', 'Predicaciones'),
    ('materiales', 'Materiales'), ('foros', 'Foros'),
]


def _description(value, limit=180):
    return strip_tags(str(value or '')).strip()[:limit]


def _page_result(page, request):
    specific = page.specific
    if isinstance(specific, IglesiaPage):
        kind, label, icon = 'iglesias', 'Iglesia', 'fa-church'
        description, image = specific.address or specific.search_description, specific.hero_image
    elif isinstance(specific, IglesiaEventPage):
        kind, label, icon = 'eventos', 'Evento', 'fa-calendar-day'
        description, image = specific.description, specific.image
    elif isinstance(specific, DoctrinaEntryPage):
        kind, label, icon = 'doctrina', 'Doctrina', 'fa-book-bible'
        description, image = specific.abstract or specific.search_description, specific.image
    else:
        kind, label, icon = 'paginas', 'Página', 'fa-file-lines'
        description, image = specific.search_description, getattr(specific, 'image', None)
    image_url = image.get_rendition('fill-240x140|format-webp').url if image else ''
    return {
        'title': page.title, 'url': page.get_url(request=request), 'kind': kind,
        'type_label': label, 'icon': icon, 'description': _description(description),
        'image': image_url,
    }


def _collect_results(query, request):
    results = [_page_result(page, request) for page in Page.objects.live().search(query)[:100]]
    sermons = Sermon.objects.select_related('iglesia').filter(
        Q(title__icontains=query) | Q(speaker__icontains=query) |
        Q(topic__icontains=query) | Q(series__icontains=query)
    )[:50]
    results.extend({
        'title': item.title,
        'url': reverse('iglesias:sermons_index') + '?' + urlencode({'q': query}),
        'kind': 'predicaciones', 'type_label': 'Predicación',
        'icon': 'fa-microphone-lines',
        'description': _description(f'{item.speaker} · {item.topic} · {item.iglesia.title}'),
        'image': f'https://i.ytimg.com/vi/{item.youtube_id}/mqdefault.jpg' if item.youtube_id else '',
    } for item in sermons)
    materials = PreachMaterial.objects.select_related('iglesia').filter(
        Q(title__icontains=query) | Q(description__icontains=query) | Q(category__icontains=query)
    )[:50]
    results.extend({
        'title': item.title,
        'url': reverse('iglesias:preach_material_detail', args=[item.pk]),
        'kind': 'materiales', 'type_label': 'Material', 'icon': 'fa-file-arrow-down',
        'description': _description(item.description or item.get_category_display()), 'image': '',
    } for item in materials)
    topics = Topic.objects.filter(is_published=True).filter(
        Q(title__icontains=query) | Q(posts__body__icontains=query, posts__is_public=True)
    ).select_related('forum').distinct()[:50]
    results.extend({
        'title': item.title,
        'url': reverse('foros:topic_detail', args=[item.forum_id, item.pk]),
        'kind': 'foros', 'type_label': 'Foro', 'icon': 'fa-comments',
        'description': _description(item.forum.description), 'image': '',
    } for item in topics)
    normalized = query.casefold()
    return sorted(results, key=lambda item: (normalized not in item['title'].casefold(), item['title'].casefold()))


def search(request):
    query = request.GET.get('query', '').strip()
    selected_type = request.GET.get('type', '').strip()
    all_results = _collect_results(query, request) if query else []
    counts = {key: sum(item['kind'] == key for item in all_results) for key, _ in TYPE_CHOICES if key}
    results = [item for item in all_results if item['kind'] == selected_type] if selected_type else all_results
    if query and request.headers.get('x-requested-with') != 'XMLHttpRequest':
        record_metric(EngagementMetric.EVENT_SEARCH, selected_type or 'all')
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'results': results[:8]})
    return TemplateResponse(request, 'search/search.html', {
        'search_query': query,
        'search_results': Paginator(results, 12).get_page(request.GET.get('page')),
        'type_choices': TYPE_CHOICES,
        'selected_type': selected_type,
        'result_counts': counts,
    })
