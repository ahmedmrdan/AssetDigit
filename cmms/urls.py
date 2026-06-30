from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf.urls.i18n import i18n_patterns
from maintenance import views as maint_views

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='maintenance/login.html'), name='login'),
    path('logout/', maint_views.custom_logout, name='logout'),
    path('', include('maintenance.urls')),
    prefix_default_language=False,
)
