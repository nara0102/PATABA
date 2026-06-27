from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db import transaction, IntegrityError
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, Count
from django.db.models.functions import ExtractMonth
from functools import wraps
import json

# 1. Impor Model Milik Manajemen Pengguna Sendiri
from .models import UserProfile, AuditLog

# 2. Impor MasterOPD & AsetTanah (Untuk hitungan Dashboard)
from apps.aset_tanah.models import MasterOPD, AsetTanah

# 3. Impor PublikasiInstansi (Untuk list berita di Dashboard BPKAD)
from apps.portal_publik.models import PublikasiInstansi


from pataba_core.constants import ROLE_OPERATOR, ROLE_ADMIN, ROLE_SUPER, STATUS_PENDING, STATUS_VALID, STATUS_REVIEW

# - - - - -
# FUNGSI UTILITY UNTUK ROLE CHECKING (SUDAH DIPERBAIKI ANTI-LOOPING)
# - - - - -

def is_superadmin(user):
    return user.is_authenticated and user.is_superuser

def is_admin_bpkad(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        # Menggunakan Query langsung agar tidak terjebak error hasattr(user, 'profile')
        profile = UserProfile.objects.get(user=user)
        return profile.role.strip().upper() == 'ADMIN_BPKAD'
    except UserProfile.DoesNotExist:
        return False

def is_operator(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True # Opsional, jika superuser boleh lihat halaman OPD
    try:
        profile = UserProfile.objects.get(user=user)
        role_ok = (profile.role.strip().upper() == 'OPERATOR_OPD')
        return role_ok
    except UserProfile.DoesNotExist:
        return False
def role_required(allowed_roles=[]):
    def decorator(view_func):
        @wraps(view_func)
        def wrap(request, *args, **kwargs):
            # 1. Cek Login
            if not request.user.is_authenticated:
                return redirect('auth:login')
            
            # 2. Cek Superuser
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # 3. Cek Profil & Role secara aman
            try:
                profile = UserProfile.objects.get(user=request.user)
                user_role = profile.role.strip().upper()
                
                if user_role in [r.upper().strip() for r in allowed_roles]:
                    # Cek spesifik untuk operator harus punya OPD
                    if user_role == 'OPERATOR_OPD' and profile.opd is None:
                        raise PermissionDenied
                    return view_func(request, *args, **kwargs)
                else:
                    raise PermissionDenied
                    
            except UserProfile.DoesNotExist:
                return redirect('auth:login')
                
        return wrap
    return decorator

# - - - - -
# AUTENTIKASI
# - - - - - 

def login_view(request):
    opd_list = MasterOPD.objects.filter(is_active=1)
    
    aset_valid = AsetTanah.objects.filter(status_verifikasi='VALID')
    total_aset = aset_valid.count()
    aset_bersertifikat = aset_valid.filter(status_sertifikasi='BERSERTIFIKAT').count()
    
    persen = 0
    if total_aset > 0:
        persen = int((aset_bersertifikat / total_aset) * 100)
    
    context = {
        'opd_list': opd_list,
        'total_aset': total_aset,
        'persentase_sertifikat': persen,
    }
    
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        
        try:
            # 1. Tarik data user langsung dari database (jangan pakai authenticate dulu)
            user_check = User.objects.get(username=u)
            
            # 2. Cek kecocokan password
            if not user_check.check_password(p):
                messages.error(request, "Username atau password salah.")
                
            # 3. Cek status aktif (Pesan ini sekarang PASTI muncul jika belum di-ACC)
            elif not user_check.is_active:
                messages.error(request, "Akun belum diverifikasi oleh Admin Pusat.")
                
            # 4. Jika password benar dan akun aktif, baru eksekusi login
            else:
                user = authenticate(request, username=u, password=p)
                if user is not None:
                    login(request, user)
                    
                    if request.POST.get('remember_me'):
                        request.session.set_expiry(1209600)
                    else:
                        request.session.set_expiry(0)
                    
                    if user.is_superuser:
                        messages.success(request, f"Login berhasil, Superadmin {user.first_name}!")
                        return redirect('auth:dashboard_superadmin')
                    
                    try:
                        profile = UserProfile.objects.get(user=user)
                        role_di_db = profile.role.strip().upper()
                        
                        if role_di_db == 'ADMIN_BPKAD':
                            messages.success(request, f"Login berhasil, Admin BPKAD {user.first_name}!")
                            return redirect('auth:dashboard_bpkad')
                        elif role_di_db == 'OPERATOR_OPD':
                            messages.success(request, f"Login berhasil, Operator OPD {user.first_name}!")
                            return redirect('auth:dashboard_opd')
                        else:
                            logout(request)
                            messages.error(request, "Role akun tidak valid.")
                            
                    except UserProfile.DoesNotExist:
                        logout(request)
                        messages.error(request, "Akun tidak memiliki profil akses. Hubungi Admin Pusat.")
                        
        except User.DoesNotExist:
            # Jika username memang tidak ada di database sama sekali
            messages.error(request, "Username atau password salah.")
                    
    return render(request, 'manajemen_pengguna/login.html', context)


# - - - - -
# FUNGSI UTILITIES: PEREKAM AUDIT LOG
# - - - - -
def catat_aktivitas(user, aksi, objek, request=None):
    """
    SOP Keamanan: Mencatat setiap aktivitas user ke dalam tabel AuditLog
    """
    from apps.manajemen_pengguna.models import AuditLog
    
    # Deteksi IP Address User
    ip = ""
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

    # Tulis ke Database
    AuditLog.objects.create(
        user=user,
        username=user.username,
        aksi=aksi,
        objek=objek,
        ip_address=ip
    )
    
def register_view(request):
    opd_list = MasterOPD.objects.filter(is_active=1).order_by('nama_opd')
    aset_valid = AsetTanah.objects.filter(status_verifikasi='VALID')
    total_aset = aset_valid.count()
    aset_bersertifikat = aset_valid.filter(status_sertifikasi='BERSERTIFIKAT').count()
    persen = int((aset_bersertifikat / total_aset) * 100) if total_aset > 0 else 0

    context = {
        'opd_list': opd_list,
        'total_aset': total_aset,
        'persentase_sertifikat': persen,
    }

    if request.method == 'POST':
        # Tangkap semua inputan
        email = request.POST.get('email', '').strip()
        username = request.POST.get('reg_username', '').strip()
        password = request.POST.get('reg_password', '')
        nama_lengkap = request.POST.get('nama_lengkap', '').strip()
        role = request.POST.get('role', '')
        opd_id = request.POST.get('opd_id', '')
        
        nip_raw = request.POST.get('nip', '')
        nip = nip_raw.replace(' ', '') if nip_raw else '' # Otomatis hapus spasi
        
        jabatan = request.POST.get('jabatan', '').strip()
        nomor_hp = request.POST.get('nomor_hp', '').strip()

        # 2. SIMPAN INPUTAN KE DALAM CONTEXT (Agar tidak hilang saat halaman di-render ulang karena error)
        context['form_data'] = {
            'email': email,
            'reg_username': username,
            'nama_lengkap': nama_lengkap,
            'role': role,
            'opd_id': opd_id,
            'nip': nip_raw,
            'jabatan': jabatan,
            'nomor_hp': nomor_hp,
        }

        # VALIDASI 1: Cek Username Ganda
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username sudah digunakan. Silakan gunakan yang lain.")
            return render(request, 'manajemen_pengguna/login.html', context)
        
        # VALIDASI 2: Cek Email Ganda
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email sudah terdaftar. Silakan gunakan email lain.")
            return render(request, 'manajemen_pengguna/login.html', context)

        # VALIDASI 3: Cek OPD Valid
        opd_obj = None
        if role.upper() == 'OPERATOR_OPD':
            if not opd_id or opd_id == 'tambah_baru':
                messages.error(request, "Harap pilih Instansi/OPD yang valid.")
                return render(request, 'manajemen_pengguna/login.html', context)
            try:
                opd_obj = MasterOPD.objects.get(id=opd_id)
            except MasterOPD.DoesNotExist:
                messages.error(request, "Instansi/OPD tidak ditemukan dalam sistem.")
                return render(request, 'manajemen_pengguna/login.html', context)

        if ' ' in nama_lengkap:
            first_name, last_name = nama_lengkap.split(' ', 1)
        else:
            first_name, last_name = nama_lengkap, ''

        # PROSES SIMPAN DATA
        try:
            with transaction.atomic(): # Transaksi atomik wajib di sini untuk mencegah akun hantu
                user = User(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                )
                user.is_active = False
                user.password = make_password(password)
                user.save()

                UserProfile.objects.create(
                    user=user,
                    role=role.upper(),
                    opd=opd_obj,
                    nip=nip,
                    jabatan=jabatan,
                    nomor_hp=nomor_hp,
                    is_active=0,
                    created_at=timezone.now()
                )
        except Exception as e:
            messages.error(request, f"Pendaftaran gagal. Kesalahan sistem: {str(e)}")
            return render(request, 'manajemen_pengguna/login.html', context)
        
        try:
            send_mail(
                'Konfirmasi Pendaftaran',
                'Akun Anda menunggu persetujuan Admin Pusat.',
                'Salam,\nTim TRANSPARA',
                [email],
                fail_silently=True,
            )
        except Exception:
            pass

        messages.success(request, "Pendaftaran berhasil! Akun menunggu persetujuan Admin.")
        return redirect('auth:login')
        
    return render(request, 'manajemen_pengguna/login.html', context)

# - - - - -
# DASHBOARD
# - - - - -

def dashboard_router(request):
    if not request.user.is_authenticated:
        return redirect('auth:login')
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role.strip().upper() == 'OPERATOR_OPD':
            return redirect('auth:dashboard_opd') 
    except:
        pass
    return redirect('auth:dashboard_bpkad')

# SEMUA DECORATOR TELAH DIPERBAIKI (Ditambahkan login_url='auth:login')
@login_required(login_url='auth:login')
@user_passes_test(is_superadmin, login_url='auth:login')
def dashboard_superadmin_view(request):
    antrean_user = UserProfile.objects.select_related('user', 'opd').filter(is_active=0)
    antrean_opd = MasterOPD.objects.filter(is_active=0)
    
    total_admin = UserProfile.objects.filter(role__iexact='ADMIN_BPKAD', is_active=1).count()
    total_operator = UserProfile.objects.filter(role__iexact='OPERATOR_OPD', is_active=1).count()
    total_opd_aktif = MasterOPD.objects.filter(is_active=1).count()

    context = {
        'antrean_user': antrean_user,
        'antrean_opd': antrean_opd,
        'jumlah_antrean_user': antrean_user.count(),
        'jumlah_antrean_opd': antrean_opd.count(),
        'total_admin': total_admin,
        'total_operator': total_operator,
        'total_opd_aktif': total_opd_aktif,
    }
    return render(request, 'manajemen_pengguna/dashboard_superadmin.html', context) 

@login_required(login_url='auth:login')
@user_passes_test(is_admin_bpkad, login_url='auth:login') 
def dashboard_bpkad_view(request):
    semua_aset = AsetTanah.objects.all().order_by('-created_at')
    antrean_aset = semua_aset.filter(status_verifikasi='BELUM_DIVERIFIKASI')
    jumlah_antrean = antrean_aset.count()
    aset_bermasalah = semua_aset.filter(kondisi_pemanfaatan__in=['SENGKETA', 'RUSAK']).count()
    
    aset_valid = semua_aset.filter(status_verifikasi='VALID')
    total_aset = aset_valid.count()
    total_nilai = aset_valid.aggregate(Sum('nilai_aset'))['nilai_aset__sum'] or 0
    
    aset_bersertifikat = aset_valid.filter(status_sertifikasi='BERSERTIFIKAT').count()
    aset_sertifikat_lainnya = aset_valid.filter(status_sertifikasi='LAINNYA').count()
    aset_belum_sertifikat = aset_valid.filter(status_sertifikasi='BELUM_BERSERTIFIKAT').count()
    persen_bersertifikat = (aset_bersertifikat / total_aset * 100) if total_aset > 0 else 0
    
    list_berita_pengumuman = PublikasiInstansi.objects.filter(
        kategori__in=['BERITA', 'PENGUMUMAN'], is_published=True
    ).order_by('-tanggal_upload')[:3]
    
    list_kegiatan = PublikasiInstansi.objects.filter(
        kategori='KEGIATAN', is_published=True
    ).order_by('-tanggal_upload')[:3]
    
    logs_aktivitas_qs = AuditLog.objects.all().order_by('-waktu')[:30] 
    log_data = []
    for log in logs_aktivitas_qs:
        waktu_lokal = timezone.localtime(log.waktu) if log.waktu else None
        log_data.append({
            'user': log.username if log.username else "Sistem",
            'aksi': log.aksi,
            'objek': log.objek,
            'waktu': waktu_lokal.strftime("%d %b %Y, %H:%M") if waktu_lokal else "-"
        })

    try:
        tahun_grafik = int(request.GET.get('tahun', timezone.now().year))
    except ValueError:
        tahun_grafik = timezone.now().year

    tahun_tersedia = aset_valid.filter(tanggal_perolehan__isnull=False)\
                               .values_list('tanggal_perolehan__year', flat=True)\
                               .distinct().order_by('-tanggal_perolehan__year')
    list_tahun = list(tahun_tersedia)
    if not list_tahun: list_tahun = [timezone.now().year]
    if tahun_grafik not in list_tahun:
        list_tahun.append(tahun_grafik)
        list_tahun.sort(reverse=True)

    grafik_data = (aset_valid.filter(tanggal_perolehan__year=tahun_grafik)
        .annotate(bulan=ExtractMonth('tanggal_perolehan')).values('bulan')
        .annotate(jumlah=Count('id')).order_by('bulan'))

    data_bulanan = [0] * 12
    for item in grafik_data:
        if item['bulan']: data_bulanan[item['bulan'] - 1] = item['jumlah']

    context = {
        'total_aset': total_aset, 'total_nilai': total_nilai,
        'aset_bersertifikat': aset_bersertifikat, 'aset_belum_sertifikat': aset_belum_sertifikat,
        'aset_sertifikat_lainnya': aset_sertifikat_lainnya, 'persen_bersertifikat': persen_bersertifikat,
        'jumlah_antrean': jumlah_antrean, 'aset_bermasalah': aset_bermasalah,
        'antrean_aset': antrean_aset[:5], 'semua_aset': semua_aset[:5],
        'list_berita_pengumuman': list_berita_pengumuman, 'list_kegiatan': list_kegiatan,
        'logs_aktivitas': log_data, 'data_grafik_bulanan': json.dumps(data_bulanan), 
        'tahun_grafik': int(tahun_grafik), 'list_tahun': list_tahun,
    }
    return render(request, 'manajemen_pengguna/dashboard_BPKAD.html', context)

@login_required(login_url='auth:login')
@user_passes_test(is_operator, login_url='auth:login')
def dashboard_opd_view(request):
    from django.http import HttpResponse
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return HttpResponse("Profil tidak ditemukan!")
    
    opd = profile.opd # Gunakan id_opd atau opd sesuai struktur field model
    aset_opd = AsetTanah.objects.filter(opd=opd).order_by('-created_at')
    aset_valid = aset_opd.filter(status_verifikasi='VALID')
    
    context = {
        'opd': opd, 'semua_aset': aset_opd, 'total_aset': aset_valid.count(), 
        'bersertifikat': aset_valid.filter(status_sertifikasi='BERSERTIFIKAT').count(),
        'belum_diverifikasi': aset_opd.filter(status_verifikasi='BELUM_DIVERIFIKASI').count(), 
        'sengketa': aset_valid.filter(kondisi_pemanfaatan='SENGKETA').count(),
    }
    return render(request, 'manajemen_pengguna/dashboard_OPD.html', context)

# - - - - -
# PERSETUJUAN & TOLAK
# - - - - -

@login_required(login_url='auth:login')
@user_passes_test(is_superadmin, login_url='auth:login')
def setujui_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = True
    user.save()
    try:
        profile = UserProfile.objects.get(user=user)
        profile.is_active = 1
        profile.save()
        send_mail('Akun Anda Diaktifkan', 'Akun telah diaktifkan.', settings.EMAIL_HOST_USER, [user.email], fail_silently=True)
        messages.success(request, f"Akun {user.username} berhasil diaktifkan!")
    except UserProfile.DoesNotExist:
        messages.error(request, "Profil tidak ada.")
    return redirect('auth:dashboard_superadmin')

@login_required(login_url='auth:login')
@user_passes_test(is_superadmin, login_url='auth:login')
def setujui_opd(request, opd_id):
    opd = get_object_or_404(MasterOPD, id=opd_id)
    opd.is_active = 1
    opd.save()
    if opd.email_resmi:
        send_mail('Instansi Disetujui', 'Instansi disetujui.', settings.EMAIL_HOST_USER, [opd.email_resmi], fail_silently=True)
    messages.success(request, f"OPD {opd.nama_opd} berhasil diaktifkan.")
    return redirect('auth:dashboard_superadmin')

@login_required(login_url='auth:login')
@user_passes_test(is_superadmin, login_url='auth:login')
def tolak_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, f"User {user.username} ditolak & dihapus.")
    return redirect('auth:dashboard_superadmin')

@login_required(login_url='auth:login')
@user_passes_test(is_superadmin, login_url='auth:login')
def tolak_opd(request, opd_id):
    opd = get_object_or_404(MasterOPD, id=opd_id)
    opd.delete()
    messages.success(request, f"OPD {opd.nama_opd} ditolak & dihapus.")
    return redirect('auth:dashboard_superadmin')

@login_required(login_url='auth:login')
@user_passes_test(is_superadmin, login_url='auth:login')
def hapus_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    username = user.username
    user.delete() 
    messages.success(request, f"Pengguna {username} telah dihapus.")
    return redirect(request.META.get('HTTP_REFERER', 'auth:dashboard_superadmin'))

# - - - - -
# KELOLA OPD
# - - - - -

def input_opd_publik_view(request):
    if request.method == 'POST':
        nama = request.POST.get('nama_opd')
        try:
            MasterOPD.objects.create(
                nama_opd=nama, singkatan=request.POST.get('singkatan'), kode_opd=request.POST.get('kode_opd'),
                kode_lokasi=request.POST.get('kode_lokasi'), kategori_opd=request.POST.get('kategori_opd'),
                kepala_opd=request.POST.get('kepala_opd'), email_resmi=request.POST.get('email_opd'),
                alamat_kantor=request.POST.get('alamat_kantor'), is_active=0, created_at=timezone.now()
            )
            messages.success(request, "Pendaftaran berhasil, tunggu persetujuan Admin Pusat.")
            return redirect('auth:login')
        except IntegrityError:
            messages.error(request, f"Gagal: OPD '{nama}' sudah terdaftar.")
    return render(request, 'manajemen_pengguna/input_OPD_publik.html')

@login_required(login_url='auth:login')
@user_passes_test(is_superadmin, login_url='auth:login')
def input_opd_sadmin_view(request):
    if request.method == 'POST':
        nama = request.POST.get('nama_opd')
        try:
            MasterOPD.objects.create(
                nama_opd=nama, singkatan=request.POST.get('singkatan'), kode_opd=request.POST.get('kode_opd'),
                kode_lokasi=request.POST.get('kode_lokasi'), kategori_opd=request.POST.get('kategori_opd'),
                kepala_opd=request.POST.get('kepala_opd'), email_resmi=request.POST.get('email_opd'),
                alamat_kantor=request.POST.get('alamat_kantor'), is_active=1, created_at=timezone.now()
            )
            messages.success(request, f"OPD {nama} berhasil ditambahkan.")
            return redirect('auth:daftar_opd')
        except IntegrityError:
            messages.error(request, f"Gagal: Instansi '{nama}' sudah ada.")
    return render(request, 'manajemen_pengguna/input_OPD_SAdmin.html')

@login_required(login_url='auth:login')
@user_passes_test(is_superadmin, login_url='auth:login')
def daftar_opd_view(request):
    semua_opd = MasterOPD.objects.all().order_by('-created_at')
    context = {
        'daftar_opd': semua_opd, 'total_opd': semua_opd.count(),
        'total_aktif': semua_opd.filter(is_active=1).count(), 'total_tidak': semua_opd.filter(is_active=2).count(),
    }
    return render(request, 'manajemen_pengguna/daftar_opd.html', context)

@login_required(login_url='auth:login')
@user_passes_test(is_admin_bpkad, login_url='auth:login')
def detail_opd_view(request, opd_id):
    opd = get_object_or_404(MasterOPD, id=opd_id)
    return render(request, 'manajemen_pengguna/detail_opd.html', {'opd': opd, 'title': f"Detail {opd.singkatan or opd.nama_opd}"})

@login_required(login_url='auth:login')
@user_passes_test(is_superadmin, login_url='auth:login')
def edit_opd_view(request, opd_id):
    opd = get_object_or_404(MasterOPD, id=opd_id)
    if request.method == 'POST':
        opd.nama_opd = request.POST.get('nama_opd')
        opd.singkatan = request.POST.get('singkatan')
        opd.kode_opd = request.POST.get('kode_opd')
        opd.kode_lokasi = request.POST.get('kode_lokasi')
        opd.kategori_opd = request.POST.get('kategori_opd')
        opd.kepala_opd = request.POST.get('kepala_opd')
        opd.email_resmi = request.POST.get('email_opd')
        opd.alamat_kantor = request.POST.get('alamat_kantor')
        try:
            opd.save()
            messages.success(request, f"Data {opd.nama_opd} diperbarui.")
            return redirect('auth:detail_opd', opd_id=opd.id)
        except IntegrityError:
            messages.error(request, "Gagal update: Instansi sudah ada.")
    return render(request, 'manajemen_pengguna/input_OPD_SAdmin.html', {'opd': opd, 'title': f"Edit {opd.singkatan or opd.nama_opd}"})

@login_required(login_url='auth:login')
@user_passes_test(is_superadmin, login_url='auth:login')
def hapus_opd(request, opd_id):
    opd = get_object_or_404(MasterOPD, id=opd_id)
    nama = opd.nama_opd
    opd.delete()
    messages.success(request, f"OPD {nama} dihapus.")
    return redirect('auth:daftar_opd')

# - - - - -
# KELOLA PENGGUNA
# - - - - -

@login_required(login_url='auth:login')
@user_passes_test(is_superadmin, login_url='auth:login')
def daftar_operator_opd(request):
    users = UserProfile.objects.select_related('user', 'opd').filter(role__iexact='OPERATOR_OPD')
    return render(request, 'manajemen_pengguna/daftar_pengguna.html', {'users': users, 'title': 'Operator OPD'})

@login_required(login_url='auth:login')
@user_passes_test(is_superadmin, login_url='auth:login')
def daftar_admin_bpkad(request):
    users = UserProfile.objects.select_related('user').filter(role__iexact='ADMIN_BPKAD')
    return render(request, 'manajemen_pengguna/daftar_pengguna.html', {'users': users, 'title': 'Admin BPKAD'})

@login_required(login_url='auth:login')
@user_passes_test(is_superadmin, login_url='auth:login')
def detail_pengguna_view(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(UserProfile, user=target_user)
    return render(request, 'manajemen_pengguna/detail_pengguna.html', {'target_user': target_user, 'profile': profile, 'title': f"Profil @{target_user.username}"})

@login_required(login_url='auth:login')
@user_passes_test(is_superadmin, login_url='auth:login')
def edit_pengguna_view(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(UserProfile, user=target_user)
    daftar_opd = MasterOPD.objects.all()

    if request.method == 'POST':
        target_user.username = request.POST.get('username')
        target_user.email = request.POST.get('email')
        nama_lengkap = request.POST.get('nama_lengkap', '').strip()
        
        if ' ' in nama_lengkap:
            target_user.first_name, target_user.last_name = nama_lengkap.split(' ', 1)
        else:
            target_user.first_name, target_user.last_name = nama_lengkap, ''

        profile.nip = request.POST.get('nip')
        profile.jabatan = request.POST.get('jabatan')
        profile.nomor_hp = request.POST.get('nomor_hp')
        role = request.POST.get('role', profile.role).upper()
        profile.role = role
        
        opd_id = request.POST.get('opd_id')
        if opd_id and role == 'OPERATOR_OPD':  
            try:
                # PERBAIKAN: Gunakan 'profile.opd' sesuai field di models.py
                profile.opd = MasterOPD.objects.get(id=opd_id) 
            except MasterOPD.DoesNotExist:
                messages.error(request, "Gagal: OPD tidak ditemukan di database.")
                return redirect('auth:edit_pengguna', user_id=target_user.id) 
        elif role == 'ADMIN_BPKAD':
             profile.opd = None 

        # --- TANGKAP FOTO PROFIL (TAMBAHAN BARU) ---
        if 'foto_profil' in request.FILES:
            profile.foto_profil = request.FILES['foto_profil']

        try:
            target_user.save()
            profile.save()
            
            # --- CATAT AKTIVITAS (SOP KEAMANAN) ---
            catat_aktivitas(request.user, "Mengedit Profil & Foto Pengguna", f"@{target_user.username}", request)

            messages.success(request, f"Profil @{target_user.username} diperbarui.")
            return redirect('auth:detail_pengguna', user_id=target_user.id) 
        except IntegrityError:
             messages.error(request, "Username atau Email telah digunakan.")

    # Jika kamu mau render ke HTML pengaturan_profil yang baru, cukup ubah nama file HTML-nya di bawah ini:
    return render(request, 'manajemen_pengguna/edit_pengguna.html', {
        'target_user': target_user, 'profile': profile, 'daftar_opd': daftar_opd,
        'nama_lengkap_awal': f"{target_user.first_name} {target_user.last_name}".strip(),
        'title': f"Edit - @{target_user.username}"
    })
    

@login_required(login_url='auth:login')
def pengaturan_profil_view(request):
    target_user = request.user
    profile = get_object_or_404(UserProfile, user=target_user)

    if request.method == 'POST':
        # 1. Tangkap sesuai atribut name="" di HTML
        target_user.first_name = request.POST.get('first_name', '').strip()
        target_user.last_name = request.POST.get('last_name', '').strip()
        target_user.email = request.POST.get('email', '').strip()
        
        profile.nomor_hp = request.POST.get('nomor_hp', '').strip()
        profile.nip = request.POST.get('nip', '').strip()
        profile.jabatan = request.POST.get('jabatan', '').strip()

        # 2. Tangkap Foto
        if 'foto_profil' in request.FILES:
            profile.foto_profil = request.FILES['foto_profil']

        try:
            # 3. KUNCI TRANSAKSI: Jika gagal satu, batalkan semua
            with transaction.atomic():
                target_user.save()
                profile.save()
            
            # Jika lolos sampai sini, catat ke log dan sukses
            catat_aktivitas(request.user, "Mengedit Profil Sendiri", "Pengaturan Akun", request)
            messages.success(request, "Profil Anda berhasil diperbarui.")
            
            return redirect('auth:pengaturan_profil') # Sesuaikan nama url kamu
            
        except Exception as e:
             # Jika S3 error, data yang kosong tadi TIDAK akan tersimpan ke database
             messages.error(request, f"Terjadi kesalahan: {str(e)}")

    return render(request, 'manajemen_pengguna/pengaturan_profil.html', {
        'user': target_user,
        'profile': profile,
    })