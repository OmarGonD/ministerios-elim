from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import MemberProfileForm
from .models import MemberProfile
from django.utils import timezone


@login_required
def member_profile_view(request):
    """View and edit member profile."""
    profile, created = MemberProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = MemberProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('miembros:profile')
    else:
        form = MemberProfileForm(instance=profile)

    return render(request, 'miembros/profile.html', {'form': form, 'profile': profile})


@login_required
def create_profile(request):
    """Create a new member profile for users who don't have one."""
    # Check if user already has a profile
    if hasattr(request.user, 'member_profile'):
        messages.info(request, 'Ya tienes un perfil de miembro creado.')
        return redirect('miembros:profile')

    # Check if user has a pastor profile (shouldn't happen, but handle it)
    if hasattr(request.user, 'pastores_profile'):
        messages.warning(request, 'Ya tienes un perfil de pastor. Si deseas cambiar a perfil de miembro, contacta al administrador.')
        return redirect('miembros:profile')

    # Get role from session or use default
    user_role = request.session.get('user_role', 'miembro')

    if request.method == 'POST':
        form = MemberProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            # Clear the session role after profile creation
            if 'user_role' in request.session:
                del request.session['user_role']
            messages.success(request, 'Perfil de miembro creado exitosamente.')
            return redirect('miembros:profile')
    else:
        # Pre-populate form with role from session
        initial_data = {}
        if user_role in ['miembro', 'visitante']:
            initial_data['role'] = user_role
        form = MemberProfileForm(initial=initial_data)

    return render(request, 'miembros/create_profile.html', {'form': form})


@login_required
def member_dashboard(request):
    """Dashboard for members."""
    pastor_profile = getattr(request.user, 'pastores_profile', None)
    if pastor_profile:
        if pastor_profile.is_apostle or pastor_profile.is_superpastor:
            return redirect('iglesias:apostol_dashboard')
        return redirect('iglesias:pastor_dashboard')

    try:
        profile = request.user.member_profile
    except MemberProfile.DoesNotExist:
        profile = None

    from doctrina.models import DoctrinaEntryPage, DoctrinaProgress
    from iglesias.models import IglesiaEventPage, PreachMaterial

    doctrine_total = DoctrinaEntryPage.objects.live().count()
    completed = DoctrinaProgress.objects.filter(
        user=request.user, page__live=True
    ).count()
    events = IglesiaEventPage.objects.live().filter(date__gte=timezone.now()).order_by('date')
    if profile and profile.iglesia_id:
        events = events.descendant_of(profile.iglesia)

    context = {
        'profile': profile,
        'is_member': profile.is_member if profile else False,
        'is_visitor': profile.is_visitor if profile else False,
        'doctrine_total': doctrine_total,
        'doctrine_completed': completed,
        'doctrine_progress': round((completed / doctrine_total) * 100) if doctrine_total else 0,
        'upcoming_events': events[:3],
        'recent_materials': PreachMaterial.objects.select_related('iglesia').order_by('-uploaded_at')[:3],
    }

    return render(request, 'miembros/dashboard.html', context)
