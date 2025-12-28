from django.urls import path
from . import views

app_name = 'iglesias'

urlpatterns = [
    path('', views.iglesias_index, name='index'),
    path('panel/', views.pastor_dashboard, name='pastor_dashboard'),
    path('panel/evento/crear/', views.create_event, name='create_event'),
    path('panel/sermon/crear/', views.create_sermon, name='create_sermon'),
    path('panel/sermon/eliminar/<int:pk>/', views.delete_sermon, name='delete_sermon'),
    path('mi-iglesia/', views.my_iglesias, name='my_iglesias'),
    path('crear/', views.create_iglesia, name='create_iglesia'),
    path('editar/<int:pk>/', views.edit_iglesia, name='edit_iglesia'),
    path('<int:pk>/', views.iglesia_detail, name='iglesia_detail'),
    path('panel/material/crear/', views.create_preach_material, name='create_preach_material'),
    path('panel/material/editar/<int:pk>/', views.edit_preach_material, name='edit_preach_material'),
    path('panel/material/eliminar/<int:pk>/', views.delete_preach_material, name='delete_preach_material'),
    path('material/<int:pk>/', views.preach_material_detail, name='preach_material_detail'),
    path('materiales/', views.materiales_index, name='materiales_index'),
    path('apostol/', views.apostol_dashboard, name='apostol_dashboard'),
]
