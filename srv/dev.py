from .base import *
from dotenv import load_dotenv


load_dotenv(BASE_DIR / '.env')

#SECRET_KEY = os.environ.get("SECRET_KEY")


#ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS","127.0.0.1").split(",")
ALLOWED_HOSTS =  ['192.168.106.126', 'localhost', '127.0.0.1', '10.20.30.202', 'api.nxfs.no', '10.20.30.203']


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}
"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
