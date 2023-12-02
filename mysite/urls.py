from django.conf import settings
from django.urls import re_path as url
#from django.conf.urls import include, url
from django.urls import path
from django.contrib import admin

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls
#from allauth.account.views import LoginView, SignupView, ConfirmEmailView
#from django.contrib.auth import views as auth_views

from search import views as search_views

from django.urls import path, include, re_path

from registration.views import signupView, loginView, logoutView, get_district, get_province

urlpatterns = [
    
    url(r'^django-admin/', admin.site.urls),
    url(r'^admin/', include(wagtailadmin_urls)),
    url(r'^documents/', include(wagtaildocs_urls)),
    url(r'^search/$', search_views.search, name='search'),
    

]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    import debug_toolbar
    urlpatterns = [
    #    path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

    


urlpatterns = urlpatterns + [

    url(r'^registrarse/', signupView, name="registration"),
    
    path('ingresar/', loginView, name = 'login'),
    path('salir/', logoutView, name = 'logout'),
    #url(r'^login/$', auth_views.LoginView.as_view(template_name="registration/account/login.html"), name="login"),
    #url(r'^logout/$', auth_views.LogoutView.as_view(template_name="account/logout.html"), name="logout"),
    url(r'^province/', get_province, name='province'),
    url(r'^district/', get_district, name='district'),
    
    url(r'', include(wagtail_urls)),


]




