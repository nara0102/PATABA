# portal_publik/urls.py
from django.urls import path
from . import views

app_name = 'publik' # Mengunci nama namespace aplikasi

urlpatterns = [
    path('', views.index_view, name='home'),
    path('peta_gis/', views.peta_gis_view, name='peta_gis'),
    path('kontak/', views.hubungi_kami, name='kontak'),
    path('aset/kendaraan/coming-soon/', views.coming_soon_view, name='coming_soon_kendaraan'),
    path('bantuan/', views.bantuan_view, name='bantuan'),
    
    # data aset 
    path('data-aset/', views.data_aset_publik_view, name='data_aset_publik'),
    
    # Publikasi Media & Konten Internal
    path('publikasi/tambah/', views.tambah_publikasi_view, name='tambah_publikasi'),
    path('publikasi/', views.list_publikasi_view, name='list_publikasi'),
    path('publikasi/edit/<int:pk>/', views.edit_publikasi_view, name='edit_publikasi'),
    path('publikasi/hapus/<int:pk>/', views.delete_publikasi_view, name='delete_publikasi'),
]