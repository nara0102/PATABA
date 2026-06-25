import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q
from django.contrib.auth.decorators import login_required, user_passes_test

# 1. Impor Model Milik Aset Tanah Sendiri
from .models import AsetTanah, RefKelurahan, RefKecamatan, SertifikatTanah, MasterOPD

# 2. Impor Hak Akses & Perekam Jejak dari Manajemen Pengguna
from apps.manajemen_pengguna.views import role_required, is_admin_bpkad, is_operator, catat_aktivitas
from apps.manajemen_pengguna.utils import get_user_profile

from pataba_core.constants import ROLE_OPERATOR, ROLE_ADMIN, STATUS_PENDING


    
    
# - - - - -
# CRUD TANAH
# - - - - -

# 1 - Fungsi Input Aset Tanah Baru (SOP VALIDASI KETAT & PING-PONG)
@login_required(login_url='auth:login')
@role_required(allowed_roles=['ADMIN_BPKAD', 'OPERATOR_OPD'])
def input_aset_tanah(request):
    profile = request.user.profile
    role_user = profile.role.strip().upper()

    if request.method == 'POST':
        # a. TANGKAP DATA PENGIRIM & LOGIKA PING-PONG (Berdasarkan SOP SKILL.MD)
        if role_user == 'OPERATOR_OPD':
            target_opd = profile.opd
            target_status = 'BELUM_DIVERIFIKASI'
            catatan_revisi = ''  # SOP: Otomatis kosongkan catatan revisi saat OPD resubmit!
        else:
            opd_id = request.POST.get('opd')
            target_opd = MasterOPD.objects.get(pk=opd_id) if opd_id else None
            target_status = request.POST.get('status_verifikasi') or 'VALID'
            catatan_revisi = request.POST.get('catatan_revisi', '')

        # b. PEMBERSIH ANGKA RELASI & WILAYAH
        kec_id = request.POST.get('kecamatan')
        kel_id = request.POST.get('kelurahan')
        kec = RefKecamatan.objects.get(pk=kec_id) if kec_id else None
        kel = RefKelurahan.objects.get(pk=kel_id) if kel_id else None
        
        luas_raw = request.POST.get('luas_m2') or '0'
        luas_bersih = luas_raw.replace('.', '').replace(',', '.') 
        
        nilai_raw = request.POST.get('nilai_aset') or '0'
        nilai_bersih = nilai_raw.replace('.', '') 

        # c. PENYESUAIAN FIELD SERTIFIKAT (Menghindari Bentrok JS vs Python)
        status_sertifikasi = request.POST.get('status_sertifikasi') or 'BELUM_BERSERTIFIKAT'
        status_hak_sementara = request.POST.get('status_hak_sementara', '')
        
        if status_sertifikasi == 'BELUM_BERSERTIFIKAT':
            # Jika belum sertifikat, ambil nilai dari UI 'nomor_hak_sementara'
            # Jika kosong, isi dengan 'Dalam Proses' agar lolos validasi database
            ket_lainnya = request.POST.get('nomor_hak_sementara') or 'Dalam Proses Pembuatan'
        else:
            ket_lainnya = request.POST.get('keterangan_sertifikasi_lainnya', '')

        # d. INSTANCE LOKAL (Belum ter-save ke database)
        aset_baru = AsetTanah(
            opd=target_opd, 
            kelurahan=kel, 
            kecamatan_nama=kec.nama_kecamatan if kec else None, 
            kelurahan_nama=kel.nama_kelurahan if kel else None,
            nama_barang=request.POST.get('nama_barang'),
            kode_barang=request.POST.get('kode_barang'),
            nibar=request.POST.get('nibar'),
            nomor_register=request.POST.get('nomor_register'),
            status_kepemilikan=request.POST.get('status_kepemilikan') or 'BELUM_JELAS',
            luas_m2=luas_bersih,
            satuan='m2', 
            nilai_aset=nilai_bersih,
            cara_perolehan=request.POST.get('cara_perolehan'),
            tanggal_perolehan=request.POST.get('tanggal_perolehan') or None,
            alamat_lokasi=request.POST.get('alamat_lokasi'),
            latitude=float(request.POST.get('latitude') or 0),
            longitude=float(request.POST.get('longitude') or 0),
            
            status_sertifikasi=status_sertifikasi,
            nomor_sertifikat=request.POST.get('nomor_sertifikat'),
            status_hak_sementara=status_hak_sementara,
            keterangan_sertifikasi_lainnya=ket_lainnya, # Variabel aman dari bentrok JS
            
            kondisi_pemanfaatan=request.POST.get('kondisi_pemanfaatan'),
            status_penggunaan=request.POST.get('status_penggunaan'),
            spesifikasi_nama_barang=request.POST.get('spesifikasi_nama_barang'),
            spesifikasi_lainnya=request.POST.get('spesifikasi_lainnya'),
            keterangan=request.POST.get('keterangan'),
            
            status_verifikasi=target_status,
            catatan_revisi=catatan_revisi, # Masukkan variabel catatan revisi untuk Ping-Pong
            created_by_id=request.user.id
        )

        # e. VALIDASI ASET KETAT (Diperbarui)
        error_msgs = []
        if aset_baru.status_sertifikasi == 'BERSERTIFIKAT' and not aset_baru.nomor_sertifikat:
            error_msgs.append("Validasi Gagal: Nomor Sertifikat BPN wajib diisi karena status aset BERSERTIFIKAT.")
        elif aset_baru.status_sertifikasi == 'BELUM_BERSERTIFIKAT':
            if not aset_baru.status_hak_sementara:
                error_msgs.append("Validasi Gagal: Status Hak (Proses) wajib dipilih untuk aset Belum Bersertifikat (Pilih: Hak Pakai/Hak Milik).")
        
        # Validasi Khusus Logika Ping-Pong Admin BPKAD
        if role_user == 'ADMIN_BPKAD' and target_status == 'PERLU_REVIEW' and not catatan_revisi:
            error_msgs.append("Validasi Gagal: Karena Anda menolak usulan (Perlu Review), maka Catatan Revisi wajib diisi!")

        # Jika ada error, KEMBALIKAN KE TEMPLATE TANPA SAVE
        if error_msgs:
            for msg in error_msgs:
                messages.error(request, msg)
            return render(request, 'aset_tanah/input_aset_tanah.html', {
                'aset': aset_baru, 
                'opd_list': MasterOPD.objects.filter(is_active=1),
                'kecamatan_list': RefKecamatan.objects.all(),
                'kelurahan_list': RefKelurahan.objects.all(),
            })

        # f. SAVE KE DATABASE KALAU VALID
        try:
            aset_baru.save()
            
            # (Pastikan fungsi catat_aktivitas sudah ada di luar fungsi ini)
            try:
                if role_user == 'OPERATOR_OPD':
                    catat_aktivitas(request.user, "Mengusulkan Aset Baru", aset_baru.nama_barang, request)
                else:
                    catat_aktivitas(request.user, "Menambahkan Master Aset", aset_baru.nama_barang, request)
            except Exception:
                pass # Abaikan jika catat_aktivitas belum terdefinisi sempurna
                
            if role_user == 'OPERATOR_OPD':
                messages.success(request, f"Usulan aset '{aset_baru.nama_barang}' berhasil dikirim dan menunggu verifikasi BPKAD.")
            else:
                if target_status == 'PERLU_REVIEW':
                    messages.warning(request, f"Usulan aset dikembalikan ke OPD untuk direvisi.")
                else:
                    messages.success(request, f"Aset '{aset_baru.nama_barang}' berhasil divalidasi dan ditambahkan ke master data publik.")
            return redirect('tanah:list_aset_tanah') # Pastikan namespace redirect sesuai
            
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan database: {e}")
            return render(request, 'aset_tanah/input_aset_tanah.html', {
                'aset': aset_baru, 
                'opd_list': MasterOPD.objects.filter(is_active=1), 
                'kecamatan_list': RefKecamatan.objects.all(), 
                'kelurahan_list': RefKelurahan.objects.all()
            })

    # Saat GET (Membuka Form Kosong)
    return render(request, 'aset_tanah/input_aset_tanah.html', {
        'opd_list': MasterOPD.objects.filter(is_active=1),
        'kecamatan_list': RefKecamatan.objects.all(),
        'kelurahan_list': RefKelurahan.objects.all(),
    })

