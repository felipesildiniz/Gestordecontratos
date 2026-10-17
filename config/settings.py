"""Configurações do Gestor de Contratos — Licitações.

Os valores que mudam de um computador para outro (senhas, endereços) ficam no
arquivo .env, que não deve ser compartilhado. Veja .env.example.
"""
import sys
from pathlib import Path

from .env import booleano, carregar_env, lista, texto

BASE_DIR = Path(__file__).resolve().parent.parent
carregar_env(BASE_DIR / ".env")

TESTANDO = "test" in sys.argv
DEBUG = booleano("DJANGO_DEBUG", False)

SECRET_KEY = texto("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG or TESTANDO:
        SECRET_KEY = "chave-insegura-apenas-para-desenvolvimento-e-testes"
    else:
        raise RuntimeError(
            "A variável DJANGO_SECRET_KEY não está definida. "
            "Copie .env.example para .env e preencha (veja INSTALACAO_WINDOWS.md)."
        )

# Nomes ou IPs pelos quais o servidor pode ser acessado na rede.
ALLOWED_HOSTS = lista("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = lista("DJANGO_CSRF_TRUSTED_ORIGINS", "")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

# Banco de dados: PostgreSQL (decisão D-004).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": texto("DB_NOME", "gestor_contratos"),
        "USER": texto("DB_USUARIO", "gestor"),
        "PASSWORD": texto("DB_SENHA"),
        "HOST": texto("DB_HOST", "localhost"),
        "PORT": texto("DB_PORTA", "5432"),
        "CONN_MAX_AGE": 60,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Idioma e horário de Cametá (Pará): UTC-3, sem horário de verão.
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Belem"
USE_I18N = True
USE_TZ = True

# Arquivos estáticos (CSS), servidos pelo WhiteNoise.
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

# Login e sessão.
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "login"
SESSION_COOKIE_AGE = 8 * 60 * 60  # 8 horas sem uso encerram a sessão
SESSION_SAVE_EVERY_REQUEST = True

# O sistema roda em rede interna, sem HTTPS por enquanto. Se um dia houver
# HTTPS, defina DJANGO_USAR_HTTPS=True no .env.
USAR_HTTPS = booleano("DJANGO_USAR_HTTPS", False)
SESSION_COOKIE_SECURE = USAR_HTTPS
CSRF_COOKIE_SECURE = USAR_HTTPS
if USAR_HTTPS:
    # Atrás de um proxy HTTPS (ex.: Railway), confia no cabeçalho do proxy.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
