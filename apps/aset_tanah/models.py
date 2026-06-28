from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from pataba_core.storages import AsetTanahStorage

User = get_user_model()

# Organisasi Perangkat Daerah
class MasterOPD(models.Model):
    id = models.BigAutoField(primary_key=True)
    nama_opd = models.CharField(unique=True, max_length=255)
    kode_opd = models.CharField(max_length=30, blank=True, null=True)
    kode_lokasi = models.CharField(max_length=30, blank=True, null=True)
    singkatan = models.CharField(max_length=20, blank=True, null=True)
    kategori_opd = models.CharField(max_length=11, blank=True, null=True)
    alamat_kantor = models.CharField(max_length=255, blank=True, null=True)
    kepala_opd = models.CharField(max_length=150, blank=True, null=True)
    email_resmi = models.EmailField(max_length=255, blank=True, null=True)
    is_active = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        managed = True
        db_table = 'master_opd'

    def __str__(self):
        return self.nama_opd


# Aset Tanah
class AsetTanah(models.Model):
    STATUS_SERTIFIKASI_CHOICES = [
        ('BERSERTIFIKAT', 'Bersertifikat'),
        ('BELUM_BERSERTIFIKAT', 'Belum Bersertifikat'),
    ]
    
    STATUS_KEPEMILIKAN_CHOICES = [
        ('BELUM_JELAS', 'Belum Jelas'),
        ('PEMDA', 'Pemda'),
        ('MASYARAKAT', 'Masyarakat'),
        ('PROVINSI', 'Provinsi'),
        ('PUSAT', 'Pusat'),
    ]

    CARA_PEROLEHAN_CHOICES = [
        ('HIBAH', 'Hibah'),
        ('PEMBELIAN', 'Pembelian'),
        ('PENYERAHAN', 'Penyerahan'),
        ('GANTI_RUGI', 'Ganti Rugi'),
    ]

    KONDISI_PEMANFAATAN_CHOICES = [
        ('TIDAK_DIKETAHUI', 'Tidak Diketahui'),
        ('DIMANFAATKAN', 'Dimanfaatkan'),
        ('TANAH_KOSONG', 'Tanah Kosong'),
        ('RUSAK', 'Rusak'),
        ('SENGKETA', 'Sengketa'),
    ]

    STATUS_HAK_SEMENTARA_CHOICES = [
        ('HAK_PAKAI', 'Hak Pakai'),
        ('HAK_MILIK', 'Hak Milik'),
    ]

    STATUS_VERIFIKASI_CHOICES = [
        ('BELUM_DIVERIFIKASI', 'Belum Diverifikasi'),
        ('PERLU_REVIEW', 'Perlu Review'),
        ('VALID', 'Valid'),
    ]
    
    KETERANGAN_SERTIFIKASI_CHOICES = [
    ('ASLI_PEMKOT', 'Asli - Pemerintah Kota Palu'),
    ('FOTOKOPI_PEMKOT', 'Fotokopi - Pemerintah Kota Palu'),
    ('ASLI_NON_PEMKOT', 'Asli - Pribadi/Provinsi/Kementerian'),
    ('FOTOKOPI_NON_PEMKOT', 'Fotokopi - Pribadi/Provinsi/Kementerian'),
]

    # opd
    id = models.BigAutoField(primary_key=True)
    opd = models.ForeignKey(MasterOPD, on_delete=models.SET_NULL, blank=True, null=True)

    # identitas aset
    nama_barang = models.CharField(max_length=200, blank=True, null=True)
    kode_barang = models.CharField(max_length=50, blank=True, null=True)
    nibar = models.CharField(max_length=50, blank=True, null=True)
    nomor_register = models.CharField(max_length=20, blank=True, null=True)
    
    # data fisik
    luas_m2 = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    satuan = models.CharField(max_length=10, default='m2')
    nilai_aset = models.BigIntegerField(default=0, blank=True, null=True)
    cara_perolehan = models.CharField(max_length=50, choices=CARA_PEROLEHAN_CHOICES, blank=True, null=True)
    tanggal_perolehan = models.DateField(blank=True, null=True)
    alamat_lokasi = models.TextField(blank=True, null=True)
    kelurahan = models.ForeignKey('RefKelurahan', on_delete=models.SET_NULL, blank=True, null=True)
    kelurahan_nama = models.CharField(max_length=100, blank=True, null=True)
    kecamatan_nama = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    
    # status sertifikasi
    status_kepemilikan = models.CharField(max_length=50, choices=STATUS_KEPEMILIKAN_CHOICES, blank=True, null=True)
    status_sertifikasi = models.CharField(max_length=25, choices=STATUS_SERTIFIKASI_CHOICES, default='BELUM_BERSERTIFIKAT')
    nomor_sertifikat = models.CharField(max_length=150, blank=True, null=True)
    status_hak_sementara = models.CharField(max_length=50, choices=STATUS_HAK_SEMENTARA_CHOICES, blank=True, null=True)
    nomor_hak = models.CharField(max_length=150, blank=True, null=True)
    keterangan_sertifikasi_lainnya = models.CharField(max_length=50, choices=KETERANGAN_SERTIFIKASI_CHOICES, blank=True, null=True)
    nama_pemegang_hak = models.CharField(max_length=255, blank=True, null=True)
    
    # peggunaan
    status_penggunaan = models.CharField(max_length=100, blank=True, null=True)
    kondisi_pemanfaatan = models.CharField(max_length=50, choices=KONDISI_PEMANFAATAN_CHOICES, blank=True, null=True)
    spesifikasi_nama_barang = models.CharField(max_length=255, blank=True, null=True)
    spesifikasi_lainnya = models.TextField(blank=True, null=True)
    keterangan = models.TextField(blank=True, null=True)
    
    # status verifikasi (admin)
    catatan_revisi = models.TextField(blank=True, null=True)
    status_verifikasi = models.CharField(max_length=50, choices=STATUS_VERIFIKASI_CHOICES, default='BELUM_DIVERIFIKASI')
    
    # lainnya
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    created_by_id = models.IntegerField(blank=True, null=True)
    updated_by_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'master_aset_tanah'

    def __str__(self):
        return f"{self.nama_barang} - {self.kode_barang}"
    