# 2 - Daftar Aset Tanah
@login_required(login_url='auth:login')
def list_aset_tanah(request):
    profile = request.user.profile
    role_user = profile.role.strip().upper()
    
    # a pembatsan hak akses
    if role_user == 'OPERATOR_OPD':
        queryset_dasar = AsetTanah.objects.filter(opd=profile.opd)
    else:
        queryset_dasar = AsetTanah.objects.all()

    # b logika filter
    opd_id = request.GET.get('opd')
    kecamatan_id = request.GET.get('kecamatan')
    kelurahan_id = request.GET.get('kelurahan')
    status_verifikasi = request.GET.get('status_verifikasi')
    
    # Logika Filter Sertifikat Bertingkat
    status_sertifikasi = request.GET.get('status_sertifikasi')
    kriteria_sertifikat = request.GET.get('kriteria_sertifikat') # Untuk Asli/Fotokopi Pemkot/Non-Pemkot
    
    kondisi_pemanfaatan = request.GET.get('kondisi_pemanfaatan')
    status_kepemilikan = request.GET.get('status_kepemilikan')
    cara_perolehan = request.GET.get('cara_perolehan')
    koordinat = request.GET.get('koordinat')

    # Terapkan filter lanjutan ke 'queryset_dasar'
    if opd_id: queryset_dasar = queryset_dasar.filter(opd_id=opd_id)
    if kecamatan_id: queryset_dasar = queryset_dasar.filter(kelurahan__kecamatan_id=kecamatan_id)
    if kelurahan_id: queryset_dasar = queryset_dasar.filter(kelurahan_id=kelurahan_id)
    if status_verifikasi: queryset_dasar = queryset_dasar.filter(status_verifikasi=status_verifikasi)
    if status_sertifikasi: queryset_dasar = queryset_dasar.filter(status_sertifikasi=status_sertifikasi)
    
    # Menangkap sub-filter dari status "LAINNYA"
    if kriteria_sertifikat: 
        queryset_dasar = queryset_dasar.filter(keterangan_sertifikasi_lainnya=kriteria_sertifikat)
        
    if kondisi_pemanfaatan: queryset_dasar = queryset_dasar.filter(kondisi_pemanfaatan=kondisi_pemanfaatan)
    if status_kepemilikan: queryset_dasar = queryset_dasar.filter(status_kepemilikan=status_kepemilikan)
    if cara_perolehan: queryset_dasar = queryset_dasar.filter(cara_perolehan=cara_perolehan)
        
    if koordinat == 'ada':
        queryset_dasar = queryset_dasar.exclude(latitude=0).exclude(latitude__isnull=True)
    elif koordinat == 'belum':
        queryset_dasar = queryset_dasar.filter(Q(latitude=0) | Q(latitude__isnull=True))

   # statistik
    queryset_valid = queryset_dasar.filter(status_verifikasi='VALID')
    
    total = queryset_valid.count()
    agregasi = queryset_valid.aggregate(total_luas=Sum('luas_m2'), total_nilai=Sum('nilai_aset'))
    
    total_luas = agregasi['total_luas'] or 0
    total_nilai = f"{agregasi['total_nilai'] or 0:,.0f}".replace(',', '.')
    
    bersertifikat = queryset_valid.filter(status_sertifikasi='BERSERTIFIKAT').count()
    belum_sertifikat = queryset_valid.filter(status_sertifikasi='BELUM_BERSERTIFIKAT').count()
    sertifikat_lainnya = queryset_valid.filter(status_sertifikasi='LAINNYA').count()
    persen_bersertifikat = (bersertifikat / total * 100) if total > 0 else 0
    
    ada_koordinat = queryset_valid.exclude(latitude=0).exclude(latitude__isnull=True).count()
    tanpa_koordinat = total - ada_koordinat
    
    # Antrean & Bermasalah tetap menghitung dari keseluruhan (bukan cuma yang valid)
    belum_verif = queryset_dasar.filter(status_verifikasi='BELUM_DIVERIFIKASI').count()
    bermasalah = queryset_dasar.filter(kondisi_pemanfaatan='SENGKETA').count()

    # pencarian kata kunci
    q = request.GET.get('q')
    semua_aset = queryset_dasar 
    
    if q:
        # Menghapus nama_lokasi_peruntukan yang sudah tiada agar tidak error
        semua_aset = semua_aset.filter(
            Q(opd__nama_opd__icontains=q) |
            Q(nama_barang__icontains=q) |
            Q(kode_barang__icontains=q) |
            Q(nibar__icontains=q) |
            Q(nomor_register__icontains=q) |
            Q(nomor_sertifikat__icontains=q) |
            Q(alamat_lokasi__icontains=q) |
            Q(kecamatan_nama__icontains=q) |
            Q(kelurahan_nama__icontains=q)
        )

    # Pengurutan data untuk tabel
    semua_aset = semua_aset.order_by('-created_at')
    
    # paginator
    paginator = Paginator(semua_aset, 10) # Angka 7 menentukan jumlah baris!
    page_number = request.GET.get('page')
    aset_page = paginator.get_page(page_number)

    # e kirim data ke template
    context = {
        'jenis_aset': 'Tanah',
        'semua_aset': aset_page, 
        'total_aset': total,
        'total_luas': total_luas,
        'total_nilai': total_nilai,
        'aset_bersertifikat': bersertifikat,
        'aset_belum_sertifikat': belum_sertifikat,
        'aset_sertifikat_lainnya': sertifikat_lainnya,
        'persen_bersertifikat': persen_bersertifikat,
        'aset_ada_koordinat': ada_koordinat,
        'aset_tanpa_koordinat': tanpa_koordinat,
        'aset_belum_verif': belum_verif,
        'aset_bermasalah': bermasalah,
        
        'opd_list': MasterOPD.objects.filter(is_active=1),
        'kecamatan_list': RefKecamatan.objects.all(),
        'kelurahan_list': RefKelurahan.objects.all(),
    }
    
    return render(request, 'aset_tanah/list_aset_tanah.html', context)


