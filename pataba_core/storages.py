# File: pataba_core/storages.py
from storages.backends.s3boto3 import S3Boto3Storage

class PublikasiStorage(S3Boto3Storage):
    bucket_name = 'konten_publik' # Sesuaikan dengan nama bucket di Supabase
    custom_domain = 'fsxojsackyaccxdgnipi.supabase.co/storage/v1/object/public/konten_publik'

class ProfileStorage(S3Boto3Storage):
    bucket_name = 'foto_profil' # Sesuaikan dengan nama bucket di Supabase
    custom_domain = 'fsxojsackyaccxdgnipi.supabase.co/storage/v1/object/public/foto_profil'
    
class AsetTanahStorage(S3Boto3Storage):
    bucket_name = 'aset_tanah'
    custom_domain = 'fsxojsackyaccxdgnipi.supabase.co/storage/v1/object/public/aset_tanah'