from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from apps.aset_tanah.models import MasterOPD
from pataba_core.storages import ProfileStorage

User = get_user_model()

# Profil 
class UserProfile(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=12)
    opd = models.ForeignKey(MasterOPD, on_delete=models.CASCADE, blank=True, null=True)
    nip = models.CharField(max_length=50, blank=True, null=True)
    jabatan = models.CharField(max_length=100, blank=True, null=True)
    nomor_hp = models.CharField(max_length=20, blank=True, null=True)
    
    # --- TAMBAHAN BARU: Kolom Foto Profil ---
    foto_profil = models.ImageField(
        upload_to='foto-profil', 
        storage=ProfileStorage(),    # <--- INI KUNCINYA
        blank=True, null=True
    ) 
    
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    is_active = models.IntegerField()
    
    class Meta:
        managed = True
        db_table = 'user_profile'
        
        
# Catatan Aktivitas
class AuditLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    aksi = models.CharField(max_length=100) 
    objek = models.CharField(max_length=255) 
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    waktu = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        managed = True
        db_table = 'audit_log'
        ordering = ['-waktu'] 