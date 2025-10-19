from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ExtendedUserCreationForm, EmailAuthenticationForm
from django.http import JsonResponse

from django.db import transaction
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings

def register(request):
    if request.method == 'POST':
        form = ExtendedUserCreationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                # Users are active immediately - no email activation needed
                user.is_active = True
                user.save()
                role = form.cleaned_data.get('role')

                # Create appropriate profile based on role
                if role in ['pastor_elim', 'pastor_otro']:
                    # Create pastor profile
                    try:
                        profile = user.pastores_profile
                        profile.role = role
                        profile.country = form.cleaned_data.get('country') or None
                        profile.country_code = form.cleaned_data.get('country_code') or None
                        profile.phone_number = form.cleaned_data.get('phone_number') or None
                        profile.save()
                    except Exception as e:
                        from pastores.models import UserProfile
                        UserProfile.objects.update_or_create(
                            user=user,
                            defaults={
                                'role': role,
                                'country': form.cleaned_data.get('country') or None,
                                'country_code': form.cleaned_data.get('country_code') or None,
                                'phone_number': form.cleaned_data.get('phone_number') or None
                            }
                        )
                else:
                    # Create member profile for members and visitors
                    try:
                        profile = user.member_profile
                        profile.role = role
                        profile.country = form.cleaned_data.get('country') or None
                        profile.country_code = form.cleaned_data.get('country_code') or None
                        profile.phone_number = form.cleaned_data.get('phone_number') or None
                        profile.save()
                    except Exception as e:
                        from miembros.models import MemberProfile
                        MemberProfile.objects.update_or_create(
                            user=user,
                            defaults={
                                'role': role,
                                'country': form.cleaned_data.get('country') or None,
                                'country_code': form.cleaned_data.get('country_code') or None,
                                'phone_number': form.cleaned_data.get('phone_number') or None
                            }
                        )
                
                # Log the user in immediately
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                
                # Store the role in session for profile creation
                request.session['user_role'] = role
                request.session.modified = True
                
                # Store the referer for potential future use
                referer = request.META.get('HTTP_REFERER')
                if referer:
                    request.session['post_registration_redirect'] = referer
                
                # Check if this is a modal submission
                if 'modal' in request.POST or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    # Return JSON response for modal submissions
                    return JsonResponse({
                        'success': True,
                        'message': '¡Registro exitoso! Bienvenido a Ministerios Elim.',
                        'redirect': referer or '/'
                    })
                else:
                    # For regular form submissions, redirect back to referer or home
                    messages.success(request, '¡Registro exitoso! Bienvenido a Ministerios Elim.')
                    return redirect(referer or '/')
        else:
            # Check if this is a modal submission
            if 'modal' in request.POST or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
            else:
                messages.error(request, 'Por favor corrige los errores.')
    else:
        form = ExtendedUserCreationForm()
    
    # Check if this is an AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    return render(request, 'registration/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Get the redirect URL from POST data or session
            redirect_url = request.POST.get('next') or request.session.get('next') or '/'
            
            # Clear the session next parameter
            if 'next' in request.session:
                del request.session['next']
            
            # Check if this is a modal submission
            if 'modal' in request.POST or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # Return JSON response for modal submissions
                return JsonResponse({
                    'success': True,
                    'message': f'¡Bienvenido, {user.get_full_name() or user.username}!',
                    'redirect': redirect_url
                })
            else:
                # For regular form submissions, redirect to the intended page
                return redirect(redirect_url)
        else:
            # Check if this is a modal submission
            if 'modal' in request.POST or request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        # Store the 'next' parameter in session for POST redirect
        if request.GET.get('next'):
            request.session['next'] = request.GET.get('next')
        form = EmailAuthenticationForm()
    
    # Check if this is an AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    return render(request, 'registration/login.html', {'form': form})


def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except Exception:
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        # Log the user in after activation
        login(request, user)
        messages.success(request, 'Cuenta activada. Ahora estás conectado.')
        
        # Redirect to the stored referer or home page
        redirect_url = request.session.pop('post_activation_redirect', '/')
        return redirect(redirect_url)
    else:
        messages.error(request, 'El enlace de activación no es válido o ha caducado.')
        return redirect('/')
