from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import KontakForm

# 1. Impor Model Milik Portal Publik Sendiri
from .models import PublikasiInstansi, PesanKontak
from pataba_core.storages import PublikasiStorage

# 2. Impor Data Aset (Untuk Peta GIS & Halaman Data Aset Publik)
from apps.aset_tanah.models import AsetTanah

# 3. Impor Hak Akses & Perekam Jejak dari Manajemen Pengguna
from apps.manajemen_pengguna.views import catat_aktivitas, is_admin_bpkad

from pataba_core.constants import ROLE_OPERATOR, ROLE_ADMIN, STATUS_PENDING


# - - - - -
# LAMAN
# - - - - -

# 1 - Halaman Utama
def index_view(request):
    # Ambil Jumlah Aset Tanah
    total_aset_tanah = AsetTanah.objects.count()

    # Ambil Data Berita & Pengumuman
    berita_semua = PublikasiInstansi.objects.filter(
        kategori__in=['BERITA', 'PENGUMUMAN'], 
        is_published=True
    ).order_by('-tanggal_upload')
    
    berita_utama = berita_semua.first() # Berita paling baru untuk kotak besar
    list_berita = berita_semua[1:4]     # Berita selanjutnya untuk list di kanan

    # Ambil Data Galeri Kegiatan
    galeri_semua = PublikasiInstansi.objects.filter(
        kategori='KEGIATAN', 
        is_published=True
    ).order_by('-tanggal_upload')
    
    galeri_utama = galeri_semua.first() # Kegiatan terbaru untuk kotak besar
    list_galeri = galeri_semua[1:3]     # Kegiatan selanjutnya untuk tumpukan di kanan

    context = {
        'total_aset_tanah': total_aset_tanah,
        'berita_utama': berita_utama,
        'list_berita': list_berita,
        'galeri_utama': galeri_utama,
        'list_galeri': list_galeri,
    }
    return render(request, 'portal_publik/index.html', context)

def peta_gis_view(request):
    # Kirim data aset ke peta (Hanya yang VALID)
    semua_aset = AsetTanah.objects.filter(status_verifikasi='VALID')
    context = {
        'semua_aset': semua_aset,
    }
    return render(request, 'portal_publik/peta_gis.html', context)

# 3 - Halaman Kontak (hubungi kami)
def hubungi_kami(request):
    if request.method == 'POST':
        form = KontakForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Pesan Anda berhasil terkirim.")
            return redirect('publik:kontak')
        else:
            messages.error(request, "Ada kesalahan pengisian pada form, silakan periksa kembali dengan benar.")
    else:
        form = KontakForm()
    
    return render(request, 'portal_publik/kontak.html', {'form': form})


# - - - - -
# PUBLIKASI KONTEN/MEDIA
# - - - - -

# 1 - Tambah
@login_required(login_url='auth:login')
@user_passes_test(is_admin_bpkad)
def tambah_publikasi_view(request):
    if request.method == 'POST':
        try:
            judul = request.POST.get('judul')
            kategori = request.POST.get('kategori')
            isi_konten = request.POST.get('isi_konten')
            
            # Tangkap file gambar
            gambar = request.FILES.get('gambar_utama')
            
            print("--- DEBUG DATA ---")
            print("Judul:", request.POST.get('judul'))
            print("File Gambar:", gambar)
            if gambar:
                print("Nama File:", gambar.name)
                print("Ukuran:", gambar.size)
            else:
                print("File GAMBAR KOSONG (None)")
            
            # Simpan ke database
            publikasi = PublikasiInstansi(
                judul=judul,
                kategori=kategori,
                isi_konten=isi_konten,
                gambar_utama=gambar,
                diupload_oleh=request.user 
            )
            publikasi.save()
            
            messages.success(request, f"{kategori} berhasil dipublikasikan!")
            return redirect('publik:list_publikasi') # Kalau sukses, lempar ke daftar tabel
            
        except Exception as e: # <-- Indentasi except HARUS sejajar dengan try
            messages.error(request, f"Gagal menyimpan data: {str(e)}")
            return redirect('publik:tambah_publikasi') # Kalau gagal, kembalikan ke form input biar bisa diperbaiki

    # <-- PENTING! JIKA BUKAN POST (Yaitu saat admin baru pertama kali klik tombol "Tulis Baru")
    # Harus ada perintah render di baris paling bawah ini
    return render(request, 'portal_publik/input_publikasi.html')

# 2 - list
@login_required(login_url='auth:login')
@user_passes_test(is_admin_bpkad)
def list_publikasi_view(request):
    semua_publikasi = PublikasiInstansi.objects.all().order_by('-tanggal_upload')
    
    context = {
        'semua_publikasi': semua_publikasi,
        'berita': semua_publikasi.filter(kategori='BERITA'),
        'pengumuman': semua_publikasi.filter(kategori='PENGUMUMAN'),
        'kegiatan': semua_publikasi.filter(kategori='KEGIATAN'),
    }
    return render(request, 'portal_publik/list_publikasi.html', context)

# 3 - Edit Publikasi
@login_required(login_url='auth:login')
@user_passes_test(is_admin_bpkad)
def edit_publikasi_view(request, pk):
    publikasi = get_object_or_404(PublikasiInstansi, pk=pk)
    
    if request.method == 'POST':
        try:
            publikasi.judul = request.POST.get('judul')
            publikasi.kategori = request.POST.get('kategori')
            publikasi.isi_konten = request.POST.get('isi_konten')
            
            # Jika user mengunggah gambar baru, timpa gambar lama
            if request.FILES.get('gambar_utama'):
                publikasi.gambar_utama = request.FILES.get('gambar_utama')
                
            publikasi.save()
            
            # Perekaman Audit Log
            catat_aktivitas(request.user, "Mengedit Publikasi", publikasi.judul, request)
            
            messages.success(request, f"Publikasi '{publikasi.judul}' berhasil diperbarui!")
            return redirect('tanah:list_publikasi')
            
        except Exception as e:
            messages.error(request, f"Gagal memperbarui data: {str(e)}")
            
    return render(request, 'portal_publik/input_publikasi.html', {'publikasi': publikasi})


# 4 - Delete Publikasi
@login_required(login_url='auth:login')
@user_passes_test(is_admin_bpkad)
def delete_publikasi_view(request, pk):
    publikasi = get_object_or_404(PublikasiInstansi, pk=pk)
    judul_terhapus = publikasi.judul
    
    publikasi.delete()
    
    # Perekaman Audit Log
    catat_aktivitas(request.user, "Menghapus Publikasi", judul_terhapus, request)
    
    messages.success(request, "Publikasi berhasil dihapus.")
    return redirect('publik:list_publikasi')


# - - - - - -
# -- COOMING SOON --
# - - - - - -

def coming_soon_view(request):
    # Ini yang akan dipanggil saat redirect('coming_soon_kendaraan') dieksekusi
    return render(request, 'portal_publik/coming_soon.html', {'title': 'Aset Kendaraan'})

def list_aset_kendaraan(request):
    # Redirect ini sekarang akan menemukan jalan pulang ke path di atas
    return redirect('publik:coming_soon_kendaraan')


# - - - - - -
# BANTUAN 
# - - - - - - 

def bantuan_view(request):
    return render(request, 'portal_publik/bantuan.html')

# data aset
def data_aset_publik_view(request):
    # Ambil data aset yang sudah valid saja
    semua_aset = AsetTanah.objects.filter(status_verifikasi='VALID').order_by('-created_at')
    
    context = {
        'semua_aset': semua_aset,
    }
    return render(request, 'portal_publik/data_aset.html', context)