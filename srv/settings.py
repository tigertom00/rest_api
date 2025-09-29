import os
import socket
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# * Load directories and environment variables
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_URLCONF = "srv.urls"
WSGI_APPLICATION = "srv.wsgi.application"
AUTH_USER_MODEL = "restAPI.CustomUser"
load_dotenv(BASE_DIR / ".env")

# * Security settings
SECRET_KEY = os.getenv("SECRET_KEY")
TRANSLATION_AUTH_KEY = os.getenv("TRANSLATION_AUTH_KEY")

# * n8n integration settings
N8N_TRANSLATE_WEBHOOK_URL = os.getenv(
    "N8N_TRANSLATE_WEBHOOK_URL", "https://n8n.nxfs.no/webhook/translate-task"
)
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.nxfs.no")

# * Applications
INSTALLED_APPS = [
    "django.contrib.admin",  # Admin interface
    "django.contrib.auth",  # Authentication framework
    "django.contrib.contenttypes",  # Content types framework
    "django.contrib.sessions",  # Session management
    "django.contrib.messages",  # Message framework for user notifications
    "django.contrib.staticfiles",  # Static files (CSS, JavaScript, Images)
    # 'django.contrib.sites',
    # * 3rd party apps
    "rest_framework",  # Django REST Framework for building APIs
    "rest_framework.authtoken",  # Token authentication for Django REST Framework
    "rest_framework_simplejwt",  # Simple JWT for token authentication
    "rest_framework_simplejwt.token_blacklist",  # Token blacklist for JWT
    "oauth2_provider",  # OAuth2 provider for external app authentication
    "corsheaders",  # CORS headers for cross-origin requests
    "drf_spectacular",  # DRF Spectacular for OpenAPI schema generation
    "channels",  # Channels for WebSockets and async support (push notifications, etc.)
    # * Local apps
    "restAPI",  # Your custom app for the API with User models and middleware
    "app.tasks",
    "app.todo",
    "app.blog",
    "app.memo",
    "app.components",
    "app.docker_monitor",  # Docker container monitoring
    "mcp_server",  # MCP server for AI integration
]

# * Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.gzip.GZipMiddleware",  # GZip compression middleware
    "restAPI.utils.monitoring.PerformanceMonitoringMiddleware",  # Performance monitoring - now production-safe
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # CORS middleware
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "restAPI.utils.restrictpaths.RestrictPathsMiddleware",  # Custom middleware for restricted paths
]


# * Template configuration
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",  # Add this to include custom templates
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# * Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# * rest framework settings
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",  # OAuth2 authentication
        "restAPI.utils.clerk.ClerkAuthentication",  # Custom authentication class for Clerk
        "rest_framework_simplejwt.authentication.JWTAuthentication",  # Simple JWT authentication
        "rest_framework.authentication.TokenAuthentication",  # API Server Token authentication
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "restAPI.utils.exceptions.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "restAPI.utils.pagination.StandardResultsSetPagination",
    # "DEFAULT_THROTTLE_CLASSES": [
    #     "restAPI.utils.throttling.APIRateThrottle",
    #     "restAPI.utils.throttling.AnonymousRateThrottle",
    # ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",  # Anonymous users: 100 requests per hour
        "api": "1000/hour",  # Authenticated users: 1000 requests per hour
        "login": "5/min",  # Login attempts: 5 per minute
        "upload": "50/hour",  # File uploads: 50 per hour
        "bulk": "10/hour",  # Bulk operations: 10 per hour
        "admin": "200/hour",  # Admin operations: 200 per hour
        "sustained": "5000/day",  # Daily limit: 5000 requests per day
        "database": "100/hour",  # Database heavy operations: 100 per hour
    },
}

# * Simple JWT settings
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer"),
}

# * Clerk settings
CLERK_URL = os.getenv("CLERK_URL")
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")
CLERK_WEBHOOK_KEY = os.getenv("CLERK_WEBHOOK_KEY")
CLERK_JWT_PUBLIC_KEY_URL = f"{CLERK_URL}/.well-known/jwks.json"

# * Host settings
ALLOWED_HOSTS = (
    "api.nxfs.no",
    "10.20.30.203",
    "10.20.30.202",
    "127.0.0.1",
    "localhost",
)

