from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q, Sum
from .forms import KontakForm
from django.core.paginator import Paginator

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

# 1 - Halaman Utama Publik 
def index_view(request):
    queryset_publik = AsetTanah.objects.filter(status_verifikasi='VALID')
    
    total_aset_tanah = queryset_publik.count()
    agregasi = queryset_publik.aggregate(
        total_luas_m2=Sum('luas_m2'),
        total_nilai_rp=Sum('nilai_aset')
    )
    
    luas_mentah = agregasi['total_luas_m2'] or 0
    nilai_mentah = agregasi['total_nilai_rp'] or 0
    total_luas_ha = luas_mentah / 10000                 # m2 dikonversi ke Hektare (Ha)
    total_nilai_miliar = nilai_mentah / 1000000000  # Rupiah dikonversi ke Miliar (M)
    
    # berita
    berita_semua = PublikasiInstansi.objects.filter(
        kategori__in=['BERITA', 'PENGUMUMAN'], 
        is_published=True
    ).order_by('-tanggal_upload')
    
    berita_utama = berita_semua.first() 
    list_berita = berita_semua[1:4]     

    # galeri
    galeri_semua = PublikasiInstansi.objects.filter(
        kategori='KEGIATAN', 
        is_published=True
    ).order_by('-tanggal_upload')
    
    galeri_utama = galeri_semua.first() 
    list_galeri = galeri_semua[1:3]     

    context = {
        'total_aset_tanah': total_aset_tanah,
        'total_luas_ha': total_luas_ha,                  
        'total_nilai_triliun': total_nilai_miliar,
        'berita_utama': berita_utama,
        'list_berita': list_berita,
        'galeri_utama': galeri_utama,
        'list_galeri': list_galeri,
    }
    return render(request, 'portal_publik/index.html', context)

# 2 - Halaman Peta Gis
def peta_gis_view(request):
    # 1. Tangkap parameter filter & pencarian (Mendukung deep-linking dari aset publik)
    query_cari = request.GET.get('q', '')
    opd_id = request.GET.get('opd', '')
    
    # 2. Base Queryset Utama (Mengunci mutlak status VALID sesuai aturan ping-pong data)
    queryset = AsetTanah.objects.filter(status_verifikasi='VALID').order_by('nama_barang')
    
    # 3. Eksekusi Pencarian Teks
    if query_cari:
        queryset = queryset.filter(nama_barang__icontains=query_cari) | queryset.filter(alamat_lokasi__icontains=query_cari)
        
    # 4. Eksekusi Filter OPD
    if opd_id:
        queryset = queryset.filter(opd_id=opd_id)
        
    # 5. Kumpulkan Daftar OPD Aktif secara aman tanpa tebak-tebakan path import model
    opd_list = []
    seen_opds = set()
    for aset in AsetTanah.objects.filter(status_verifikasi='VALID').select_related('opd'):
        if aset.opd and aset.opd.id not in seen_opds:
            opd_list.append(aset.opd)
            seen_opds.add(aset.opd.id)

    # 6. ANTISIPASI DATA RIBUAN: Batasi muatan maksimal 10 data per halaman di panel kiri
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page')
    semua_aset_paginated = paginator.get_page(page_number)
    
    context = {
        'semua_aset': semua_aset_paginated,
        'opd_list': opd_list,
        'query_cari': query_cari,
        'opd_id': opd_id,
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

# 4 - Halaman Berita
def berita_publik_view(request):
    # Ambil seluruh publikasi secara terpusat dan urutkan dari yang terbaru
    semua_publikasi = PublikasiInstansi.objects.all().order_by('-tanggal_upload')
    
    context = {
        # Saring berdasarkan kategori untuk dilempar ke template berita.html
        'berita_list': semua_publikasi.filter(kategori='BERITA'),
        'pengumuman_list': semua_publikasi.filter(kategori='PENGUMUMAN'),
        'kegiatan_list': semua_publikasi.filter(kategori='KEGIATAN'), # Opsional jika ingin dipakai nanti
    }
    return render(request, 'portal_publik/berita.html', context)

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

# 2 - List
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
# COOMING SOON
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


# - - - - -
# LAINNYA
# - - - - -

# 1 - TABEL Data Aset


def data_aset_publik_view(request):
    # Ambil semua aset yang sudah diverifikasi VALID oleh BPKAD
    aset_list = AsetTanah.objects.filter(status_verifikasi='VALID').order_by('nama_barang')
    
    # qr
    q = request.GET.get('q', '')
    id_dari_qr = request.GET.get('id', '')
    
    if id_dari_qr:
        # Jika QR Code di-scan, langsung kunci secara mutlak ke ID tersebut!
        aset_list = aset_list.filter(id=id_dari_qr)
    elif q:
        # Jika pengguna mengetik manual di kolom pencarian biasa
        aset_list = aset_list.filter(
            Q(nama_barang__icontains=q) | 
            Q(nibar__icontains=q) | 
            Q(alamat_lokasi__icontains=q)
        )
        
    # --- PROSES PAGINATOR DJANGO ---
    # Batasi muatan maksimal 10 baris per halaman sesuai request kamu
    paginator = Paginator(aset_list, 10) 
    page_number = request.GET.get('page')
    semua_aset_paginated = paginator.get_page(page_number)
        
    context = {
        'semua_aset': semua_aset_paginated,
        
        'aset_list': aset_list,
        'q': q,
        'id_terpilih': id_dari_qr
    }
    return render(request, 'portal_publik/data_aset.html', context)