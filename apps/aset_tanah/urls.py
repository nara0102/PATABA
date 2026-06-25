# aset_tanah/urls.py
from django.urls import path
from . import views

app_name = 'tanah' # nama namespace aplikasi

urlpatterns = [
    # Master Data & Transaksi Aset
    path('aset/tanah/daftar/', views.list_aset_tanah, name='list_aset_tanah'),
    path('aset/kendaraan/daftar/', views.list_aset_kendaraan, name='list_aset_kendaraan'),
    path('aset/tanah/tambah/', views.input_aset_tanah, name='input_aset_tanah'),
    path('aset/input/tanah/', views.input_aset_tanah, name='input_aset_tanah_alt'), # Cadangan rute lama
    path('aset/tanah/detail/<int:pk>/', views.detail_aset_tanah, name='detail_aset_tanah'),
    path('aset/tanah/edit/<int:pk>/', views.edit_aset_tanah, name='edit_aset_tanah'),
    path('aset/tanah/hapus/<int:pk>/', views.delete_aset_tanah, name='delete_aset_tanah'),
    
    # Manajemen Sertifikasi & Dokumen BPN
    path('aset/tanah/<int:aset_id>/sertifikat/tambah/', views.tambah_sertifikat, name='tambah_sertifikat'),
    path('aset/tanah/sertifikat/daftar/', views.list_sertifikat, name='list_sertifikat'),
    path('aset/tanah/sertifikat/edit/<int:sertifikat_id>/', views.edit_sertifikat, name='edit_sertifikat'),
    path('sertifikat/hapus/<int:sertifikat_id>/', views.delete_sertifikat, name='delete_sertifikat'),
    
    # Sertif pembebasan
    path('pembebasan-lahan/', views.list_pembebasan_lahan, name='list_pembebasan_lahan'),
    
    
    # API Gateway Lokasi Dinamis
    # path('api/get-kelurahan/', views.get_kelurahan_by_kecamatan, name='api_get_kelurahan'),
    
    # Excel
    path('export/excel/', views.export_excel_aset, name='export_excel_aset'),
]