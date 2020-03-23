import ast
import datetime
import os

import environ

import boto3
from boto3 import session as boto3_session

root = environ.Path(__file__) - 2
# set default values and casting
env = environ.Env(DEBUG=(bool, True),)
# reading .env file
environ.Env.read_env('.env')


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('DJANGO_SECRET_KEY')

AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME')  # e.g. us-east-2
AWS_DEFAULT_ACL = 'private'
AWS_S3_ENCRYPTION = env('AWS_S3_ENCRYPTION')

# Tell django-storages the domain to use to refer to static files.
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}


# AWS S3 Bucket client and session
S3_SESSION = boto3_session.Session(region_name=AWS_S3_REGION_NAME)
S3_CLIENT = S3_SESSION.client(
    's3', config=boto3_session.Config(signature_version='s3v4'))


# AWS SNS Settings
AWS_SNS_CLIENT = boto3.client(
    "sns",
    aws_access_key_id=env('AWS_SNS_ACCESS_KEY_ID'),
    aws_secret_access_key=env('AWS_SNS_SECRET_ACCESS_KEY'),
    region_name=env('AWS_SNS_REGION_NAME')
)
AWS_SNS_CLIENT.set_sms_attributes(
    attributes={
        'DefaultSMSType': 'Transactional'
    }
)


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = ['*']


# Application definition
INBUILT_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
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
    'apps.manipal_admin',
    'apps.lab_and_radiology_items',
    'apps.payments',
    'apps.patient_registration',
    'apps.personal_documents',
    'apps.cart_items',
    'apps.reports',
    'apps.dashboard',


]

THIRD_PARTY_APPS = [
    'corsheaders',
    'rest_framework',
    'django_filters',
    'phonenumber_field',
    'import_export',
    'django_extensions',
    'django.contrib.gis'
]

# Application definition
INSTALLED_APPS = INBUILT_APPS + THIRD_PARTY_APPS + CUSTOM_APPS

# Created USER MODEL for authorisation
AUTH_USER_MODEL = 'users.BaseUser'

AUTHENTICATION_BACKENDS = (
    # 'django.contrib.auth.backends.ModelBackend',
    'utils.custom_authentication.CustomPatientAuthBackend',

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


# Database (Postgresql) Settings
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': env('MANIPAL_DB_NAME'),
        'USER': env('MANIPAL_DB_USER'),
        'PASSWORD': env('MANIPAL_DB_USER_PASSWORD'),
        'HOST': env('MANIPAL_DB_HOST'),
        'PORT': env('MANIPAL_DB_PORT'),

    }
}

# Password validation
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
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Created setting, JWT authentication
JWT_AUTH = {
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_EXPIRATION_DELTA': datetime.timedelta(days=90),
    'JWT_ALLOW_REFRESH': True,
    'JWT_REFRESH_EXPIRATION_DELTA': datetime.timedelta(days=90),
}


# Created setting, all the global settings for a REST framework API
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
    ),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.AcceptHeaderVersioning',
    'ALLOWED_VERSIONS': ['1.0', '2.0'],
    'DEFAULT_VERSION': '1.0',
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'utils.pagination.CustomPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'utils.custom_jwt_authentication.JSONWebTokenAuthentication',
    ),
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'EXCEPTION_HANDLER': 'utils.exception_handler.custom_exception_handler',
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/
STATIC_URL = '/static/'


#  Created setting, hosts that are allowed to do cross-site requests
CORS_ORIGIN_ALLOW_ALL = True


# Manipal Proxy API settings
MANIPAL_API_URL = env('MANIPAL_API_URL')

REST_PROXY = {

    'HOST': MANIPAL_API_URL,
    # 'AUTH': {
    #     'user': PROCESS_ENGINE_USER,
    #     'password': PROCESS_ENGINE_PASSWORD,
    #     # Or alternatively:
    #     'token': '',
    # },
    'TIMEOUT': None,
    'DEFAULT_HTTP_ACCEPT': 'application/json',
    'DEFAULT_HTTP_ACCEPT_LANGUAGE': 'en-US,en;q=0.8',
    'DEFAULT_CONTENT_TYPE': 'application/xml',

    # Return response as-is if enabled
    'RETURN_RAW': False,

    # Used to translate Accept HTTP field
    'ACCEPT_MAPS': {
        'text/html': 'application/json',
    },

    # Do not pass following parameters
    'DISALLOWED_PARAMS': ('format',),

    # Perform a SSL Cert Verification on URI requests are being proxied to
    'VERIFY_SSL': False,
}


# MAX_FILE_UPLOAD_SIZE IN MB
MAX_FILE_UPLOAD_SIZE = int(env('MAX_FILE_UPLOAD_SIZE_IN_MB'))

# Supported File Extensions
VALID_IMAGE_FILE_EXTENSIONS = ast.literal_eval(
    env('VALID_IMAGE_FILE_EXTENSIONS'))
VALID_FILE_EXTENSIONS = ast.literal_eval(env('VALID_FILE_EXTENSIONS'))

SMS_SENDER = env('SMS_SENDER')

OTP_EXPIRATION_TIME = env('OTP_EXPIRATION_TIME')


OTP_EXPIRATION_TIME

#  User OTP expiration time in seconds
OTP_EXPIRATION_TIME = env('OTP_EXPIRATION_TIME')

ANDROID_SMS_RETRIEVER_API_KEY = env('ANDROID_SMS_RETRIEVER_API_KEY')

SALUCRO_AUTH_USER = env('SALUCRO_AUTH_USER')
SALUCRO_AUTH_KEY = env('SALUCRO_AUTH_KEY')
SALUCRO_USERNAME = env('SALUCRO_USERNAME')
SALUCRO_RESPONSE_URL = env('SALUCRO_RESPONSE_URL')
SALUCRO_RETURN_URL = env('SALUCRO_RETURN_URL')
SALUCRO_MID = env('SALUCRO_MID')
SALUCRO_SECRET_KEY = env('SALUCRO_SECRET_KEY')
PATIENT_PROFILE_SYNC_API = env('PATIENT_PROFILE_SYNC_API')
REDIRECT_URL= env('REDIRECT_URL')