@login_required(login_url='auth:login')
@role_required(allowed_roles=['ADMIN_BPKAD', 'OPERATOR_OPD'])
def edit_aset_tanah(request, pk):
    aset = get_object_or_404(AsetTanah, pk=pk)
    profile = request.user.profile
    role_user = profile.role.strip().upper()

    if role_user == 'OPERATOR_OPD' and aset.opd != profile.opd:
        messages.error(request, "Akses Ditolak: Anda tidak dapat mengubah data aset milik instansi lain.")
        return redirect('auth:dashboard_opd')

    if request.method == 'POST':
        # --- 1. LOGIKA TIKET PING-PONG (STATUS OTOMATIS) ---
        if role_user == 'OPERATOR_OPD':
            target_opd = profile.opd
            target_status = 'BELUM_DIVERIFIKASI' # OPD Submit = Reset ke Antrean BPKAD
        else:
            opd_id = request.POST.get('opd')
            target_opd = MasterOPD.objects.get(pk=opd_id) if opd_id else aset.opd
            target_status = request.POST.get('status_verifikasi') or aset.status_verifikasi

        # --- 2. UPDATE INSTANCE LOKAL (MENIMPA DATA SEMENTARA) ---
        kec_id = request.POST.get('kecamatan')
        kel_id = request.POST.get('kelurahan')
        kec = RefKecamatan.objects.get(pk=kec_id) if kec_id else aset.kelurahan.kecamatan
        kel = RefKelurahan.objects.get(pk=kel_id) if kel_id else aset.kelurahan
        
        aset.opd = target_opd
        aset.kelurahan = kel
        aset.kecamatan_nama = kec.nama_kecamatan
        aset.kelurahan_nama = kel.nama_kelurahan
        aset.nama_barang = request.POST.get('nama_barang')
        aset.kode_barang = request.POST.get('kode_barang')
        aset.nibar = request.POST.get('nibar')
        aset.nomor_register = request.POST.get('nomor_register')
        aset.status_kepemilikan = request.POST.get('status_kepemilikan') or 'BELUM_JELAS'
        
        luas_raw = request.POST.get('luas_m2') or '0'
        aset.luas_m2 = luas_raw.replace('.', '').replace(',', '.') 
        nilai_raw = request.POST.get('nilai_aset') or '0'
        aset.nilai_aset = nilai_raw.replace('.', '') 
        
        aset.cara_perolehan = request.POST.get('cara_perolehan')
        tanggal_perolehan = request.POST.get('tanggal_perolehan')
        if tanggal_perolehan: aset.tanggal_perolehan = tanggal_perolehan
        
        aset.alamat_lokasi = request.POST.get('alamat_lokasi')
        aset.latitude = float(request.POST.get('latitude') or 0)
        aset.longitude = float(request.POST.get('longitude') or 0)
        
        # --- PENYESUAIAN LOGIKA SERTIFIKAT (SINKRON DENGAN FUNGSI INPUT) ---
        status_sertif = request.POST.get('status_sertifikasi') or 'BELUM_BERSERTIFIKAT'
        aset.status_sertifikasi = status_sertif
        aset.nomor_sertifikat = request.POST.get('nomor_sertifikat')
        aset.status_hak_sementara = request.POST.get('status_hak_sementara', '')
        
        if status_sertif == 'BELUM_BERSERTIFIKAT':
            # Ambil dari kotak Nomor Hak (HTML), kalau kosong otomatis isi default
            aset.keterangan_sertifikasi_lainnya = request.POST.get('nomor_hak_sementara') or 'Dalam Proses Pembuatan'
        else:
            aset.keterangan_sertifikasi_lainnya = request.POST.get('keterangan_sertifikasi_lainnya', '')
        
        aset.kondisi_pemanfaatan = request.POST.get('kondisi_pemanfaatan')
        aset.status_penggunaan = request.POST.get('status_penggunaan')
        aset.spesifikasi_nama_barang = request.POST.get('spesifikasi_nama_barang')
        aset.spesifikasi_lainnya = request.POST.get('spesifikasi_lainnya')
        aset.keterangan = request.POST.get('keterangan')
        
        # LOGIKA CATATAN REVISI PING-PONG
        aset.status_verifikasi = target_status
        if role_user == 'ADMIN_BPKAD' or request.user.is_superuser:
            if target_status == 'PERLU_REVIEW':
                aset.catatan_revisi = request.POST.get('catatan_revisi')
            else:
                aset.catatan_revisi = "" 
        else:
            aset.catatan_revisi = "" # OPD Submit = Hapus catatan merah BPKAD

        # --- 3. GERBANG VALIDASI KEAMANAN & SOP PING-PONG ---
        error_msgs = []
        if aset.status_sertifikasi == 'BERSERTIFIKAT' and not aset.nomor_sertifikat:
            error_msgs.append("Validasi Gagal: Nomor Sertifikat BPN wajib diisi karena status aset BERSERTIFIKAT.")
        elif aset.status_sertifikasi == 'BELUM_BERSERTIFIKAT':
            if not aset.status_hak_sementara:
                error_msgs.append("Validasi Gagal: Status Hak (Proses) wajib dipilih untuk aset Belum Bersertifikat (Pilih: Hak Pakai/Hak Milik).")

        # Validasi Khusus Admin (Dilarang menolak tanpa alasan!)
        if role_user == 'ADMIN_BPKAD' and target_status == 'PERLU_REVIEW':
            if not aset.catatan_revisi or aset.catatan_revisi.strip() == '':
                error_msgs.append("SOP BPKAD: Catatan revisi WAJIB diisi jika usulan dikembalikan ke OPD (PERLU REVIEW).")

        # Jika ada error, KEMBALIKAN KE TEMPLATE TANPA MENIMPA DATABASE
        if error_msgs:
            for msg in error_msgs:
                messages.error(request, msg)
            return render(request, 'aset_tanah/input_aset_tanah.html', {
                'aset': aset, 
                'opd_list': MasterOPD.objects.filter(is_active=1),
                'kecamatan_list': RefKecamatan.objects.all(),
                'kelurahan_list': RefKelurahan.objects.all(), # Ditambahkan agar dropdown kelurahan tidak error
            })

        # --- 4. EKSEKUSI SAVE DATABASE JIKA LOLOS VALIDASI ---
        try:
            aset.save()
            
            try:
                if role_user == 'ADMIN_BPKAD' or request.user.is_superuser:
                    if target_status == 'PERLU_REVIEW':
                        catat_aktivitas(request.user, "Menolak/Revisi Usulan Aset", aset.nama_barang, request)
                        messages.warning(request, f"Aset {aset.nama_barang} dikembalikan ke OPD untuk direvisi.")
                    elif target_status == 'VALID':
                        catat_aktivitas(request.user, "Memvalidasi Aset", aset.nama_barang, request)
                        messages.success(request, f"Aset {aset.nama_barang} berhasil diperbarui & diverifikasi.")
                    else:
                        catat_aktivitas(request.user, "Mengedit Data Aset", aset.nama_barang, request)
                        messages.success(request, f"Aset {aset.nama_barang} berhasil diperbarui.")
                else:
                    catat_aktivitas(request.user, "Mengirim Ulang Revisi Aset", aset.nama_barang, request)
                    messages.success(request, f"Usulan revisi aset {aset.nama_barang} berhasil dikirim ulang ke BPKAD.")
            except Exception:
                pass
                
            return redirect('tanah:list_aset_tanah') 
        except Exception as e:
            messages.error(request, f"Gagal memperbarui aset: {e}")
            return render(request, 'aset_tanah/input_aset_tanah.html', {
                'aset': aset, 
                'opd_list': MasterOPD.objects.filter(is_active=1), 
                'kecamatan_list': RefKecamatan.objects.all(),
                'kelurahan_list': RefKelurahan.objects.all()
            })
    
    # Menampilkan Form Awal (Method GET)
    return render(request, 'aset_tanah/input_aset_tanah.html', {
        'aset': aset, 
        'opd_list': MasterOPD.objects.filter(is_active=1),
        'kecamatan_list': RefKecamatan.objects.all(),
        'kelurahan_list': RefKelurahan.objects.all(), # Ditambahkan agar kelurahan ter-load saat buka form
    })

