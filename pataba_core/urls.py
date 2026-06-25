from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.aset_tanah import views as tanah_views

urlpatterns = [
    path('admin-django/', admin.site.urls), 
    path('', include('apps.portal_publik.urls')),
    path('auth/', include('apps.manajemen_pengguna.urls')),
    path('tanah/', include('apps.aset_tanah.urls')),
    path('api/get-kelurahan/', tanah_views.get_kelurahan_by_kecamatan, name='api_get_kelurahan'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)