from django.urls import path
from . import views

app_name = 'miembros'

urlpatterns = [
    path('profile/', views.member_profile_view, name='profile'),
    path('profile/crear/', views.create_profile, name='create_profile'),
    path('dashboard/', views.member_dashboard, name='dashboard'),
]
