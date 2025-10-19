from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.conf import settings
from django.http import HttpResponse
from social_django.utils import psa

# Google OAuth2 callback view
@psa('social:complete')
def register_by_access_token(request, backend):
    token = request.POST.get('access_token')
    user = request.backend.do_auth(token)
    if user:
        login(request, user)
        return redirect('/')
    else:
        return HttpResponse('Authentication failed', status=401)


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from pastores.forms import UserProfileForm
from pastores.models import UserProfile


@login_required
def profile_view(request):
    """Redirect to appropriate profile based on user type."""
    if hasattr(request.user, 'pastores_profile'):
        return redirect('pastores:profile')
    elif hasattr(request.user, 'member_profile'):
        return redirect('miembros:profile')
    else:
        # Fallback: redirect to pastor profile (will create if needed)
        return redirect('pastores:profile')
