import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

APPS_DIR = BASE_DIR / "apps"

env = environ.Env()

SECRET_KEY = env("DJANGO_SECRET_KEY", default="foo")

DEBUG = env.bool("DJANGO_DEBUG", default=False)

# URLS
# ------------------------------------------------------------------------------

ROOT_URLCONF = 'config.urls'

# WSGI
# ------------------------------------------------------------------------------
WSGI_APPLICATION = 'config.wsgi.application'

# ASGI
# ------------------------------------------------------------------------------
ASGI_APPLICATION = 'config.asgi.application'

# Allowed hosts
# ------------------------------------------------------------------------------

ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['*'])
CSRF_TRUSTED_ORIGINS = env.list(
    'CSRF_TRUSTED_ORIGINS',
    default=['http://localhost']
)

# APPS
# ------------------------------------------------------------------------------

DJANGO_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'crispy_forms',
    'crispy_bootstrap5',
    'django_celery_beat',
]

LOCAL_APPS = [
    'apps.users'
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS + THIRD_PARTY_APPS

# Middleware
# ------------------------------------------------------------------------------

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
# Templates
# ------------------------------------------------------------------------------

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [str(APPS_DIR / "templates")],
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

FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

CRISPY_TEMPLATE_PACK = "bootstrap5"
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

# Database
# ------------------------------------------------------------------------------

DATABASES = {'default': env.db("DATABASE_URL")}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# AUTHENTICATION
# ------------------------------------------------------------------------------

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_USER_MODEL = "users.User"

# Password validation
# ------------------------------------------------------------------------------

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

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
# ------------------------------------------------------------------------------

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Asia/Bishkek'

USE_I18N = True

USE_TZ = True

# STATIC
# ------------------------------------------------------------------------------

STATIC_ROOT = str(BASE_DIR / "staticfiles")

STATIC_URL = "/static/"

STATICFILES_DIRS = [str(APPS_DIR / "static")]

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880

# MEDIA
# ------------------------------------------------------------------------------

MEDIA_ROOT = str(BASE_DIR / "mediafiles")

MEDIA_URL = "/media/"

# Redis
# ------------------------------------------------------------------------------

REDIS_URL = env("REDIS_URL", default="redis://redis:6379/0")
REDIS_SSL = REDIS_URL.startswith("rediss://")

# CACHES
# ------------------------------------------------------------------------------
SESSION_ENGINE = "django.contrib.sessions.backends.cache"


CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,
        },
    },
}

# Celery
# ------------------------------------------------------------------------------

if USE_TZ:
    CELERY_TIMEZONE = TIME_ZONE

CELERY_BROKER_URL = REDIS_URL

CELERY_RESULT_BACKEND = REDIS_URL

CELERY_RESULT_EXTENDED = True

CELERY_RESULT_BACKEND_ALWAYS_RETRY = True

CELERY_RESULT_BACKEND_MAX_RETRIES = 10

CELERY_ACCEPT_CONTENT = ["json"]

CELERY_TASK_SERIALIZER = "json"

CELERY_RESULT_SERIALIZER = "json"

CELERY_TASK_TIME_LIMIT = 5 * 60

CELERY_TASK_SOFT_TIME_LIMIT = 60

CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

CELERY_WORKER_SEND_TASK_EVENTS = True

CELERY_TASK_SEND_SENT_EVENT = True

CELERY_WORKER_HIJACK_ROOT_LOGGER = False

# Jazzmin
# ------------------------------------------------------------------------------

