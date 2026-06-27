from django.db import models
from django.contrib.auth.models import User
from pataba_core.storages import PublikasiStorage

# =========================================
# PESAN (DARI WARGA/PUBLIK)
# =========================================
class PesanKontak(models.Model):
    KATEGORI_CHOICES = [
        ('permohonan', 'Permohonan Data'),
        ('kerusakan', 'Laporan Kerusakan'),
        ('pendaftaran', 'Pendaftaran Aset Pribadi'),
        ('info_aset', 'Informasi Aset Daerah'),
    ]
    
    nama = models.CharField(max_length=100)
    email = models.EmailField()
    hp = models.CharField(max_length=20)
    kategori = models.CharField(max_length=50, choices=KATEGORI_CHOICES)
    pesan = models.TextField()
    dibuat_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pesan_kontak'

    def __str__(self):
        return f"{self.nama} - {self.get_kategori_display()}"


# =========================================
# KONTEN PUBLIK (BERITA & PENGUMUMAN)
# =========================================
class PublikasiInstansi(models.Model):
    KATEGORI_CHOICES = [
        ('PENGUMUMAN', 'Pengumuman Penting'),
        ('BERITA', 'Berita BPKAD'),
        ('KEGIATAN', 'Galeri Kegiatan'),
    ]

    judul = models.CharField(max_length=255)
    kategori = models.CharField(max_length=20, choices=KATEGORI_CHOICES)
    isi_konten = models.TextField(blank=True, null=True) 
    gambar_utama = models.ImageField(
        upload_to='konten-publik', 
        storage=PublikasiStorage(),  
        blank=True, null=True
    ) 
    
    tanggal_upload = models.DateTimeField(auto_now_add=True)
    diupload_oleh = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        db_table = 'publikasi_instansi'
        ordering = ['-tanggal_upload']