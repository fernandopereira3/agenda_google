from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv(".env", override=True)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "True") == "True"

if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ── Content Security Policy ─────────────────────────────────────────────────
CSP_DIRECTIVES = {
    "default-src": ["'self'"],
    "script-src": ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
    "style-src": [
        "'self'",
        "'unsafe-inline'",
        "https://fonts.googleapis.com",
        "https://cdnjs.cloudflare.com",
    ],
    "font-src": [
        "'self'",
        "https://fonts.gstatic.com",
        "https://cdnjs.cloudflare.com",
    ],
    "img-src": ["'self'", "data:"],
    "connect-src": ["'self'"],
    "object-src": ["'none'"],
    "base-uri": ["'self'"],
    # 'self' não basta: o form de login social (allauth) redireciona para o
    # provedor OAuth após o POST, e o Chromium aplica form-action também ao
    # destino desse redirect, não só à action do <form>.
    "form-action": ["'self'", "https://accounts.google.com"],
    "frame-ancestors": ["'none'"],
}

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

ALLOWED_HOSTS = ["*"]
_origins = os.getenv("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = []
for _o in (o.strip() for o in _origins.split(",") if o.strip()):
    if _o.startswith(("http://", "https://")):
        CSRF_TRUSTED_ORIGINS.append(_o)
    else:
        # Sem esquema: adiciona http e https para não bloquear nenhum dos dois
        CSRF_TRUSTED_ORIGINS.append(f"http://{_o}")
        CSRF_TRUSTED_ORIGINS.append(f"https://{_o}")

# Application definition

INSTALLED_APPS = [
    "core.mongo_apps.MongoContentTypesConfig",
    "django.contrib.staticfiles",
    "core.mongo_apps.MongoAuthConfig",
    "django.contrib.sessions",
    "django.contrib.messages",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "agenda",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "core.middleware.ContentSecurityPolicyMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.MobileDetectionMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]


ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "agenda" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.google_calendar_status",
            ],
        },
    },
]

# ── Autenticação (login via Google, sem cadastro local) ─────────────────────
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

LOGIN_URL = "account_login"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "account_login"

# Login tradicional (usuário/senha). Contas são criadas pelo administrador
# via /admin/ — não há cadastro público (ver core/account_adapter.py).
ACCOUNT_ADAPTER = "core.account_adapter.NoSignupAccountAdapter"
ACCOUNT_LOGIN_METHODS = {"username"}
ACCOUNT_SIGNUP_FIELDS = ["username*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_LOGOUT_ON_GET = False

# Config do provedor Google fica pronta para a Fase B (conectar a agenda ao
# Google Calendar a partir de dentro do sistema, não para login no site).
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": [
            "profile",
            "email",
            "https://www.googleapis.com/auth/calendar.readonly",
        ],
        "AUTH_PARAMS": {
            "access_type": "offline",
            "prompt": "consent",
        },
        "OAUTH_PKCE_ENABLED": True,
        "APP": {
            "client_id": os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
            "secret": os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
            "key": "",
        },
    }
}

WSGI_APPLICATION = "core.wsgi.application"


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django_mongodb_backend",
        "NAME": os.getenv("DB_NAME"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": int(os.getenv("DB_PORT", 27017)),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "OPTIONS": {"tlsAllowInvalidCertificates": True},
    }
}


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = "pt-br"

TIME_ZONE = "America/Sao_Paulo"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Additional locations of static files
STATICFILES_DIRS = [
    BASE_DIR / "agenda" / "static",
]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Se você não rodar o comando 'python manage.py collectstatic',
# o Whitenoise precisa buscar os estáticos diretamente nos STATICFILES_DIRS.
# Isso evita problemas com o arquivo CSS não sendo encontrado com o Gunicorn.
WHITENOISE_USE_FINDERS = True

# Tempo em segundos que o navegador deve guardar os arquivos estáticos
WHITENOISE_MAX_AGE = 600  # 10 minutos

# Default primary key field type
# https://docs.djangoproject.com/en/6.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django_mongodb_backend.fields.ObjectIdAutoField"
ALLAUTH_DEFAULT_AUTO_FIELD = DEFAULT_AUTO_FIELD

# django_mongodb_backend não suporta o AutoField (inteiro) padrão do Django,
# então contrib.auth/contenttypes usam ObjectIdAutoField (via MongoAuthConfig/
# MongoContentTypesConfig). Isso diverge do id fixado nas migrations que esses
# apps já trazem prontas, então as migrations de ajuste ficam aqui no projeto
# em vez de serem escritas dentro do pacote instalado (site-packages).
MIGRATION_MODULES = {
    "contenttypes": "core.migrations_overrides.contenttypes",
    "auth": "core.migrations_overrides.auth",
    "account": "core.migrations_overrides.allauth_account",
    "socialaccount": "core.migrations_overrides.allauth_socialaccount",
}


# ── E-mail (Hostinger SMTP) ─────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.hostinger.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 465))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
DEFAULT_FROM_EMAIL = os.getenv("EMAIL_FROM", EMAIL_HOST_USER)