JAZZMIN_SETTINGS = {
    # title of the window (Will default to current_admin_site.site_title if absent or None)
    "site_title": "AIS 'Class Schedule'",

    # Title on the login screen (19 chars max) (defaults to current_admin_site.site_header if absent or None)
    "site_header": "AIS 'Class Schedule'",

    # Title on the brand (19 chars max) (defaults to current_admin_site.site_header if absent or None)
    "site_brand": "AIS 'Class Schedule'",

    # Logo to use for your site, must be present in static files, used for brand on top left
    "site_logo": "img/logo.png",

    # Logo to use for your site, must be present in static files, used for login form logo (defaults to site_logo)
    "login_logo": None,

    # Logo to use for login form in dark themes (defaults to login_logo)
    "login_logo_dark": None,

    # CSS classes that are applied to the logo above
    "site_logo_classes": "img-circle",

    # Relative path to a favicon for your site, will default to site_logo if absent (ideally 32x32 px)
    "site_icon": None,

    # Welcome text on the login screen
    "welcome_sign": "Welcome to the AIS 'Class Schedule'",

    # Copyright on the footer
    "copyright": "Acme AIS 'Class Schedule' Ltd",

    # List of model admins to search from the search bar, search bar omitted if excluded
    # If you want to use a single search field you dont need to use a list, you can use a simple string 
    "search_model": ["auth.User", "auth.Group"],

    # Field name on user model that contains avatar ImageField/URLField/Charfield or a callable that receives the user
    "user_avatar": None,

    ############
    # Top Menu #
    ############

    # Links to put along the top menu
    "topmenu_links": [

        # Url that gets reversed (Permissions can be added)
        {"name": "Home",  "url": "admin:index", "permissions": ["auth.view_user"]},

        # model admin to link to (Permissions checked against model)
        {"model": "auth.User"},

    ],

    #############
    # User Menu #
    #############

    # Additional links to include in the user menu on the top right ("app" url type is not allowed)
    "usermenu_links": [
        {"name": "Support", "url": "https://github.com/farridav/django-jazzmin/issues", "new_window": True},
        {"model": "auth.user"}
    ],

    #############
    # Side Menu #
    #############

    # Whether to display the side menu
    "show_sidebar": True,

    # Whether to aut expand the menu
    "navigation_expanded": True,

    # Hide these apps when generating side menu e.g (auth)
    "hide_apps": [],

    # Hide these models when generating side menu (e.g auth.user)
    "hide_models": [],

    # List of apps (and/or models) to base side menu ordering off of (does not need to contain all apps/models)
    "order_with_respect_to": ["auth",],

    # Custom links to append to app groups, keyed on app name
    "custom_links": {},

    # Custom icons for side menu apps/models See https://fontawesome.com/icons?d=gallery&m=free&v=5.0.0,5.0.1,5.0.10,5.0.11,5.0.12,5.0.13,5.0.2,5.0.3,5.0.4,5.0.5,5.0.6,5.0.7,5.0.8,5.0.9,5.1.0,5.1.1,5.2.0,5.3.0,5.3.1,5.4.0,5.4.1,5.4.2,5.13.0,5.12.0,5.11.2,5.11.1,5.10.0,5.9.0,5.8.2,5.8.1,5.7.2,5.7.1,5.7.0,5.6.3,5.5.0,5.4.2
    # for the full list of 5.13.0 free icon classes
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
    },
    # Icons that are used when one is not manually specified
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",

    #################
    # Related Modal #
    #################
    # Use modals instead of popups
    "related_modal_active": False,

    #############
    # UI Tweaks #
    #############
    # Relative paths to custom CSS/JS scripts (must be present in static files)
    "custom_css": None,
    "custom_js": None,
    # Whether to link font from fonts.googleapis.com (use custom_css to supply font otherwise)
    "use_google_fonts_cdn": True,
    # Whether to show the UI customizer on the sidebar
    "show_ui_builder": False,

    ###############
    # Change view #
    ###############
    # Render out the change view as a single form, or in tabs, current options are
    # - single
    # - horizontal_tabs (default)
    # - vertical_tabs
    # - collapsible
    # - carousel
    "changeform_format": "horizontal_tabs",
    # override change forms on a per modeladmin basis
    "changeform_format_overrides": {"auth.user": "collapsible", "auth.group": "vertical_tabs"},
    # Add a language dropdown into the admin
    "language_chooser": True,
}