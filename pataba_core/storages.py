# File: pataba_core/storages.py
from storages.backends.s3boto3 import S3Boto3Storage

class PublikasiStorage(S3Boto3Storage):
    bucket_name = 'konten_publik' # Sesuaikan dengan nama bucket di Supabase

class ProfileStorage(S3Boto3Storage):
    bucket_name = 'foto_profil' # Sesuaikan dengan nama bucket di Supabase