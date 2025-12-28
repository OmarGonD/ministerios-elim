from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import IglesiaForm
from .models import Iglesia, IglesiaPage, CountryIndexPage, IglesiaEventPage, Sermon, PreachMaterial
from django.core.paginator import Paginator
from django.contrib import messages
from wagtail.models import Page


@login_required
def my_iglesias(request):
    items = IglesiaPage.objects.live().filter(owner=request.user)
    return render(request, 'iglesias/my_iglesias.html', {'iglesias': items})


def iglesias_index(request):
    """Public list of all iglesias with optional country filter."""
    qs = IglesiaPage.objects.live().order_by('-first_published_at')
    
    selected_country_code = request.GET.get('country')
    if selected_country_code:
        # Filter by finding the Country Page and getting its descendants
        # We need to find the CountryIndexPage with this country code
        try:
           # CountryField stores code like 'MX', 'PE'
           # The template sends the country code? 
           # Wait, previous view sent values_list('country', flat=True) which for CountryField might be the code.
           # Let's assume code.
           country_page = CountryIndexPage.objects.live().filter(country=selected_country_code).first()
           if country_page:
               qs = qs.descendant_of(country_page)
        except Exception:
            pass

    paginator = Paginator(qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get list of countries that have churches
    # We can get all live CountryIndexPages
    countries = CountryIndexPage.objects.live()
    
    return render(request, 'iglesias/list.html', {
        'page_obj': page_obj, 
        'countries': countries, 
        'selected_country': selected_country_code
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

    events = IglesiaEventPage.objects.child_of(iglesia).live().order_by('date')
    
    return render(request, 'iglesias/pastor_dashboard.html', {
        'iglesia': iglesia,
        'pending_members': pending_members,
        'active_members': active_members,
        'ayudas': ayudas,
        'events': events,
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
        is_live = request.POST.get('is_live') == 'on'
        Sermon.objects.create(
            iglesia=iglesia,
            title=title,
            youtube_url=youtube_url,
            is_live=is_live,
        )
        messages.success(request, "Predicación publicada exitosamente.")
        return redirect('iglesias:pastor_dashboard')
    return render(request, 'iglesias/sermon_form.html', {'iglesia': iglesia})

@login_required
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
        if request.FILES.get('ppt_file'):
            material.ppt_file = request.FILES.get('ppt_file')
        if request.FILES.get('extra_file'):
            material.extra_file = request.FILES.get('extra_file')
        material.youtube_links = request.POST.get('youtube_links')
        material.save()
        messages.success(request, "Material actualizado.")
        return redirect('iglesias:pastor_dashboard')
    return render(request, 'iglesias/preach_material_form.html', {'material': material, 'iglesia': iglesia})

@login_required
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
    if not profile or not profile.is_apostle:
        messages.error(request, "Acceso denegado. Solo los apóstoles pueden acceder a este panel.")
        return redirect('home')
    
    # Handle upgrade/demote actions
    if request.method == 'POST':
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
    pastores = UserProfile.objects.filter(role=UserProfile.ROLE_PASTOR).exclude(user=request.user).order_by('-is_superpastor', 'user__first_name')
    
    # Get counts
    total_pastores = pastores.count()
    superpastores_count = pastores.filter(is_superpastor=True).count()
    
    return render(request, 'iglesias/apostol_dashboard.html', {
        'pastores': pastores,
        'total_pastores': total_pastores,
        'superpastores_count': superpastores_count,
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