# b. detail
def detail_aset_tanah(request, pk):
    aset = get_object_or_404(AsetTanah, pk=pk)
    return render(request, 'aset_tanah/detail_aset_tanah.html', {
        'aset': aset,
        'profile': get_user_profile(request.user)
    })

# c. delete
@login_required(login_url='auth:login')
@role_required(allowed_roles=['ADMIN_BPKAD'])
def delete_aset_tanah(request, pk):
    aset = get_object_or_404(AsetTanah, pk=pk)
    nama_aset_terhapus = aset.nama_barang
    aset.delete()
    catat_aktivitas(request.user, "Menghapus Data Aset", nama_aset_terhapus, request)
    messages.success(request, "Aset berhasil dihapus.")
    return redirect('aset_tanah:list_aset_tanah')


# - - - - -
# SERTIFIKASI TANAH
# - - - - -

# 1 - Tambah Sertifikat
@login_required(login_url='auth:login')
@role_required(allowed_roles=['ADMIN_BPKAD'])
def tambah_sertifikat(request, aset_id):
    aset = get_object_or_404(AsetTanah, pk=aset_id)
    
    if request.method == 'POST':
        # --- 1. PEMBERSIH ANGKA & RELASI OPD ---
        luas_raw = request.POST.get('luas') or '0'
        luas_bersih = luas_raw.replace('.', '').replace(',', '.') 
        
        nilai_raw = request.POST.get('nilai') or '0'
        nilai_bersih = nilai_raw.replace('.', '') 

        opd_id = request.POST.get('opd')
        target_opd = MasterOPD.objects.get(pk=opd_id) if opd_id else None

        # --- 2. BUAT INSTANCE LOKAL (BELUM DISAVE) ---
        sertifikat_baru = SertifikatTanah(
            aset_tanah=aset,
            opd=target_opd,
            nomor_sertifikat=request.POST.get('nomor_sertifikat'),
            nama_pemegang_hak=request.POST.get('nama_pemegang_hak') or 'Pemerintah Kota Palu',
            alamat=request.POST.get('alamat'),
            peruntukan=request.POST.get('peruntukan'),
            status_hak=request.POST.get('status_hak'),
            luas=luas_bersih,
            tanggal_pembuatan_input = request.POST.get('tanggal_pembuatan') or None,
            tahun_terbit=request.POST.get('tahun_terbit') or None,
            nilai=nilai_bersih,
            pemetaan_bpn=request.POST.get('pemetaan_bpn'),
            keterangan=request.POST.get('keterangan'),
            catatan=request.POST.get('catatan')
        )

        # --- 3. GERBANG VALIDASI KEAMANAN (SOP) ---
        error_msgs = []
        if not sertifikat_baru.status_hak:
            error_msgs.append("Validasi Gagal: Status Hak Sertifikat wajib dipilih.")
        if not sertifikat_baru.nomor_sertifikat:
            error_msgs.append("Validasi Gagal: Nomor Sertifikat wajib diisi.")
        if not request.POST.get('nama_pemegang_hak'):
            error_msgs.append("Validasi Gagal: Nama Pemegang Hak wajib diisi (Sistem mendeteksi kekosongan).")
        if not sertifikat_baru.keterangan:
            error_msgs.append("Validasi Gagal: Bukti Fisik Sertifikat (Asli / Fotokopi) wajib dipilih.")

        # Jika ada error, KEMBALIKAN KE TEMPLATE TANPA SAVE (Isian tidak akan hilang)
        if error_msgs:
            for msg in error_msgs:
                messages.error(request, msg)
            return render(request, 'aset_tanah/input_sertifikat.html', {
                'sertifikat': sertifikat_baru, 
                'aset': aset, 
                'opd_list': MasterOPD.objects.filter(is_active=1)
            })

        # --- 4. EKSEKUSI SAVE DATABASE & SINKRONISASI ASET ---
        # --- 4. EKSEKUSI SAVE DATABASE & SINKRONISASI ASET ---
        try:
            sertifikat_baru.save()
            
            # Otomatis ubah status aset master menjadi BERSERTIFIKAT
            aset.status_sertifikasi = 'BERSERTIFIKAT'
            aset.nomor_sertifikat = sertifikat_baru.nomor_sertifikat
            
            # Menyiapkan keterangan turunan untuk master aset
            kriteria_fisik = "ASLI" if sertifikat_baru.keterangan == 'ASLI' else "FOTOKOPI"
            kriteria_pemilik = "PEMKOT" if sertifikat_baru.nama_pemegang_hak == 'Pemerintah Kota Palu' else "NON_PEMKOT"
            aset.keterangan_sertifikasi_lainnya = f"{kriteria_fisik}_{kriteria_pemilik}"
            
            aset.save()

            # --- PEREKAMAN LOG AKTIVITAS ---
            catat_aktivitas(request.user, "Menerbitkan Sertifikat", f"{sertifikat_baru.nomor_sertifikat} ({aset.nama_barang})", request)

            messages.success(request, f"Sertifikat {sertifikat_baru.nomor_sertifikat} berhasil diterbitkan & disinkronkan ke Master Aset.")
            return redirect('tanah:detail_aset_tanah', pk=aset_id)
            
        except Exception as e:
            messages.error(request, f"Gagal menyimpan sertifikat: {e}")
            return render(request, 'aset_tanah/input_sertifikat.html', {'sertifikat': sertifikat_baru, 'aset': aset, 'opd_list': MasterOPD.objects.filter(is_active=1)})
    # Saat GET
    return render(request, 'aset_tanah/input_sertifikat.html', {'aset': aset, 'opd_list': MasterOPD.objects.filter(is_active=1)})


