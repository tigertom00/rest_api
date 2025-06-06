from .base import *
from dotenv import load_dotenv


load_dotenv(BASE_DIR / '.env')

ALLOWED_HOSTS = ("api.nxfs.no", "10.20.30.203", "127.0.0.1")

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