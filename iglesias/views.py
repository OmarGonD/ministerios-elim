from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import IglesiaForm
from .models import (
    CityIndexPage, Iglesia, IglesiaPage, CountryIndexPage, IglesiaEventPage,
    Sermon, PreachMaterial,
)
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from wagtail.models import Page


def _upload_is_valid(upload, extensions, max_mb):
    if not upload:
        return True
    extension = upload.name.rsplit('.', 1)[-1].lower() if '.' in upload.name else ''
    return extension in extensions and upload.size <= max_mb * 1024 * 1024


@login_required
def my_iglesias(request):
    items = IglesiaPage.objects.live().filter(owner=request.user)
    return render(request, 'iglesias/my_iglesias.html', {'iglesias': items})


def iglesias_index(request):
    """Public church finder with search, location and language filters."""
    qs = IglesiaPage.objects.live().select_related('owner').order_by('title')
    search_query = request.GET.get('q', '').strip()
    selected_country_code = request.GET.get('country', '').strip().upper()
    selected_city_id = request.GET.get('city', '').strip()
    selected_language = request.GET.get('language', '').strip()

    if search_query:
        qs = qs.filter(Q(title__icontains=search_query) | Q(address__icontains=search_query))
    
    if selected_country_code:
        country_page = CountryIndexPage.objects.live().filter(country=selected_country_code).first()
        qs = qs.descendant_of(country_page) if country_page else qs.none()

    if selected_city_id.isdigit():
        city_page = CityIndexPage.objects.live().filter(pk=int(selected_city_id)).first()
        qs = qs.descendant_of(city_page) if city_page else qs.none()

    if selected_language:
        qs = qs.filter(primary_language=selected_language)

    paginator = Paginator(qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    countries = CountryIndexPage.objects.live().order_by('title')
    cities = CityIndexPage.objects.live().order_by('title')
    if selected_country_code:
        country_page = countries.filter(country=selected_country_code).first()
        cities = cities.descendant_of(country_page) if country_page else cities.none()

    map_churches = []
    for church in qs.filter(latitude__isnull=False, longitude__isnull=False):
        map_churches.append({
            'title': church.title,
            'address': church.address,
            'latitude': float(church.latitude),
            'longitude': float(church.longitude),
            'url': church.get_url(request=request),
            'city': church.city.title if church.city else '',
        })
    
    return render(request, 'iglesias/list.html', {
        'page_obj': page_obj,
        'countries': countries,
        'cities': cities,
        'map_churches': map_churches,
        'language_choices': IglesiaPage._meta.get_field('primary_language').choices,
        'search_query': search_query,
        'selected_country': selected_country_code,
        'selected_city': selected_city_id,
        'selected_language': selected_language,
        'result_count': paginator.count,
    })


def events_calendar(request):
    """Public calendar of upcoming events across all churches."""
    events = IglesiaEventPage.objects.live().filter(date__gte=timezone.now()).order_by('date')
    churches = IglesiaPage.objects.live().order_by('title')
    church_id = request.GET.get('church', '').strip()
    category = request.GET.get('category', '').strip()
    month = request.GET.get('month', '').strip()

    if church_id.isdigit():
        church = churches.filter(pk=int(church_id)).first()
        events = events.descendant_of(church) if church else events.none()
    if category:
        events = events.filter(category=category)
    if month:
        try:
            year, month_number = (int(part) for part in month.split('-', 1))
            events = events.filter(date__year=year, date__month=month_number)
        except (TypeError, ValueError):
            month = ''

    page_obj = Paginator(events, 12).get_page(request.GET.get('page'))
    return render(request, 'iglesias/events_calendar.html', {
        'page_obj': page_obj,
        'churches': churches,
        'categories': IglesiaEventPage.CATEGORY_CHOICES,
        'selected_church': church_id,
        'selected_category': category,
        'selected_month': month,
    })


def sermons_index(request):
    """Public, filterable catalogue of YouTube sermons."""
    sermons = Sermon.objects.select_related('iglesia', 'related_doctrine').order_by(
        '-is_live', '-preached_at', '-date_added'
    )
    query = request.GET.get('q', '').strip()
    speaker = request.GET.get('speaker', '').strip()
    church_id = request.GET.get('church', '').strip()
    topic = request.GET.get('topic', '').strip()
    series = request.GET.get('series', '').strip()

    if query:
        sermons = sermons.filter(
            Q(title__icontains=query) | Q(speaker__icontains=query) |
            Q(topic__icontains=query) | Q(series__icontains=query)
        )
    if speaker:
        sermons = sermons.filter(speaker=speaker)
    if church_id.isdigit():
        sermons = sermons.filter(iglesia_id=int(church_id))
    if topic:
        sermons = sermons.filter(topic=topic)
    if series:
        sermons = sermons.filter(series=series)

    page_obj = Paginator(sermons, 12).get_page(request.GET.get('page'))
    return render(request, 'iglesias/sermons_list.html', {
        'page_obj': page_obj,
        'churches': IglesiaPage.objects.live().order_by('title'),
        'topics': Sermon.objects.exclude(topic='').values_list('topic', flat=True).distinct().order_by('topic'),
        'speakers': Sermon.objects.exclude(speaker='').values_list('speaker', flat=True).distinct().order_by('speaker'),
        'series_options': Sermon.objects.exclude(series='').values_list('series', flat=True).distinct().order_by('series'),
        'search_query': query,
        'selected_speaker': speaker,
        'selected_church': church_id,
        'selected_topic': topic,
        'selected_series': series,
    })


@login_required
def create_iglesia(request):
    if request.method == 'POST':
        form = IglesiaForm(request.POST, request.FILES)
        if form.is_valid():
            iglesia = form.save(commit=False)
            iglesia.owner = request.user
            iglesia.save()
            return redirect('iglesias:iglesia_detail', pk=iglesia.pk)
    else:
        form = IglesiaForm()
    return render(request, 'iglesias/create_iglesia.html', {'form': form})


@login_required
def edit_iglesia(request, pk):
    iglesia = get_object_or_404(Iglesia, pk=pk)
    if iglesia.owner != request.user and not request.user.is_staff:
        return redirect('iglesias:my_iglesias')
    if request.method == 'POST':
        form = IglesiaForm(request.POST, request.FILES, instance=iglesia)
        if form.is_valid():
            form.save()
            return redirect('iglesias:iglesia_detail', pk=iglesia.pk)
    else:
        form = IglesiaForm(instance=iglesia)
    return render(request, 'iglesias/edit_iglesia.html', {'form': form, 'iglesia': iglesia})


def iglesia_detail(request, pk):
    """Public detail view of an iglesia."""
    iglesia = get_object_or_404(Iglesia, pk=pk)
    
    # Check if user can edit this iglesia
    can_edit = False
    if request.user.is_authenticated:
        can_edit = (iglesia.owner == request.user) or request.user.is_staff
    
    return render(request, 'iglesias/detail.html', {
        'iglesia': iglesia,
        'can_edit': can_edit
    })

from miembros.models import MemberProfile
from django.contrib import messages

@login_required
def pastor_dashboard(request):
    # Check if user has a pastor profile OR is a delegated editor (MemberProfile)
    # 1. Check Pastor Profile
    if hasattr(request.user, 'pastores_profile'):
        profile = request.user.pastores_profile
        iglesia = profile.iglesia
    # 2. Check Member Profile (Ayuda/Delegated)
    elif hasattr(request.user, 'member_profile'):
         # Check if this user is a delegated editor for ANY church
         # Wagtail Page ManyToMany related_name='editable_iglesias'
         iglesia = request.user.editable_iglesias.live().first()
         if not iglesia:
             messages.error(request, "No tienes permiso para acceder a este panel.")
             return redirect('home')
    else:
        messages.error(request, "No tienes permiso para acceder a este panel.")
        return redirect('home')

    if not iglesia:
        messages.warning(request, "No tienes una iglesia asignada para administrar.")
        return redirect('home')
    
    # Permission Check
    is_pastor = hasattr(request.user, 'pastores_profile')
    is_delegated = iglesia.delegated_editors.filter(id=request.user.id).exists()
    
    if iglesia.owner != request.user and not is_delegated and not request.user.is_superuser:
         messages.error(request, "No tienes permiso para administrar esta iglesia.")
         return redirect('home')

    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        action = request.POST.get('action')
        
        try:
            member = MemberProfile.objects.get(id=member_id, iglesia=iglesia)
            if action == 'approve':
                member.is_approved_member = True
                member.save()
                messages.success(request, f"Miembro {member.user.get_full_name() or member.user.username} aprobado.")
            elif action == 'reject':
                member.iglesia = None
                member.save()
                messages.info(request, "Solicitud rechazada.")
        except MemberProfile.DoesNotExist:
            messages.error(request, "Solicitud no encontrada.")
            
        return redirect('iglesias:pastor_dashboard')

    # Get lists
    pending_members = MemberProfile.objects.filter(iglesia=iglesia, is_approved_member=False)
    active_members = MemberProfile.objects.filter(iglesia=iglesia, is_approved_member=True).exclude(role=MemberProfile.ROLE_AYUDA)
    ayudas = MemberProfile.objects.filter(iglesia=iglesia, is_approved_member=True, role=MemberProfile.ROLE_AYUDA)
    
    # Sermons
    sermons = Sermon.objects.filter(iglesia=iglesia).order_by('-date_added')
    preach_materials = PreachMaterial.objects.filter(iglesia=iglesia).order_by('-uploaded_at')

    events = IglesiaEventPage.objects.child_of(iglesia).live().filter(
        date__gte=timezone.now()
    ).order_by('date')
    
    return render(request, 'iglesias/pastor_dashboard.html', {
        'iglesia': iglesia,
        'pending_members': pending_members,
        'active_members': active_members,
        'ayudas': ayudas,
        'events': events,
        'sermons': sermons,
        'preach_materials': preach_materials,
        'is_pastor': is_pastor,
        'is_delegated': is_delegated,
    })

@login_required
def create_event(request):
    # Logic similar to dashboard permission check
    iglesia = None
    if hasattr(request.user, 'pastores_profile'):
        iglesia = request.user.pastores_profile.iglesia
    elif hasattr(request.user, 'member_profile'):
         iglesia = request.user.editable_iglesias.live().first()

    if not iglesia:
         return redirect('home')
         
    # Check permission
    is_delegated = iglesia.delegated_editors.filter(id=request.user.id).exists()
    if iglesia.owner != request.user and not is_delegated and not request.user.is_superuser:
        return redirect('home')

    if request.method == 'POST':
        title = request.POST.get('title')
        date = request.POST.get('date')
        location = request.POST.get('location')
        description = request.POST.get('description')
        category = request.POST.get('category', 'general') # Default to general
        image_file = request.FILES.get('image')
        if not _upload_is_valid(image_file, {'jpg', 'jpeg', 'png', 'webp'}, 8):
            messages.error(request, 'La imagen debe ser JPG, PNG o WebP y pesar como máximo 8 MB.')
            return redirect('iglesias:create_event')
        
        # Create Page Programmatically
        new_event = IglesiaEventPage(
            title=title,
            date=date,
            location=location,
            description=description,
            category=category,
        )
        
        if image_file:
            from wagtail.images.models import Image
            from django.core.files.images import ImageFile
            img_obj = Image(title=title)
            img_obj.file.save(image_file.name, image_file, save=True)
            img_obj.save()
            new_event.image = img_obj

        # Add as child of Iglesia
        iglesia.add_child(instance=new_event)
        new_event.save_revision().publish()
        
        messages.success(request, "Evento publicado exitosamente.")
        return redirect('iglesias:pastor_dashboard')

    return render(request, 'iglesias/event_form.html', {'iglesia': iglesia})


@login_required
def create_sermon(request):
    # Permission check similar to create_event
    iglesia = None
    if hasattr(request.user, 'pastores_profile'):
        iglesia = request.user.pastores_profile.iglesia
    elif hasattr(request.user, 'member_profile'):
        iglesia = request.user.editable_iglesias.live().first()
    if not iglesia:
        return redirect('home')
    is_delegated = iglesia.delegated_editors.filter(id=request.user.id).exists()
    if iglesia.owner != request.user and not is_delegated and not request.user.is_superuser:
        return redirect('home')

    if request.method == 'POST':
        title = request.POST.get('title')
        youtube_url = request.POST.get('youtube_url')
        speaker = request.POST.get('speaker', '').strip()
        topic = request.POST.get('topic', '').strip()
        series = request.POST.get('series', '').strip()
        preached_at = request.POST.get('preached_at') or None
        doctrine_id = request.POST.get('related_doctrine')
        is_live = request.POST.get('is_live') == 'on'
        Sermon.objects.create(
            iglesia=iglesia,
            title=title,
            youtube_url=youtube_url,
            speaker=speaker,
            topic=topic,
            series=series,
            preached_at=preached_at,
            related_doctrine_id=doctrine_id or None,
            is_live=is_live,
        )
        messages.success(request, "Predicación publicada exitosamente.")
        return redirect('iglesias:pastor_dashboard')
    from doctrina.models import DoctrinaEntryPage
    return render(request, 'iglesias/sermon_form.html', {
        'iglesia': iglesia,
        'doctrine_entries': DoctrinaEntryPage.objects.live().order_by('title'),
    })

@login_required
@require_POST
def delete_sermon(request, pk):
    sermon = get_object_or_404(Sermon, pk=pk)
    iglesia = sermon.iglesia
    is_delegated = iglesia.delegated_editors.filter(id=request.user.id).exists()
    if iglesia.owner != request.user and not is_delegated and not request.user.is_superuser:
        return redirect('home')
    sermon.delete()
    messages.success(request, "Predicación eliminada.")
    return redirect('iglesias:pastor_dashboard')

@login_required
def create_preach_material(request):
    # Permission check similar to create_sermon
    iglesia = None
    if hasattr(request.user, 'pastores_profile'):
        iglesia = request.user.pastores_profile.iglesia
    elif hasattr(request.user, 'member_profile'):
        iglesia = request.user.editable_iglesias.live().first()
    if not iglesia:
        return redirect('home')
    is_delegated = iglesia.delegated_editors.filter(id=request.user.id).exists()
    if iglesia.owner != request.user and not is_delegated and not request.user.is_superuser:
        return redirect('home')

    if request.method == 'POST':
        title = request.POST.get('title')
        category = request.POST.get('category')
        description = request.POST.get('description')
        ppt_file = request.FILES.get('ppt_file')
        extra_file = request.FILES.get('extra_file')
        youtube_links = request.POST.get('youtube_links')
        if not ppt_file or not _upload_is_valid(ppt_file, {'ppt', 'pptx'}, 20):
            messages.error(request, 'La presentación debe ser PPT/PPTX y pesar como máximo 20 MB.')
            return redirect('iglesias:create_preach_material')
        if not _upload_is_valid(extra_file, {'pdf', 'doc', 'docx', 'txt', 'ppt', 'pptx', 'xls', 'xlsx'}, 20):
            messages.error(request, 'El archivo adicional tiene un formato no permitido o supera 20 MB.')
            return redirect('iglesias:create_preach_material')
        PreachMaterial.objects.create(
            iglesia=iglesia,
            title=title,
            category=category,
            description=description,
            ppt_file=ppt_file,
            extra_file=extra_file,
            youtube_links=youtube_links,
            created_by=request.user,
        )
        messages.success(request, "Material de predicación creado.")
        return redirect('iglesias:pastor_dashboard')
    return render(request, 'iglesias/preach_material_form.html', {'iglesia': iglesia})

@login_required
def edit_preach_material(request, pk):
    material = get_object_or_404(PreachMaterial, pk=pk)
    iglesia = material.iglesia
    is_delegated = iglesia.delegated_editors.filter(id=request.user.id).exists()
    if iglesia.owner != request.user and not is_delegated and not request.user.is_superuser:
        return redirect('home')
    if request.method == 'POST':
        material.title = request.POST.get('title')
        material.category = request.POST.get('category')
        material.description = request.POST.get('description')
        new_ppt = request.FILES.get('ppt_file')
        new_extra = request.FILES.get('extra_file')
        if not _upload_is_valid(new_ppt, {'ppt', 'pptx'}, 20) or not _upload_is_valid(
            new_extra, {'pdf', 'doc', 'docx', 'txt', 'ppt', 'pptx', 'xls', 'xlsx'}, 20
        ):
            messages.error(request, 'El archivo tiene un formato no permitido o supera 20 MB.')
            return redirect('iglesias:edit_preach_material', pk=material.pk)
        if new_ppt:
            material.ppt_file = new_ppt
        if new_extra:
            material.extra_file = new_extra
        material.youtube_links = request.POST.get('youtube_links')
        material.save()
        messages.success(request, "Material actualizado.")
        return redirect('iglesias:pastor_dashboard')
    return render(request, 'iglesias/preach_material_form.html', {'material': material, 'iglesia': iglesia})

@login_required
@require_POST
def delete_preach_material(request, pk):
    material = get_object_or_404(PreachMaterial, pk=pk)
    iglesia = material.iglesia
    is_delegated = iglesia.delegated_editors.filter(id=request.user.id).exists()
    if iglesia.owner != request.user and not is_delegated and not request.user.is_superuser:
        return redirect('home')
    material.delete()
    messages.success(request, "Material eliminado.")
    return redirect('iglesias:pastor_dashboard')

@login_required
def preach_material_detail(request, pk):
    material = get_object_or_404(PreachMaterial, pk=pk)
    # Related materials same category, from ANY church, excluding self
    related = PreachMaterial.objects.filter(category=material.category).exclude(pk=pk).order_by('?')[:5]
    # Process youtube links
    youtube_links_list = [link.strip() for link in material.youtube_links.splitlines() if link.strip()]
    return render(request, 'iglesias/preach_material_detail.html', {
        'material': material,
        'related': related,
        'youtube_links_list': youtube_links_list,
    })


# ============================================================================
# APOSTOL DASHBOARD
# ============================================================================

from pastores.models import UserProfile

@login_required
def apostol_dashboard(request):
    """
    Dashboard for Apostoles to manage pastors:
    - View all Pastores Elim
    - Upgrade a Pastor to "Pastor de Pastores" (Superpastor)
    - Demote a Superpastor back to regular Pastor
    """
    # Check if user is an Apostol
    profile = getattr(request.user, 'pastores_profile', None)
    if not profile or not (profile.is_apostle or profile.is_superpastor):
        messages.error(request, "Acceso denegado. Este panel es para supervisores y liderazgo general.")
        return redirect('home')
    
    # Handle upgrade/demote actions
    if request.method == 'POST' and profile.is_apostle:
        pastor_id = request.POST.get('pastor_id')
        action = request.POST.get('action')
        
        try:
            pastor = UserProfile.objects.get(id=pastor_id, role=UserProfile.ROLE_PASTOR)
            
            if action == 'upgrade':
                pastor.is_superpastor = True
                pastor.save()
                messages.success(request, f"¡{pastor.user.get_full_name() or pastor.user.username} ha sido promovido a Pastor de Pastores!")
            elif action == 'demote':
                pastor.is_superpastor = False
                pastor.save()
                messages.success(request, f"{pastor.user.get_full_name() or pastor.user.username} ya no es Pastor de Pastores.")
        except UserProfile.DoesNotExist:
            messages.error(request, "Pastor no encontrado.")
        
        return redirect('iglesias:apostol_dashboard')
    
    # Get all Pastores Elim (excluding self)
    pastores = UserProfile.objects.filter(role=UserProfile.ROLE_PASTOR).exclude(user=request.user)
    if profile.is_superpastor and not profile.is_apostle:
        pastores = pastores.filter(supervisor=profile)
    pastores = pastores.select_related('user', 'iglesia').order_by('-is_superpastor', 'user__first_name')
    
    # Get counts
    total_pastores = pastores.count()
    superpastores_count = pastores.filter(is_superpastor=True).count()
    church_ids = list(pastores.exclude(iglesia=None).values_list('iglesia_id', flat=True))
    if profile.iglesia_id:
        church_ids.append(profile.iglesia_id)
    churches = IglesiaPage.objects.live().filter(pk__in=church_ids)
    upcoming_events_count = sum(
        IglesiaEventPage.objects.live().descendant_of(church).filter(date__gte=timezone.now()).count()
        for church in churches
    )
    pending_members_count = MemberProfile.objects.filter(
        iglesia_id__in=church_ids, is_approved_member=False
    ).count()
    sermon_count = Sermon.objects.filter(iglesia_id__in=church_ids).count()
    from datetime import timedelta
    from home.models import EngagementMetric
    metric_totals = {
        row['event_type']: row['total']
        for row in EngagementMetric.objects.filter(
            date__gte=timezone.localdate() - timedelta(days=30)
        ).values('event_type').annotate(total=Sum('count'))
    }
    
    return render(request, 'iglesias/apostol_dashboard.html', {
        'pastores': pastores,
        'total_pastores': total_pastores,
        'superpastores_count': superpastores_count,
        'church_count': churches.count(),
        'upcoming_events_count': upcoming_events_count,
        'pending_members_count': pending_members_count,
        'sermon_count': sermon_count,
        'is_general_leadership': profile.is_apostle,
        'metric_totals': metric_totals,
    })


def materiales_index(request):
    """Public list of all preaching materials."""
    qs = PreachMaterial.objects.all().order_by('-uploaded_at')
    
    # Filter by Category
    category = request.GET.get('category')
    if category:
        qs = qs.filter(category=category)

    paginator = Paginator(qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'iglesias/materiales_list.html', {
        'page_obj': page_obj,
        'selected_category': category,
        'categories': PreachMaterial.CATEGORY_CHOICES,
    })

