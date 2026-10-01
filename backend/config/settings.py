from datetime import timedelta
from pathlib import Path

from django.templatetags.static import static

from config.env import env_flag, env_int, env_list, env_required, env_text

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = env_required("DJANGO_SECRET_KEY")
DEBUG = env_flag("DJANGO_DEBUG")
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
COOKIE_SECURE = env_flag("COOKIE_SECURE")

SESSION_LIFETIME = timedelta(hours=8)
LOGIN_FAILURE_LIMIT = 5
LOGIN_COOLOFF = timedelta(minutes=15)
PASSWORD_MIN_LENGTH = 12
DATABASE_CONNECTION_AGE_SECONDS = 60
BACKGROUND_TASK_TIMEOUT_SECONDS = 1800
BACKGROUND_TASK_RETRY_SECONDS = BACKGROUND_TASK_TIMEOUT_SECONDS + 60
BACKGROUND_TASK_HISTORY = 100
HSE_REQUEST_DELAY_SECONDS = 0.7

INSTALLED_APPS = [
    "unfold",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts.login_protection.LoginProtectionConfig",
    "django_q",
    "core",
    "accounts",
    "catalog",
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
    "axes.middleware.AxesMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

LOGIN_URL = "admin:login"
LOGIN_REDIRECT_URL = "admin:index"

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "HOST": env_text("DB_HOST", "db"),
        "PORT": env_int("DB_PORT", 3306),
        "NAME": env_text("DB_NAME", "dpo"),
        "USER": env_text("DB_USER", "dpo"),
        "PASSWORD": env_text("DB_PASSWORD"),
        "CONN_MAX_AGE": DATABASE_CONNECTION_AGE_SECONDS,
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        "TEST": {
            "NAME": env_text("DB_TEST_NAME", "test_dpo"),
            "CHARSET": "utf8mb4",
            "COLLATION": "utf8mb4_unicode_ci",
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": PASSWORD_MIN_LENGTH},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / "locale"]

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(env_text("MEDIA_ROOT", str(BASE_DIR / "media")))
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_COOKIE_NAME = "dpo_session"
SESSION_COOKIE_AGE = int(SESSION_LIFETIME.total_seconds())
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = COOKIE_SECURE
CSRF_COOKIE_NAME = "dpo_csrftoken"
CSRF_COOKIE_SECURE = COOKIE_SECURE
CSRF_COOKIE_HTTPONLY = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

AXES_FAILURE_LIMIT = LOGIN_FAILURE_LIMIT
AXES_COOLOFF_TIME = LOGIN_COOLOFF
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]
AXES_RESET_ON_SUCCESS = True
AXES_CLIENT_IP_CALLABLE = "core.client_ip.client_ip"

BRAND_BLUE = {
    "50": "oklch(97% .015 262)",
    "100": "oklch(93.5% .035 262)",
    "200": "oklch(88% .065 262)",
    "300": "oklch(80% .11 262)",
    "400": "oklch(69% .16 262)",
    "500": "oklch(58% .195 262)",
    "600": "oklch(50.7% .2 262.1)",
    "700": "oklch(42.6% .175 262)",
    "800": "oklch(36% .14 262)",
    "900": "oklch(30% .11 262)",
    "950": "oklch(22% .08 262)",
}

UNFOLD = {
    "SITE_TITLE": "Центр ДПО",
    "SITE_HEADER": "Центр ДПО",
    "SITE_SUBHEADER": "Факультет права НИУ ВШЭ",
    "SITE_URL": "/",
    "SITE_ICON": lambda request: static("core/brand-mark.webp"),
    "SITE_FAVICONS": [
        {"rel": "icon", "sizes": "32x32", "type": "image/png", "href": lambda request: static("core/favicon-32.png")},
    ],
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "COLORS": {"primary": BRAND_BLUE},
}

Q_CLUSTER = {
    "name": "dpo",
    "label": "Фоновые задачи",
    "orm": "default",
    "workers": 1,
    "timeout": BACKGROUND_TASK_TIMEOUT_SECONDS,
    "retry": BACKGROUND_TASK_RETRY_SECONDS,
    "max_attempts": 1,
    "catch_up": False,
    "save_limit": BACKGROUND_TASK_HISTORY,
    "ack_failures": True,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env_text("LOG_LEVEL", "INFO")},
    "loggers": {"httpx": {"level": "WARNING"}, "httpcore": {"level": "WARNING"}},
}

SILENCED_SYSTEM_CHECKS = ["models.W037"]
