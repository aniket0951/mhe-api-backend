import datetime
import os

import environ

root = environ.Path(__file__) - 2
# set default values and casting
env = environ.Env(DEBUG=(bool, False),)
# reading .env file
environ.Env.read_env('.env')


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('DJANGO_SECRET_KEY')
AWS_ACCESS_KEY = env('ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = env('SECRET_KEY')
AWS_SNS_TOPIC_NAME = env('SNS_TOPIC_NAME')
AWS_SNS_TOPIC_REGION = env('SNS_TOPIC_REGION')
AWS_SNS_Topic_ARN = env('SNS_Topic_ARN')
AWS_S3_BUCKET_NAME = env('S3_BUCKET_NAME')
AWS_S3_REGION_NAME = env('S3_REGION_NAME')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
"""
env('DEBUG')
"""

ALLOWED_HOSTS = ['*']


# Application definition


INBUILT_APPS = [
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
]

CUSTOM_APPS = [
    'apps.meta_app',
    'apps.users',
    'apps.patients',
    'apps.master_data',
    'apps.health_packages',
    'apps.health_tests',
    'apps.doctors',
    'apps.appointments',
    'apps.manipal_admin'
]

THIRD_PARTY_APPS = [
    'phonenumber_field',

]

# Application definition

INSTALLED_APPS = INBUILT_APPS + THIRD_PARTY_APPS + CUSTOM_APPS

# Created USER MODEL for authorisation
AUTH_USER_MODEL = 'users.BaseUser'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

DEFAULT_MIDDLEWARES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


CREATED_MIDDLEWARES = [
    'corsheaders.middleware.CorsMiddleware',
]

MIDDLEWARE = CREATED_MIDDLEWARES + DEFAULT_MIDDLEWARES


ROOT_URLCONF = 'manipal_api.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'manipal_api.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
# Database (Postgresql) Settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('MANIPAL_DB_NAME'),
        'USER': env('MANIPAL_DB_USER'),
        'PASSWORD': env('MANIPAL_DB_USER_PASSWORD'),
        'HOST': env('MANIPAL_DB_HOST'),
        'PORT': env('MANIPAL_DB_PORT'),

    }
}

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

JWT_AUTH = {
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_EXPIRATION_DELTA': datetime.timedelta(days=90),
    'JWT_ALLOW_REFRESH': True,
    'JWT_REFRESH_EXPIRATION_DELTA': datetime.timedelta(days=90),
}

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        # 'rest_framework.authentication.SessionAuthentication',
        # 'rest_framework.authentication.BasicAuthentication',
    ),
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'

#  Created setting, hosts that are allowed to do cross-site requests
CORS_ORIGIN_ALLOW_ALL = True
