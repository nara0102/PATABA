from pathlib import Path
import os
import environ
from dotenv import load_dotenv

# Setup BASE_DIR (HARUS PALING AWAL)
BASE_DIR = Path(__file__).resolve().parent.parent

# Setup Environ
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Database Configuration (Supabase)
DATABASES = {
    'default': env.db(),
}
SECRET_KEY = env('SECRET_KEY', default='narvt010201chzie3000')
DEBUG = env.bool('DEBUG', default=True)

# Pengaturan Akses Terbuka untuk Ngrok
ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = [
    'https://mullets-fancy-maritime.ngrok-free.dev',
    'https://*.ngrok-free.dev',
    'https://*.ngrok-free.app',
    'https://*.ngrok.io',
]

# Memberitahu Django bahwa request dari Ngrok itu HTTPS yang aman
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# session terbaca dari https ke http
SESSION_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_SECURE = True

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    
    'storages',
    # Aplikasi Lokal
    'apps.aset_tanah',
    'apps.manajemen_pengguna',
    'apps.portal_publik',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # penting untuk deployment
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware', # language
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pataba_core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'frontend/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug', 
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.manajemen_pengguna.context_processors.user_profile',
            ],
        },
    },
]

WSGI_APPLICATION = 'pataba_core.wsgi.application'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
USE_THOUSAND_SEPARATOR = False
LANGUAGE_CODE = 'id' # Bahasa Indonesia
TIME_ZONE = 'Asia/Makassar' # Zona Waktu WITA (Palu)
USE_I18N = True
USE_L10N = True
USE_TZ = True

# DAFTARKAN BAHASA YANG KITA JUAL (Indonesia & Inggris)
from django.utils.translation import gettext_lazy as _
LANGUAGES = [
    ('id', _('Indonesian')),
    ('en', _('English')),
]

# TEMPAT MENYIMPAN KAMUS TERJEMAHAN NANTI
LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'frontend/static'), 
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# EMAIL CONFIG
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='') 

# Login
LOGIN_URL = 'auth:login'

# Session Remember me
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 1209600

# MEDIA KONTEN (Penyimpanan Gambar Hasil Upload)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# storages
AWS_ACCESS_KEY_ID = env('SUPABASE_ACCESS_KEY', default='')
AWS_SECRET_ACCESS_KEY = env('SUPABASE_SECRET_KEY', default='')
AWS_S3_ENDPOINT_URL = env('SUPABASE_ENDPOINT', default='')
AWS_S3_REGION_NAME = env('SUPABASE_REGION', default='ap-northeast-1')
AWS_DEFAULT_ACL = None

# Konfigurasi Tambahan Wajib agar gambar bisa tampil di HTML:
AWS_QUERYSTRING_AUTH = False 
AWS_S3_FILE_OVERWRITE = True

AWS_S3_ADDRESSING_STYLE = 'path'   
AWS_S3_SIGNATURE_VERSION = 's3v4'