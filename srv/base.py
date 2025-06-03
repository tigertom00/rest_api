from pathlib import Path
import os
from datetime import timedelta


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    #'django.contrib.sites',
    # 3rd party apps
    'rest_framework',
    'rest_framework.authtoken',
    #'allauth',
    #'allauth.account',
    #'allauth.socialaccount',
    #'dj_rest_auth',  # Django REST framework authentication
    #'dj_rest_auth.registration',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',  
    'drf_spectacular',  # Core API for common functionality
    # Local apps
    'restAPI'
]


# rest framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',  
}

# Allauth settings

#SITE_ID = 1  # Required for allauth

#AUTHENTICATION_BACKENDS = [
    
    # Needed to login by username in Django admin, regardless of `allauth`
    #'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by email
    #'allauth.account.auth_backends.AuthenticationBackend',
    
#]


#ACCOUNT_ADAPTER = "allauth.account.adapter.DefaultAccountAdapter"

#ACCOUNT_LOGIN_METHODS = {'email'}
#ACCOUNT_SIGNUP_FIELDS = ['username', 'email*', 'password1*', 'password2*']

# * DJ Rest Auth
#REST_AUTH_SERIALIZERS = {
    #'USER_DETAILS_SERIALIZER': 'restAPI.serializers.UsersSerializer'
#}
#REST_USE_JWT = True

# Simple JWT settings
#SIMPLE_JWT = {
    #'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    ##'ROTATE_REFRESH_TOKENS': True,
    #'BLACKLIST_AFTER_ROTATION': True,
    #'AUTH_HEADER_TYPES': ('jwt'),
#}

# CORS settings to allow your frontend to communicate with the backend
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    'http://localhost:19006',  # Expo default port
    'http://127.0.0.1:8000',   # Django backend
    'http://192.168.106.126:8000',
]

# User model

AUTH_USER_MODEL = 'restAPI.CustomUser'

# Spec settings for drf_spectacular
SPECTACULAR_SETTINGS = {
    'TITLE': 'DjangoAPI',
    'DESCRIPTION': 'API for all things...',
    'VERSION': '0.0.1',
    'SERVE_INCLUDE_SCHEMA': True,
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

# Email settings

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # Or your SMTP server
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_USERNAME')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASSWORD')


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",    # CORS middleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    #"allauth.account.middleware.AccountMiddleware", # Allauth middleware
]

ROOT_URLCONF = 'srv.urls'



TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',  # Add this to include custom templates
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'srv.wsgi.application'




# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]




# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True



# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'