"""
URL configuration for YouJudge project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Landing page
    path('', TemplateView.as_view(template_name='landing.html'), name='landing'),

    # App URLs
    path('accounts/', include('apps.accounts.urls')),
    path('dashboard/', include('apps.competitions.urls')),
    path('scoring/', include('apps.scoring.urls')),
    path('notifications/', include('apps.notifications.urls')),

    # API URLs
    path('api/', include([
        path('auth/', include('apps.accounts.api.urls')),
        path('competitions/', include('apps.competitions.api.urls')),
        path('scoring/', include('apps.scoring.api.urls')),
        path('notifications/', include('apps.notifications.api.urls')),
    ])),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='api-docs'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin site
admin.site.site_header = "YouJudge Administration"
admin.site.site_title = "YouJudge Admin"
admin.site.index_title = "Welcome to YouJudge Administration"
