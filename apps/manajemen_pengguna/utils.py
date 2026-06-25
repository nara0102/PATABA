# manajemen_pengguna/utils.py

# Panggil model dari aplikasi aset_tanah secara spesifik
from .models import UserProfile

def get_user_profile(user):
    try:
        return UserProfile.objects.get(user__username=user.username)
    except UserProfile.DoesNotExist:
        return None