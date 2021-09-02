import ast
import datetime
import os

import environ
from django.utils.log import DEFAULT_LOGGING

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
API_SECRET_KEY = env('API_SECRET_KEY')

APNS_ENDPOINT=env('APNS_ENDPOINT')
APNS_USE_SANDBOX= True if env("APNS_USE_SANDBOX") and str(env("APNS_USE_SANDBOX"))=="True" else False
APNS_CERT_PATH=os.path.join(BASE_DIR, env('APNS_CERT_PATH'))
APNS_KEY_ID = env("APNS_KEY_ID")
BUNDLE_ID = env("BUNDLE_ID")
TEAM_ID = env("TEAM_ID")
APNS_SOUND=env('APNS_SOUND')


AWS_ACCESS_KEY_ID = None  # Set to None to use IAM role
AWS_SECRET_ACCESS_KEY = None  # Set to None to use IAM role
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
    aws_access_key_id=None,
    aws_secret_access_key=None,
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
    'apps.video_conferences',
    'apps.notifications.apps.NotificationsConfig',
    'apps.discharge_summaries',
    'apps.additional_features',
    'apps.middleware'
]

THIRD_PARTY_APPS = [
    'corsheaders',
    'rest_framework',
    'django_filters',
    'phonenumber_field',
    'import_export',
    'django_extensions',
    'django.contrib.gis',
    'django_clamd',
    'fcm_django',
    'axes'
]

# Application definition
INSTALLED_APPS = INBUILT_APPS + THIRD_PARTY_APPS + CUSTOM_APPS

# Created USER MODEL for authorisation
AUTH_USER_MODEL = 'users.BaseUser'

