from django.urls import path
from . import views

app_name = 'pastores'

urlpatterns = [
    path('', views.profile_view, name='profile'),
    path('crear/', views.create_profile, name='create_profile'),
    path('biografia/<int:pk>/', views.biography_detail, name='biography_detail'),
]
