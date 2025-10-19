from django.urls import path
from . import views

app_name = 'doctrina'

urlpatterns = [
    path('crear/<str:section>/', views.create_doctrina_entry, name='create_entry'),
]
