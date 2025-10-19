from django.urls import path
from . import views

app_name = 'iglesias'

urlpatterns = [
    path('', views.iglesias_index, name='index'),
    path('mi-iglesia/', views.my_iglesias, name='my_iglesias'),
    path('crear/', views.create_iglesia, name='create_iglesia'),
    path('editar/<int:pk>/', views.edit_iglesia, name='edit_iglesia'),
    path('<int:pk>/', views.iglesia_detail, name='iglesia_detail'),
]
