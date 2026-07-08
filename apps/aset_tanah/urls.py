# aset_tanah/urls.py
from django.urls import path
from . import views

app_name = 'tanah' #  namespace aplikasi

urlpatterns = [
    
    # Master Data & Transaksi Aset
    path('aset/tanah/daftar/', views.list_aset_tanah, name='list_aset_tanah'),
    path('aset/kendaraan/daftar/', views.list_aset_kendaraan, name='list_aset_kendaraan'),
    path('aset/tanah/tambah/', views.input_aset_tanah, name='input_aset_tanah'),
    path('aset/tanah/detail/<int:pk>/', views.detail_aset_tanah, name='detail_aset_tanah'),
    path('aset/tanah/edit/<int:pk>/', views.edit_aset_tanah, name='edit_aset_tanah'),
    path('aset/tanah/hapus/<int:pk>/', views.delete_aset_tanah, name='delete_aset_tanah'),
    
    # Manajemen Sertifikasi & Dokumen BPN
    path('aset/tanah/<int:aset_id>/sertifikat/tambah/', views.tambah_sertifikat, name='tambah_sertifikat'),
    path('aset/tanah/sertifikat/daftar/', views.list_sertifikat, name='list_sertifikat'),
    path('aset/tanah/sertifikat/edit/<int:sertifikat_id>/', views.edit_sertifikat, name='edit_sertifikat'),
    path('sertifikat/hapus/<int:sertifikat_id>/', views.delete_sertifikat, name='delete_sertifikat'),
    path('sertifikat/<int:sertifikat_id>/detail/', views.detail_sertifikat, name='detail_sertifikat'),
    
    # Sertif pembebasan
    path('pembebasan-lahan/', views.list_pembebasan_lahan, name='list_pembebasan_lahan'),
    
    
    # API Gateway Lokasi Dinamis
    # path('api/get-kelurahan/', views.get_kelurahan_by_kecamatan, name='api_get_kelurahan'),
    
    # Excel
    path('export/konfigurasi/', views.halaman_export_excel, name='halaman_export_excel'),
    path('export/proses-excel/', views.proses_export_excel, name='proses_export_excel'),
    
    path('aset/tanah/import/', views.halaman_import_view, name='halaman_import'),
    path('laporan/import-excel/proses/', views.proses_import_excel, name='proses_import_excel'),
    
    path('aset/tanah/template-import/', views.unduh_template_import, name='unduh_template_import'),
    
    # PDF
    path('detail/<int:id_aset>/pdf/', views.export_pdf_detail, name='export_pdf_detail'),
    
    path('laporan/export-pdf/', views.halaman_export_pdf, name='halaman_export_pdf'),
    path('laporan/rekap-sertif/pdf/', views.export_pdf_rekap_sertif, name='export_pdf_rekap_sertif'),
    path('laporan/aset-opd/pdf/', views.export_pdf_aset_opd, name='export_pdf_aset_opd'),
]