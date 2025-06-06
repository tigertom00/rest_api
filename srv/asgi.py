"""
ASGI config for srv project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

settings_module = 'srv.dev'
        # Check environment variable for DEBUG
debug = os.environ.get('DJANGO_DEBUG', 'True') == 'True'
if not debug:
   settings_module = 'srv.prod'


os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

application = get_asgi_application()
