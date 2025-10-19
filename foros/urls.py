from django.urls import path
from . import views

app_name = 'foros'

urlpatterns = [
    path('', views.forum_list, name='forum_list'),
    path('<int:pk>/', views.forum_detail, name='forum_detail'),
    path('<int:forum_pk>/topics/<int:topic_pk>/', views.topic_detail, name='topic_detail'),
    path('<int:forum_pk>/topics/create/', views.create_topic, name='create_topic'),
    path('<int:forum_pk>/topics/<int:topic_pk>/posts/create/', views.create_post, name='create_post'),
    # API endpoints
    path('<int:forum_pk>/api/topics/', views.topics_api, name='topics_api'),
    path('<int:forum_pk>/api/topics/<int:topic_pk>/posts/', views.posts_api, name='posts_api'),
]
