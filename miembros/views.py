from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import MemberProfileForm
from .models import MemberProfile


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
    try:
        profile = request.user.member_profile
    except MemberProfile.DoesNotExist:
        profile = None

    context = {
        'profile': profile,
        'is_member': profile.is_member if profile else False,
        'is_visitor': profile.is_visitor if profile else False,
    }

    return render(request, 'miembros/dashboard.html', context)
