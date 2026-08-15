from django.urls import path
from . import views

app_name = 'doctrina'

urlpatterns = [
    # Legacy: redirect to Wagtail admin (kept for backward compat)
    path('crear/<str:section>/', views.create_doctrina_entry, name='create_entry'),

    # NEW: Frontend-friendly views
    path('nuevo/<str:section>/', views.frontend_create_entry, name='frontend_create'),
    path('editar/<int:entry_id>/', views.frontend_edit_entry, name='frontend_edit'),
    path('eliminar/<int:entry_id>/', views.frontend_delete_entry, name='frontend_delete'),
    path('mis-articulos/', views.mis_articulos, name='mis_articulos'),
]