# 2 - Edit Sertifikat
@login_required(login_url='auth:login')
@role_required(allowed_roles=['ADMIN_BPKAD'])
def edit_sertifikat(request, sertifikat_id):
    sertifikat = get_object_or_404(SertifikatTanah, pk=sertifikat_id)
    aset = sertifikat.aset_tanah
    
    if request.method == 'POST':
        # --- 1. UPDATE INSTANCE LOKAL ---
        luas_raw = request.POST.get('luas') or '0'
        sertifikat.luas = luas_raw.replace('.', '').replace(',', '.')
        
        nilai_raw = request.POST.get('nilai') or '0'
        sertifikat.nilai = nilai_raw.replace('.', '')

        opd_id = request.POST.get('opd')
        sertifikat.opd = MasterOPD.objects.get(pk=opd_id) if opd_id else None
        
        sertifikat.nomor_sertifikat = request.POST.get('nomor_sertifikat')
        sertifikat.nama_pemegang_hak = request.POST.get('nama_pemegang_hak') or 'Pemerintah Kota Palu'
        sertifikat.alamat = request.POST.get('alamat')
        sertifikat.peruntukan = request.POST.get('peruntukan')
        sertifikat.status_hak = request.POST.get('status_hak')
        sertifikat.tanggal_pembuatan = request.POST.get('tanggal_pembuatan') or None
        sertifikat.tahun_terbit = request.POST.get('tahun_terbit') or None
        sertifikat.pemetaan_bpn = request.POST.get('pemetaan_bpn')
        sertifikat.keterangan = request.POST.get('keterangan')
        sertifikat.catatan = request.POST.get('catatan')

        # --- 2. GERBANG VALIDASI ---
        error_msgs = []
        if not sertifikat.status_hak: error_msgs.append("Status Hak Sertifikat wajib dipilih.")
        if not sertifikat.nomor_sertifikat: error_msgs.append("Nomor Sertifikat wajib diisi.")
        if not request.POST.get('nama_pemegang_hak'): error_msgs.append("Nama Pemegang Hak wajib diisi.")
        if not sertifikat.keterangan: error_msgs.append("Bukti Fisik Sertifikat wajib dipilih.")

        if error_msgs:
            for msg in error_msgs:
                messages.error(request, msg)
            return render(request, 'aset_tanah/input_sertifikat.html', {'sertifikat': sertifikat, 'aset': aset, 'opd_list': MasterOPD.objects.filter(is_active=1)})
            
        # --- 3. EKSEKUSI SAVE ---
        # --- 3. EKSEKUSI SAVE ---
        try:
            sertifikat.save()
            
            # Sinkronisasi nomor sertifikat ke aset tanah jika berubah
            if aset.nomor_sertifikat != sertifikat.nomor_sertifikat:
                aset.nomor_sertifikat = sertifikat.nomor_sertifikat
                aset.save()

            # --- PEREKAMAN LOG AKTIVITAS ---
            catat_aktivitas(request.user, "Mengedit Data Sertifikat", f"{sertifikat.nomor_sertifikat} ({aset.nama_barang})", request)

            messages.success(request, "Data sertifikat berhasil diperbarui.")
            return redirect('tanah:detail_aset_tanah', pk=aset.id)
            
        except Exception as e:
            messages.error(request, f"Gagal memperbarui sertifikat: {e}")
            return render(request, 'aset_tanah/input_sertifikat.html', {'sertifikat': sertifikat, 'aset': aset, 'opd_list': MasterOPD.objects.filter(is_active=1)})
        
    # Saat GET
    return render(request, 'aset_tanah/input_sertifikat.html', {'sertifikat': sertifikat, 'aset': aset, 'opd_list': MasterOPD.objects.filter(is_active=1)})

