from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserProfileForm
from .models import UserProfile


@login_required
def profile_view(request):
    """View and edit user profile."""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('pastores:profile')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'pastores/profile.html', {'form': form, 'profile': profile})


@login_required
def create_profile(request):
    """Create a new pastor profile for users who don't have one."""
    # Check if user already has a profile
    if hasattr(request.user, 'pastores_profile'):
        messages.info(request, 'Ya tienes un perfil de pastor creado.')
        return redirect('pastores:profile')

    # Check if user has a member profile (shouldn't happen, but handle it)
    if hasattr(request.user, 'member_profile'):
        messages.warning(request, 'Ya tienes un perfil de miembro. Si deseas cambiar a perfil de pastor, contacta al administrador.')
        return redirect('miembros:profile')

    # Get role from session or use default
    user_role = request.session.get('user_role', 'pastor_elim')

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            # Clear the session role after profile creation
            if 'user_role' in request.session:
                del request.session['user_role']
            messages.success(request, 'Perfil de pastor creado exitosamente.')
            return redirect('pastores:profile')
    else:
        # Pre-populate form with role from session
        initial_data = {}
        if user_role in ['pastor_elim', 'pastor_otro']:
            initial_data['role'] = user_role
        form = UserProfileForm(initial=initial_data)

    return render(request, 'pastores/create_profile.html', {'form': form})


def biography_detail(request, pk):
    """Public view for pastor biography."""
    profile = get_object_or_404(UserProfile, pk=pk)
    return render(request, 'pastores/biography_detail.html', {'profile': profile})
