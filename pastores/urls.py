from django.urls import path
from . import views

app_name = 'pastores'

urlpatterns = [
    path('', views.profile_view, name='profile'),
    path('crear/', views.create_profile, name='create_profile'),
]