# 3 - Hapus Sertifikat
@login_required(login_url='auth:login')
@role_required(allowed_roles=['ADMIN_BPKAD'])
def delete_sertifikat(request, sertifikat_id):
    sertifikat = get_object_or_404(SertifikatTanah, pk=sertifikat_id)
    aset = sertifikat.aset_tanah
    
    # Simpan nomor sertifikat dan nama aset ke variabel sementara
    nomor_sertifikat_terhapus = sertifikat.nomor_sertifikat
    nama_aset_terkait = aset.nama_barang
    
    sertifikat.delete()
    
    # --- PEREKAMAN LOG AKTIVITAS ---
    catat_aktivitas(request.user, "Menghapus Sertifikat", f"{nomor_sertifikat_terhapus} ({nama_aset_terkait})", request)
    
    messages.success(request, "Sertifikat berhasil dihapus.")
    
    # Kembalikan user ke halaman list sertifikat atau detail aset
    return redirect('tanah:list_sertifikat')


# 3 - list sertifikat 
@login_required(login_url='auth:login')
@role_required(allowed_roles=['ADMIN_BPKAD'])
def list_sertifikat(request):
    # ==========================================
    # 1. PERHITUNGAN STATISTIK (DASHBOARD ATAS)
    # ==========================================
    # HANYA mengambil data Aset Tanah yang VALID untuk dasar statistik
    semua_aset = AsetTanah.objects.filter(status_verifikasi='VALID')
    
    total_aset = semua_aset.count()
    luas_aset = semua_aset.aggregate(Sum('luas_m2'))['luas_m2__sum'] or 0
    nilai_aset = semua_aset.aggregate(Sum('nilai_aset'))['nilai_aset__sum'] or 0

    # Statistik Aset yang SUDAH Bersertifikat (Diambil dari yang VALID)
    aset_sertifikat = semua_aset.filter(status_sertifikasi='BERSERTIFIKAT')
    total_sertifikat = aset_sertifikat.count()
    luas_sertifikat = aset_sertifikat.aggregate(Sum('luas_m2'))['luas_m2__sum'] or 0
    nilai_sertifikat = aset_sertifikat.aggregate(Sum('nilai_aset'))['nilai_aset__sum'] or 0

    # Statistik Aset yang BELUM Bersertifikat / Lainnya
    aset_belum = semua_aset.exclude(status_sertifikasi='BERSERTIFIKAT')
    total_belum = aset_belum.count()
    luas_belum = aset_belum.aggregate(Sum('luas_m2'))['luas_m2__sum'] or 0
    nilai_belum = aset_belum.aggregate(Sum('nilai_aset'))['nilai_aset__sum'] or 0

    # Perhitungan Persentase Progres
    persen_sertifikat = (total_sertifikat / total_aset * 100) if total_aset > 0 else 0
    persen_belum = (total_belum / total_aset * 100) if total_aset > 0 else 0


    # ==========================================
    # 2. QUERY TABEL & LOGIKA FILTER
    # ==========================================
    # Mengambil data sertifikat dan menarik data relasi (OPD dan Aset) sekaligus
    sertifikat_list = SertifikatTanah.objects.select_related('opd', 'aset_tanah').order_by('-created_at')
    
    # A. Filter Pencarian Universal (Search Box)
    # Sekarang bisa mencari Nomor Sertifikat, Nama Aset, NIBAR, atau Nama OPD!
    q = request.GET.get('q')
    if q:
        sertifikat_list = sertifikat_list.filter(
            Q(nomor_sertifikat__icontains=q) |
            Q(aset_tanah__nama_barang__icontains=q) |
            Q(aset_tanah__nibar__icontains=q) |
            Q(opd__nama_opd__icontains=q)
        )
        
    # B. Filter Bukti Fisik (Asli / Fotokopi)
    keterangan = request.GET.get('keterangan')
    if keterangan:
        sertifikat_list = sertifikat_list.filter(keterangan=keterangan)
        
    # C. Filter Kategori Pemegang Hak (Pemkot / Lainnya)
    # Karena di database tersimpan string asli, kita gunakan pengecekan string
    pemegang_hak = request.GET.get('pemegang_hak')
    if pemegang_hak == 'PEMKOT':
        sertifikat_list = sertifikat_list.filter(nama_pemegang_hak__iexact='Pemerintah Kota Palu')
    elif pemegang_hak == 'LAINNYA':
        sertifikat_list = sertifikat_list.exclude(nama_pemegang_hak__iexact='Pemerintah Kota Palu')

    # D. Filter Status Hak (Hak Pakai / Hak Milik)
    status_hak = request.GET.get('status_hak')
    if status_hak:
        sertifikat_list = sertifikat_list.filter(status_hak=status_hak)


    # ==========================================
    # 3. KIRIM DATA KE TEMPLATE
    # ==========================================
    context = {
        # Mengisi 4 Kotak Dashboard
        'total_aset': total_aset,
        'luas_aset': luas_aset,
        'nilai_aset': nilai_aset,
        
        'total_sertifikat': total_sertifikat,
        'luas_sertifikat': luas_sertifikat,
        'nilai_sertifikat': nilai_sertifikat,
        
        'total_belum': total_belum,
        'luas_belum': luas_belum,
        'nilai_belum': nilai_belum,
        
        'persen_sertifikat': persen_sertifikat,
        'persen_belum': persen_belum,
        
        # Mengisi Tabel List Sertifikat (Perhatikan nama variabelnya)
        'semua_sertifikat': sertifikat_list,
    }
    return render(request, 'aset_tanah/list_sertifikat.html', context)


    