AUTHENTICATION_BACKENDS = (
    # 'django.contrib.auth.backends.ModelBackend',
    'axes.backends.AxesBackend',
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
    'axes.middleware.AxesMiddleware',
    'apps.middleware.cipherMiddleware.CipherRequestMiddleware',
    'apps.middleware.cipherMiddleware.CipherResponseMiddleware'
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
    # 'read_db': {
    #     'ENGINE': 'django.contrib.gis.db.backends.postgis',
    #     'NAME': env('MANIPAL_READ_DB_NAME'),
    #     'USER': env('MANIPAL_READ_DB_USER'),
    #     'PASSWORD': env('MANIPAL_READ_DB_USER_PASSWORD'),
    #     'HOST': env('MANIPAL_READ_DB_HOST'),
    #     'PORT': env('MANIPAL_READ_DB_PORT'),

    # }
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

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_L10N = True

USE_TZ = False

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
MANIPAL_API_TIMEOUT = None

try:
    MANIPAL_API_TIMEOUT = int(env('MANIPAL_API_TIMEOUT'))
except Exception as error:
    pass

REST_PROXY = {

    'HOST': MANIPAL_API_URL,
    # 'AUTH': {
    #     'user': PROCESS_ENGINE_USER,
    #     'password': PROCESS_ENGINE_PASSWORD,
    #     # Or alternatively:
    #     'token': '',
    # },
    'TIMEOUT': MANIPAL_API_TIMEOUT if MANIPAL_API_TIMEOUT and MANIPAL_API_TIMEOUT>0 else None,
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
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_FILE_UPLOAD_SIZE * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = FILE_UPLOAD_MAX_MEMORY_SIZE
# Supported File Extensions
VALID_IMAGE_FILE_EXTENSIONS = ast.literal_eval(env('VALID_IMAGE_FILE_EXTENSIONS'))
VALID_FILE_EXTENSIONS = ast.literal_eval(env('VALID_FILE_EXTENSIONS'))

SMS_SENDER = env('SMS_SENDER')

#  User OTP expiration time in seconds
OTP_EXPIRATION_TIME = env('OTP_EXPIRATION_TIME')
OTP_LENGTH = 6
try:
    OTP_LENGTH = int(env('OTP_LENGTH'))
except Exception as error:
    pass

MAX_FAMILY_MEMBER_COUNT = env('MAX_FAMILY_MEMBER_COUNT')

FCM_DJANGO_SETTINGS = {
    "FCM_SERVER_KEY": env('FCM_SERVER_KEY')
}
FCM_API_KEY = env('FCM_API_KEY')


ANDROID_SMS_RETRIEVER_API_KEY = env('ANDROID_SMS_RETRIEVER_API_KEY')

SALUCRO_AUTH_USER = env('SALUCRO_AUTH_USER')
SALUCRO_AUTH_KEY = env('SALUCRO_AUTH_KEY')
SALUCRO_USERNAME = env('SALUCRO_USERNAME')
SALUCRO_RESPONSE_URL = env('SALUCRO_RESPONSE_URL')
SALUCRO_RETURN_URL = env('SALUCRO_RETURN_URL')
SALUCRO_MID = env('SALUCRO_MID')
SALUCRO_SECRET_KEY = env('SALUCRO_SECRET_KEY')
PATIENT_PROFILE_SYNC_API = env('PATIENT_PROFILE_SYNC_API')
REDIRECT_URL = env('REDIRECT_URL')
REFUND_URL = env('REFUND_URL')
VC_URL_REDIRECTION = env('VC_URL_REDIRECTION')
SMS_SECRET_KEY = env('SMS_SECRET_KEY')

WEBSITE = env('WEBSITE')

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_FROM_USER = env('EMAIL_FROM_USER')
EMAIL_HOST = env('AWS_SES_REGION_ENDPOINT')
EMAIL_HOST_USER = env('AWS_SES_ACCESS_KEY_ID')
EMAIL_HOST_PASSWORD = env('AWS_SES_SECRET_ACCESS_KEY')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_USE_TLS = True

# Celery settings
CELERY_BROKER_URL = "sqs://"
CELERY_RESULT_BACKEND = None
CELERY_TASK_DEFAULT_QUEUE = env('CELERY_TASK_DEFAULT_QUEUE')
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'region': 'ap-south-1',
}
CELERY_TIMEZONE = 'Asia/Kolkata'

TWILIO_ACCOUNT_SID = env('TWILIO_ACCOUNT_SID')
TWILIO_ACCOUNT_AUTH_KEY = env('TWILIO_ACCOUNT_AUTH_KEY')
TWILIO_API_KEY_SID = env('TWILIO_API_KEY_SID')
TWILIO_API_KEY_SECRET = env('TWILIO_API_KEY_SECRET')
TWILIO_CHAT_SERVICE_ID = env('TWILIO_CHAT_SERVICE_ID')
TWILIO_SYNC_SERVICE_ID = env('TWILIO_CHAT_SERVICE_ID')

DOCTOR_PROFILE_USERNAME = env('DOCTOR_PROFILE_USERNAME')
DOCTOR_PROFILE_PASSWORD = env('DOCTOR_PROFILE_PASSWORD')
IOS_VERSION = env('IOS_VERSION')
FORCE_UPDATE_ENABLE = env('FORCE_UPDATE_ENABLE')
HEALTH_PACKAGE_UPDATE_API= env('HEALTH_PACKAGE_UPDATE_API')
HEALTH_PACKAGE_UPDATE_USER = env('HEALTH_PACKAGE_UPDATE_USER')
HEALTH_PACKAGE_UPDATE_PASSWORD = env('HEALTH_PACKAGE_UPDATE_PASSWORD')

FEEDBACK_NOTIFICATION_EMAIL_SUBJECT=env("FEEDBACK_NOTIFICATION_EMAIL_SUBJECT")

RAZOR_APP_TITLE=env("RAZOR_APP_TITLE")
RAZOR_APP_VERSION=env("RAZOR_APP_VERSION")
RAZOR_PAYMENT_CURRENCY=env("RAZOR_PAYMENT_CURRENCY")
RAZOR_AMOUNT_OFFSET=env("RAZOR_AMOUNT_OFFSET")

AXES_FAILURE_LIMIT=3
AXES_COOLOFF_TIME = datetime.timedelta(minutes=10)
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True

JWT_AUTHORIZATION_KEY = env("JWT_AUTHORIZATION_KEY")
ENCRYPTION_ENABLED= True if env("ENCRYPTION_ENABLED") and str(env("ENCRYPTION_ENABLED"))=="True" else False
ENCRYPTION_FLAG = env("ENCRYPTION_FLAG")
ENCRYPTION_KEYWORD = env("ENCRYPTION_KEYWORD")
ENCRYPTION_KEYWORD_LENGTH = env("ENCRYPTION_KEYWORD_LENGTH")
ENCRYPTION_BODY_KEY = env("ENCRYPTION_BODY_KEY")
STRICTLY_ENCRYPTED = env("STRICTLY_ENCRYPTED").split(",") if env("STRICTLY_ENCRYPTED") else []

RATELIMIT_KEY_IP = env("RATELIMIT_KEY_IP")
RATELIMIT_KEY_USER_OR_IP = env("RATELIMIT_KEY_USER_OR_IP")
RATELIMIT_DOCUMENT_UPLOAD = env("RATELIMIT_DOCUMENT_UPLOAD")
RATELIMIT_OTP_GENERATION = env("RATELIMIT_OTP_GENERATION")

HARDCODED_MOBILE_NO = env("HARDCODED_MOBILE_NO")
HARDCODED_MOBILE_OTP = env("HARDCODED_MOBILE_OTP")

WRONG_OTP_ATTEMPT_ERROR = env("WRONG_OTP_ATTEMPT_ERROR")
MAX_WRONG_OTP_ATTEMPT_ERROR = env("MAX_WRONG_OTP_ATTEMPT_ERROR")

CLAMD_ENABLED = True if env("CLAMD_ENABLED")=="True" else False
COVID_SERVICE = env("COVID_SERVICE")
COVID_SUB_SERVICE_DOSE1 = env("COVID_SUB_SERVICE_DOSE1")
COVID_SUB_SERVICE_DOSE2 = env("COVID_SUB_SERVICE_DOSE2")
 
MIN_VACCINATION_AGE = 0
try:
    MIN_VACCINATION_AGE = int(env("MIN_VACCINATION_AGE"))
except Exception as e:
    pass
VACCINATION_AGE_ERROR_MESSAGE = env("VACCINATION_AGE_ERROR_MESSAGE")
COVID_BOOTH_IMAGE = env("COVID_BOOTH_IMAGE")

DELETE_ACCOUNT_API = True if env("DELETE_ACCOUNT_API")=="True" else False

SKEY = env('SKEY')
MID = env('MID')

MANIPAL_WHATSAPP_CONTACT = env('MANIPAL_WHATSAPP_CONTACT')

FLYER_ENABLED = True if env("FLYER_ENABLED") and str(env("FLYER_ENABLED"))=="True" else False

MAX_FLYER_IMAGES = env('MAX_FLYER_IMAGES')

BIRTHDAY_NOTIFICATION_IMAGE_URL = env("BIRTHDAY_NOTIFICATION_IMAGE_URL")

ENVIRONMENT = env("ENVIRONMENT")

# Logger configuration
LOGGING = {
    'version': 1,
    'disable_existing_logger': False,
    'formatters': {
        'simple': {
            'format': '%(levelname)s -- %(message)s'
        },
        'standard': {
            'format': '[%(asctime)s] -- %(name)s: --  %(levelname)s: --  %(msg)s'
        },
        'request_log': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '{server_time} -- {message}',
            'style': '{',
        },
        'generic': {
            'format': '%(asctime)s -- [%(process)d] --  [%(levelname)s] --  %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            '()': 'logging.Formatter',
        },
        'django.server': DEFAULT_LOGGING['formatters']['django.server'],
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file_handler': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.log',
            'maxBytes': FILE_UPLOAD_MAX_MEMORY_SIZE*4,  # 5 MB
            'backupCount': 10,
            'formatter': 'standard'
        },
        'console_handler': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stderr',
            'formatter': 'standard'
        },
        'django_server_console': {
            'class': 'logging.StreamHandler',
            'formatter': 'django.server',
            'level': 'INFO'
        },
        'django_server_file': {
            'formatter': 'django.server',
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.log',
            'maxBytes': FILE_UPLOAD_MAX_MEMORY_SIZE*4,   # 5 MB
            'backupCount': 10,
        },
        'django_request_console': {
            'class': 'logging.StreamHandler',
            'formatter': 'request_log',
            'level': 'INFO'
        },
        'django_request_file': {
            'formatter': 'request_log',
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/requests.log',
            'maxBytes': FILE_UPLOAD_MAX_MEMORY_SIZE*4,  # 5 MB
            'backupCount': 5,
        },
        'error_file': {
            'class': 'logging.FileHandler',
            'formatter': 'generic',
            'filename': 'logs/gunicorn_error.log',
        },
        'access_file': {
            'class': 'logging.FileHandler',
            'formatter': 'generic',
            'filename': 'logs/gunicorn_access.log',
        },
    },
    # 'root': {
    #     'handlers': ['file_handler', 'console_handler'],
    #     'level': 'INFO',
    # },
    'loggers': {
        'django': {
            'propagate': False,
            'handlers': ['file_handler', 'console_handler'],
            'level': 'INFO',
        },
        'django.request': {
            'propagate': False,
            'handlers': ['django_request_console', 'django_request_file'],
            'level': 'INFO'
        },
        'django.server':  {
            'handlers': ['django_server_console', 'django_server_file'],
            'propagate': False,
            'level': 'INFO',
        },
        'gunicorn.error': {
            'level': 'DEBUG',
            'handlers': ['error_file'],
            'propagate': True,
        },
        'gunicorn.access': {
            'level': 'DEBUG',
            'handlers': ['access_file'],
            'propagate': True,
        },
    }
}