# foto 
class FotoAsetTanah(models.Model):
    # Hubungkan ke AsetTanah menggunakan ForeignKey
    aset = models.ForeignKey(AsetTanah, on_delete=models.CASCADE, related_name='koleksi_foto')
    file_foto = models.ImageField(upload_to='foto-tanah', storage=AsetTanahStorage())
    diunggah_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'foto_aset_tanah'


# Sertifikat Tanah
class SertifikatTanah(models.Model):
    STATUS_HAK_CHOICES = [
        ('HAK_PAKAI', 'Hak Pakai'),
        ('HAK_MILIK', 'Hak Milik'),
    ]
    KETERANGAN_CHOICES = [
        ('ASLI', 'Asli'),
        ('FOTOKOPI', 'Foto Kopi'),
    ]

    id = models.BigAutoField(primary_key=True)
    aset_tanah = models.ForeignKey(AsetTanah, on_delete=models.CASCADE, related_name='data_sertifikat')
    opd = models.ForeignKey(MasterOPD, on_delete=models.SET_NULL, blank=True, null=True, related_name='sertifikat_opd')

    nomor_sertifikat = models.CharField(max_length=150)
    nama_pemegang_hak = models.CharField(max_length=255, default='Pemerintah Kota Palu')
    alamat = models.TextField(blank=True, null=True)
    peruntukan = models.CharField(max_length=255, blank=True, null=True)
    status_hak = models.CharField(max_length=20, choices=STATUS_HAK_CHOICES)
    nomor_hak = models.CharField(max_length=150, blank=True, null=True)
    
    luas = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    tanggal_pembuatan = models.DateField(blank=True, null=True)
    tahun_terbit = models.SmallIntegerField(blank=True, null=True)
    nilai = models.BigIntegerField(default=0, blank=True, null=True)
    
    pemetaan_bpn = models.CharField(max_length=255, blank=True, null=True)
    keterangan = models.CharField(max_length=15, choices=KETERANGAN_CHOICES)
    catatan = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        managed = True
        db_table = 'sertifikat_tanah'


# Data Kecamatan
class RefKecamatan(models.Model):
    id = models.BigAutoField(primary_key=True)
    nama_kecamatan = models.CharField(unique=True, max_length=100)
    kode_kecamatan = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'ref_kecamatan'


# Data Kelurahan
class RefKelurahan(models.Model):
    id = models.BigAutoField(primary_key=True)
    kecamatan = models.ForeignKey(RefKecamatan, models.DO_NOTHING)
    nama_kelurahan = models.CharField(max_length=100)
    kode_kelurahan = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'ref_kelurahan'
        unique_together = (('kecamatan', 'nama_kelurahan'),)



   