# - - - - - -
# API 
# - - - - - -

# 1 -Dropdown Dinamis Kelurahan
@login_required(login_url='auth:login')
def get_kelurahan_by_kecamatan(request):
    kecamatan_id = request.GET.get('kecamatan_id')
    if kecamatan_id:
        # Ambil kelurahan yang kecamatannya sesuai
        kelurahan = RefKelurahan.objects.filter(kecamatan_id=kecamatan_id).values('id', 'nama_kelurahan')
        return JsonResponse(list(kelurahan), safe=False)
    return JsonResponse([], safe=False)




# def list_aset_kendaraan(request):
#     # Logika Stats untuk Kendaraan
#     asets = AsetKendaraan.objects.all() # Pastikan model ini sudah ada
#     context = {
#         'jenis_aset': 'Kendaraan',
#         'semua_aset': asets,
#         'total_aset': asets.count(),
#         'bersertifikat': asets.filter(status_pajak='Aktif').count(), # Contoh field kendaraan
#         'sengketa': asets.filter(kondisi='Rusak Berat').count(),
#     }
#     return render(request, 'aset_tanah/daftar_aset_list.html', context)

# aset kendaraan sementara
def list_aset_kendaraan(request):
    # Secara cerdas melempar pengguna ke rute coming_soon yang ada di portal_publik
    return redirect('publik:coming_soon_kendaraan')



