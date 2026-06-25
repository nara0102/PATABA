# manajemen_pengguna/context_processors.py

from .utils import get_user_profile

def user_profile(request):
    if request.user.is_authenticated:
        return {'profile': get_user_profile(request.user)}
    return {'profile': None}