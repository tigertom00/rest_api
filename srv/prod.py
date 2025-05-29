from base import *

DEBUG = True

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS","127.0.0.1").split(",")

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