# - - - - -
# PEMBEBASAN LAHAN (GANTI RUGI)
# - - - - -

@login_required(login_url='auth:login')
@role_required(allowed_roles=['ADMIN_BPKAD'])
def list_pembebasan_lahan(request):
    """
    Fungsi sementara (Mockup) untuk halaman Pembebasan Lahan.
    Data ditarik dari HTML statis untuk bahan diskusi dengan Dinas.
    """
    return render(request, 'aset_tanah/pembebasan_lahan.html')

# ==========================================
# FITUR EXPORT EXCEL (MENGIKUTI FILTER UI)
# ==========================================
@login_required(login_url='auth:login')
def export_excel_aset(request):
    # 1. Siapkan File Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Laporan_Aset_Tanah_BPKAD.xlsx"'

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = 'Daftar Aset Tanah'

    # 2. Desain Header (Bisa kamu Edit/Tambah/Kurangi sesuai kebutuhan presentasi)
    headers = [
        'No', 'Instansi (OPD)', 'Kode Barang', 'Nama Barang', 'NIBAR', 'Nomor Register', 
        'Luas (m2)', 'Alamat Lokasi', 'Kecamatan', 'Titik Koordinat', 'Nilai Aset (Rp)', 
        'Status Sertifikasi', 'Nomor Sertifikat/Hak', 'Cara Perolehan', 'Tanggal Perolehan', 'Status Penggunaan'
    ]
    
    header_fill = PatternFill(start_color="0056B3", end_color="0056B3", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    
    for col_num, header_title in enumerate(headers, 1):
        cell = worksheet.cell(row=1, column=col_num, value=header_title)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # 3. TANGKAP PARAMETER FILTER DARI URL
    q = request.GET.get('q', '')
    opd_id = request.GET.get('opd', '')
    kecamatan_id = request.GET.get('kecamatan', '')
    status_sertif = request.GET.get('status_sertifikasi', '')

    # 4. TERAPKAN FILTER KE DATABASE (Sesuai SOP SKILL.MD: Hanya Data VALID)
    aset_data = AsetTanah.objects.filter(status_verifikasi='VALID')

    if q:
        aset_data = aset_data.filter(
            Q(nama_barang__icontains=q) | 
            Q(nibar__icontains=q) | 
            Q(alamat_lokasi__icontains=q)
        )
    if opd_id:
        aset_data = aset_data.filter(opd_id=opd_id)
    if kecamatan_id:
        aset_data = aset_data.filter(kelurahan__kecamatan_id=kecamatan_id)
    if status_sertif:
        aset_data = aset_data.filter(status_sertifikasi=status_sertif)

    aset_data = aset_data.order_by('-created_at')

    # 5. Masukkan Data ke Baris Excel
    for row_num, aset in enumerate(aset_data, 2): 
        
        koordinat = "-"
        if aset.latitude and aset.longitude:
            koordinat = f"{aset.latitude}, {aset.longitude}"
            
        tgl_perolehan = aset.tanggal_perolehan.strftime("%d-%m-%Y") if aset.tanggal_perolehan else "-"
        
        # Logika Keterangan Sertifikat
        nomor_sertif_tampil = aset.nomor_sertifikat if aset.nomor_sertifikat else aset.keterangan_sertifikasi_lainnya
        
        # Pastikan urutan ini sama persis dengan urutan 'headers' di atas!
        row_data = [
            row_num - 1,
            aset.opd.nama_opd if aset.opd else "-",
            aset.kode_barang or "-",
            aset.nama_barang or "-",
            aset.nibar or "-",
            aset.nomor_register or "-",
            aset.luas_m2 or 0,
            aset.alamat_lokasi or "-",
            aset.kecamatan_nama or "-",
            koordinat,
            aset.nilai_aset or 0,
            aset.get_status_sertifikasi_display() or "-",
            nomor_sertif_tampil or "-", 
            aset.cara_perolehan or "-",
            tgl_perolehan,
            aset.status_penggunaan or "-"
        ]
        
        for col_num, cell_value in enumerate(row_data, 1):
            worksheet.cell(row=row_num, column=col_num, value=cell_value)

    # 6. Sesuaikan Lebar Kolom
    for col in worksheet.columns:
        max_length = 0
        col_letter = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        worksheet.column_dimensions[col_letter].width = max_length + 2

    workbook.save(response)
    return response