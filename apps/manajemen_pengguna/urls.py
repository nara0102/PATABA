# manajemen_pengguna/urls.py
from django.urls import path
from . import views

app_name = 'auth' # Mengunci nama namespace aplikasi

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register_view'),
    
    # Dasbor Router & Hak Akses Role
    path('dashboard/', views.dashboard_router, name='dashboard_router'),
    path('superadmin/', views.dashboard_superadmin_view, name='dashboard_superadmin'),
    path('admin-bpkad/', views.dashboard_bpkad_view, name='dashboard_bpkad'),
    path('opd/', views.dashboard_opd_view, name='dashboard_opd'),
    
    # Manajemen Pendaftaran OPD
    path('input-opd-publik/', views.input_opd_publik_view, name='input_opd_publik'),
    path('input_opd_sadmin/', views.input_opd_sadmin_view, name='input_opd_sadmin'),
    path('daftar-opd/', views.daftar_opd_view, name='daftar_opd'),
    path('hapus-opd/<int:opd_id>/', views.hapus_opd, name='hapus_opd'),
    path('opd/detail/<int:opd_id>/', views.detail_opd_view, name='detail_opd'),
    path('opd/edit/<int:opd_id>/', views.edit_opd_view, name='edit_opd'),
    
    # Persetujuan & Penolakan Akses (Superadmin)
    path('setujui-opd/<int:opd_id>/', views.setujui_opd, name='setujui_opd'),
    path('setujui-user/<int:user_id>/', views.setujui_user, name='setujui_user'),
    path('tolak-user/<int:user_id>/', views.tolak_user, name='tolak_user'),
    path('tolak-opd/<int:opd_id>/', views.tolak_opd, name='tolak_opd'),
    
    # Manajemen Pengguna / Akun Staff
    path('pengguna/operator-opd/', views.daftar_operator_opd, name='daftar_operator_opd'),
    path('pengguna/admin-bpkad/', views.daftar_admin_bpkad, name='daftar_admin_bpkad'),
    path('pengguna/hapus/<int:user_id>/', views.hapus_user, name='delete_user'),
    path('pengguna/detail/<int:user_id>/', views.detail_pengguna_view, name='detail_pengguna'),
    path('pengguna/edit/<int:user_id>/', views.edit_pengguna_view, name='edit_pengguna'),
    
    # Pengaturan Profil
    path('pengaturan/', views.pengaturan_profil_view, name='pengaturan_profil'),
]