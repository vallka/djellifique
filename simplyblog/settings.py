"""
Django settings for simplyblog project.

Generated by 'django-admin startproject' using Django 3.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
#BASE_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))



# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '$6#)l_2$c8y=tp)=mrl9+znqa&=_$r1zteeg+3vdtxdldtgjd('

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'blog',
    'prestashop',
    'newsletter',
    'gellifinsta',
    'gellifihouse',
    'ups',
    'dhl',
    'stats',
    'pos',
    'gtranslator',
    #'chatbot',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'debug_toolbar',
    'markdownx',
    'django_extensions',

    'rest_framework',
    'rest_framework.authtoken',
    'drf_yasg',
    'corsheaders',
    'django.contrib.sites',
    'django.contrib.sitemaps',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    #'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    #'simplyblog.autologin.AutoLoginMiddleware',
]


ROOT_URLCONF = 'simplyblog.urls'

TEMPLATES = [
    {
        'BACKEND':'django.template.backends.jinja2.Jinja2',
        'DIRS': [os.path.join(BASE_DIR, 'templates-jinja2')],
        'APP_DIRS': True,
        'OPTIONS': {
            'extensions': [
                #'jdj_tags.extensions.DjangoCompat',
            ],
            "environment": "simplyblog.jinja2.JinjaEnvironment",
        },
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

#TEMPLATE_SKIN = 'gellifique'
TEMPLATE_SKIN = 'vallka'

WSGI_APPLICATION = 'simplyblog.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    },
    'presta': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db-presta.sqlite3'),
    },
    'presta-testa': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db-presta-testa.sqlite3'),
    },
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'dj',
        'USER': 'gellifique',
        'PASSWORD': os.environ['POLLS_DB_PASSWORD'],
        'HOST': '127.0.0.1',
        'OPTIONS': {'charset': 'utf8mb4'},
    },
    'presta': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'gellifique_new',
        'USER': 'gellifique',
        'PASSWORD': os.environ['POLLS_DB_PASSWORD'],
        'HOST': '127.0.0.1',
        'OPTIONS': {'charset': 'utf8mb4'},
    },
    'presta_eu': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'gellifique_eu',
        'USER': 'gellifique',
        'PASSWORD': os.environ['POLLS_DB_PASSWORD'],
        'HOST': '127.0.0.1',
        'OPTIONS': {'charset': 'utf8mb4'},
    },
}  

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.1/topics/i18n/
LANGUAGE_CODE = 'en'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('en','English'),
    ('es','Spanish'),
    ('de','German'),
    ('fr','French'),
    ('pt','Portuguese'),
    ('pl','Polish'),
    ('ro','Romanian'),
    ('it','Italien'),
    ('uk','Ukrainian'),
]


LOGIN_URL = '/admin/login/'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static")
]
#STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

DATA_UPLOAD_MAX_MEMORY_SIZE = 26214400 
FILE_UPLOAD_MAX_MEMORY_SIZE = 26214400
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000


from datetime import datetime

MARKDOWNX_MEDIA_PATH = datetime.now().strftime('markdownx/%Y/%m/%d')
MARKDOWNX_IMAGE_MAX_SIZE = { 'size': (1500, 1500), 'quality': 80 }
MARKDOWNX_MARKDOWN_EXTENSIONS = [
    'tables','attr_list','fenced_code','md_in_html','nl2br','wikilinks','footnotes',
]


#EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = 'sent-emails' # change this to a proper location

EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = os.environ.get('EMAIL_PORT')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
#EMAIL_TIMEOUT
#EMAIL_SSL_KEYFILE
#EMAIL_SSL_CERTFILE

EMAIL_FROM_USER = "info@vallka.com"
EMAIL_BCC_TO = None

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',  
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
}

CORS_ALLOW_ALL_ORIGINS = True
#SECURE_REFERRER_POLICY = 'unsafe-url'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'incremental': True,
    'root': {
        'level': 'DEBUG',
    },
}

#INTERNAL_IPS = ['127.0.0.1','90.253.213.37','87.74.96.146']
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

#sentry_sdk.init(
#    environment="dev",
#    dsn="https://235ef220fc8e4f9793858eacb15a542d@o480612.ingest.sentry.io/5528028",
#    integrations=[DjangoIntegration()],
#    traces_sample_rate=1.0,
#
#    # If you wish to associate users to errors (assuming you are using
#    # django.contrib.auth) you may enable sending PII data.
#    send_default_pii=True
#)