# * CORS settings to allow your frontend to communicate with the backend
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8080",  # Expo default port
    "http://127.0.0.1:8080",  # Django backend
    "http://10.20.30.203:8080",
    "https://api.nxfs.no:443",
    "https://www.nxfs.no",
    "https://nxfs.no",
    "https://n8n.nxfs.no",
    "https://cloud.nxfs.no",
    "http://10.20.30.202:3000",  # React frontend dev
]
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]
CSRF_TRUSTED_ORIGINS = [
    "http://10.20.30.203:8080",
    "https://api.nxfs.no:443",
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_TLS = True


# * Spec settings for drf_spectacular
SPECTACULAR_SETTINGS = {
    "TITLE": "DjangoAPI",
    "DESCRIPTION": "API for all things...",
    "VERSION": "0.0.1",
    "SERVE_INCLUDE_SCHEMA": True,
    "COMPONENT_SPLIT_REQUEST": True,
    "SECURITY": [
        {
            "jwtAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        },
        {
            "oauth2": {
                "type": "oauth2",
                "flows": {
                    "authorizationCode": {
                        "authorizationUrl": "/auth/o/authorize/",
                        "tokenUrl": "/auth/o/token/",
                        "scopes": {
                            "read": "Read access",
                            "write": "Write access",
                        },
                    }
                },
            }
        },
    ],
    "ENUM_NAME_OVERRIDES": {
        "Status68aEnum": "TaskStatusEnum",
        "Status073Enum": "ProjectStatusEnum",
        "Status041Enum": "ContainerStatusEnum",
    },
    "DISABLE_ERRORS_AND_WARNINGS": True,
}

# File upload settings
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
    }
}

# Development machine settings Database setup
DEV_IP = "10.20.30.202"
current_ip = socket.gethostbyname(socket.gethostname())

if current_ip == DEV_IP:
    # print("Running on development machine, using MySQL Production Database.")
    DEBUG = True
    # DATABASES = {
    #   'default': {
    #      'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': BASE_DIR / 'db.sqlite3',
    # }
    # }
else:
    print("Running on production server, using MySQL DB. DEBUG=False")
    DEBUG = False


# * Channels settings for WebSockets (push notifications, etc.)
ASGI_APPLICATION = "srv.asgi.application"
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}
# * Gotify settings for push notifications
GOTIFY_URL = os.getenv("GOTIFY_URL")  # Your Gotify URL
GOTIFY_TOKEN = os.getenv("GOTIFY_TOKEN")  # Your Gotify application token
GOTIFY_ACCESS_TOKEN = os.getenv("GOTIFY_ACCESS_TOKEN")  # Access token for Gotify


# * Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static/")
MEDIA_ROOT = os.path.join(BASE_DIR, "media/")
MEDIA_URL = "/media/"

STATICFILES_DIRS = []

# * Email settings

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"  # Or your SMTP server
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_USERNAME")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_PASSWORD")


# * Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "nb-no"

TIME_ZONE = "Europe/Oslo"

USE_I18N = True

USE_TZ = True


# * OAuth2 Provider settings
OAUTH2_PROVIDER = {
    "SCOPES": {
        "read": "Read scope",
        "write": "Write scope",
    },
    "ACCESS_TOKEN_EXPIRE_SECONDS": 3600,
    "REFRESH_TOKEN_EXPIRE_SECONDS": 3600 * 24 * 7,  # 7 days
    "AUTHORIZATION_CODE_EXPIRE_SECONDS": 600,
    "ROTATE_REFRESH_TOKEN": True,
}

# Login URL for OAuth2
LOGIN_URL = "/admin/login/"

# * MCP Server settings
DJANGO_MCP_AUTHENTICATION_CLASSES = [
    "oauth2_provider.contrib.rest_framework.OAuth2Authentication",  # OAuth2 for MCP
    "rest_framework.authentication.TokenAuthentication",  # Token auth for MCP
]

# * Celery Configuration
CELERY_BROKER_URL = "redis://redis:6379/0"
CELERY_RESULT_BACKEND = "redis://redis:6379/0"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    "sync-docker-containers": {
        "task": "app.docker_monitor.tasks.sync_containers",
        "schedule": 120.0,  # Every 2 minutes
    },
    "collect-container-stats": {
        "task": "app.docker_monitor.tasks.collect_stats",
        "schedule": 300.0,  # Every 5 minutes
    },
}

# * Logging Configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "mcp_server": {
            "handlers": ["console"],
            "level": "ERROR",  # Suppress INFO/WARNING messages from MCP
            "propagate": False,
        },
        "django_mcp_server": {
            "handlers": ["console"],
            "level": "ERROR",  # Suppress INFO/WARNING messages from Django MCP
            "propagate": False,
        },
        "monitoring": {
            "handlers": ["console"],
            "level": "INFO",  # Performance monitoring logs
            "propagate": False,
        },
        "audit": {
            "handlers": ["console"],
            "level": "INFO",  # Audit logs
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# * Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# * Debug mode settings
if DEBUG:
    print("Running in DEBUG mode!")
    # Remove RestrictPathsMiddleware if in DEBUG mode
    MIDDLEWARE = [
        mw
        for mw in MIDDLEWARE
        if mw != "restAPI.utils.restrictpaths.RestrictPathsMiddleware"
    ]
