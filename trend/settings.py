import os
import socket
from pathlib import Path
from datetime import timedelta
from environ import Env

# Initialize environment variables
env = Env()
READ_ENV_FILE = env.bool("DJANGO_READ_ENV_FILE", default=True)

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from a .env file if specified
if READ_ENV_FILE:
    Env.read_env(str(BASE_DIR / ".env"))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY", default="your-secret-key-here")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=True)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

try:
    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = [ip for ip in ips] + ['127.0.0.1']
except socket.gaierror:
    INTERNAL_IPS = ['127.0.0.1']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'whitenoise.runserver_nostatic',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt.token_blacklist',
    'drf_yasg',
    'django_extensions',
    'django_celery_beat',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    "dj_rest_auth",
    'dj_rest_auth.registration',
    # Your apps
    'vlog',
    'post',
    'profile_app',
    'authentication',
    'storages',
    'notifications',
    'reactions',
]

# django.contrib.sites
SITE_ID = 1
AUTH_USER_MODEL = "authentication.CustomUser"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = 'trend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'trend.wsgi.application'

# Database configuration
USE_POSTGRES_DB = env.bool("USE_POSTGRES_DB", default=False)
DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
# if not USE_POSTGRES_DB:
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.sqlite3',
#             'NAME': BASE_DIR / 'db.sqlite3',
#         }
#     }
# else:
#     DATABASES = {
#         "default": {
#             "ENGINE": env("SQL_ENGINE", default="django.db.backends.postgresql"),
#             "NAME": env("POSTGRES_DB", default="mydatabase"),
#             "USER": env("POSTGRES_USER", default="myuser"),
#             "PASSWORD": env("POSTGRES_PASSWORD", default="mypassword"),
#             "HOST": env("POSTGRES_HOST", default="localhost"),
#             "PORT": env("POSTGRES_PORT", default="5432"),
#         }
#     }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static and Media files configuration
STATIC_URL = '/static/'  # The URL used to serve static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # The directory for collectstatic to use
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]  # Optional: custom static files during development
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# AWS S3 Configuration (For production with AWS S3)
USE_S3 = env.bool("USE_S3", default=False)
if USE_S3:
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="your-bucket-name")
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="us-east-1")
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
    STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"
    STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    AWS_DEFAULT_ACL = None

# Debug configuration for static files
if DEBUG and not USE_S3:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    STATIC_URL = '/static/'  # The URL used to serve static files
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # The directory for collectstatic to use
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Django Rest Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        # 'dj_rest_auth.jwt_auth.JWTCookieAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 10,
}

# JWT Configuration
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=365),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=730),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
}

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]


# CORS settings
CORS_ALLOW_ALL_ORIGINS = True

# Celery configuration
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# Additional application-specific settings

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Print settings to verify
print(f"Debug Mode: {DEBUG}")
print(f"Allowed Hosts: {ALLOWED_HOSTS}")
print(f"Using S3: {USE_S3}")
print(f"Static URL: {STATIC_URL}")
print(f"Media URL: {MEDIA_URL}")
# Other settings...

# Maximum video file size in bytes (e.g., 200MB)
MAX_VIDEO_SIZE = env.float("MAX_VIDEO_SIZE", default=200*1024*1024)  # Example: 200 MB in bytes
MAX_VIDEO_DURATION = env.float("MAX_VIDEO_DURATION", default=30)  # Example: 30 seconds 


BASE_BACKEND_URL = env("BASE_BACKEND_URL", default="http://localhost:8000")

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'mpandhp@gmail.com'
EMAIL_HOST_PASSWORD = 'attl tvgh sjag kxgm'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'


ACCOUNT_AUTHENTICATION_METHOD = "email"  # Use Email / Password authentication
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "none" # Do not require email confirmation

# Google OAuth
GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_OAUTH_CALLBACK_URL = os.getenv("GOOGLE_OAUTH_CALLBACK_URL")
GOOGLE_AUTH_URL = os.getenv("GOOGLE_AUTH_URL", "https://accounts.google.com/o/oauth2/auth")

# django-allauth (social)
# Authenticate if local account with this email address already exists
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
# Connect local account and social account if local account with that email address already exists
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APPS": [
            {
                "client_id": GOOGLE_OAUTH_CLIENT_ID,
                "secret": GOOGLE_OAUTH_CLIENT_SECRET,
                "key": "",
            },
        ],
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
    }
}