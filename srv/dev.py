from .base import *
from dotenv import load_dotenv


load_dotenv(BASE_DIR / '.env')




DEBUG = True

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS","127.0.0.1").split(",")



# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django-test',
        'USER': 'django-test',
        'PASSWORD': 'django-test',
        'HOST': '10.20.30.203',
        'PORT': '3306',
    }
}
"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}