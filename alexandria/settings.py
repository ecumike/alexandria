"""
Django settings for alexandria project.

Generated by 'django-admin startproject' using Django 4.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os

SETTINGS_PATH = os.path.normpath(os.path.dirname(__file__))

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/


# Replace the key with a generated one from Django, 
#  like 'm*@%pn4cx015)ynyk54$y41z*1o4*@-whe6s%pkd@%%cbv7d3l'
SECRET_KEY = 'REPLACE_ME'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG_FLAG', False)

ALLOWED_HOSTS = [
	'localhost',
	'127.0.0.1',
]

INTERNAL_IPS = ['127.0.0.1',]

# Application definition

INSTALLED_APPS = [
	'django.contrib.admin',
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.messages',
	'django.contrib.staticfiles',
	'django.contrib.humanize',
	'django_extensions',
	'compat',
	'django.contrib.admindocs',
	'hijack_admin',
	'hijack',
	'request',
	'storages',
	'research',
	'metrics',
	'info',
]

MIDDLEWARE = [
	#'login_required_middleware.LoginRequiredMiddleware',
	'django.middleware.security.SecurityMiddleware',
	'whitenoise.middleware.WhiteNoiseMiddleware',
	'django.middleware.gzip.GZipMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.common.CommonMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'request.middleware.RequestMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'alexandria.urls'

if DEBUG:
	MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')
	INSTALLED_APPS.append('debug_toolbar')
	

TEMPLATES = [
	{
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'DIRS': [
			'templates',
			'research/templates',
			'metrics/templates',
			'info/templates',
		],
		'APP_DIRS': True,
		'OPTIONS': {
			'context_processors': [
				'alexandria.context_processors.app_settings',
				'django.template.context_processors.debug',
				'django.template.context_processors.request',
				'django.contrib.auth.context_processors.auth',
				'django.contrib.messages.context_processors.messages',
			],
			'libraries': {
				'common_templatetags': 'templatetags.common_templatetags'	
			},
		},
	},
]


WSGI_APPLICATION = 'alexandria.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.postgresql',
		'NAME': os.getenv('DJANGO_DB_NAME', 'alexandria'),
		'USER': os.getenv('DJANGO_DB_USER', ''),
		'PASSWORD': os.getenv('DJANGO_DB_PASSWORD', ''),
		'HOST': os.getenv('DJANGO_DB_HOST', 'localhost'),
		'PORT': os.getenv('DJANGO_DB_PORT', 5432),
	}
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/New_York'

USE_I18N = True

USE_L10N = True

USE_TZ = True

ADMINS = []
MANAGERS = ADMINS
SERVER_EMAIL = ' surveykong-error@somedomain.com'
# EMAIL_HOST = 'smtp.sendgrid.net'
# EMAIL_HOST_USER = 'apikey'
# EMAIL_HOST_PASSWORD = os.getenv('SENDGRID_API_KEY', '')
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

# OPTIONAL. 
# This overrides the default memory vs. file storage handling.
# Here we force file storage so we can simply point to the temp file path to upload to COS.
FILE_UPLOAD_HANDLERS = ['django.core.files.uploadhandler.TemporaryFileUploadHandler']

STATIC_ROOT = os.path.join(BASE_DIR, 'static-deploy/')

STATICFILES_DIRS = [
	os.path.join(BASE_DIR, "static/"),
]

STATIC_URL = os.getenv('DJANGO_STATIC_URL', '/static-alexandria/')
MEDIA_URL = os.getenv('DJANGO_MEDIA_URL', '/media/')

# COS vars. Used for static files and COS API lib.
# Static file storage package uses AWS VAR names/alias below with common vars.
# COS lib uses dedicated COS and bucket for uploads.
COS_ACCESS_KEY_ID=os.getenv('COS_ACCESS_KEY_ID','')
COS_API_KEY_ID=os.getenv('COS_API_KEY_ID','')
COS_AUTH_ENDPOINT=os.getenv('COS_AUTH_ENDPOINT','')
COS_BUCKET_LOCATION=os.getenv('COS_BUCKET_LOCATION','')
COS_BUCKET_NAME=os.getenv('COS_BUCKET_NAME','')
COS_CDN_DOMAIN=os.getenv('COS_CDN_DOMAIN','')
COS_ENDPOINT=os.getenv('COS_ENDPOINT','')
COS_RESOURCE_CRN=os.getenv('COS_RESOURCE_CRN','')
COS_SECRET_ACCESS_KEY=os.getenv('COS_SECRET_ACCESS_KEY','')

# This is to use COS instead of local app storage directory for STATIC files AWS package.
# Common lines here, just change last 2 as noted.
AWS_ACCESS_KEY_ID = COS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = COS_SECRET_ACCESS_KEY
AWS_S3_HOST = COS_AUTH_ENDPOINT
AWS_S3_ENDPOINT_URL = COS_ENDPOINT
AWS_LOCATION = 'static'
AWS_QUERYSTRING_AUTH = False
AWS_DEFAULT_ACL = 'public-read'
AWS_STORAGE_BUCKET_NAME = COS_BUCKET_NAME
AWS_S3_CUSTOM_DOMAIN = COS_CDN_DOMAIN


# UPLOADS
# These are used for uploads, via COS lib. 
# This should be a different COS instance or bucket than static files 
#  to separate uploads from app static files. 
COS_UPLOADS_BUCKET_NAME='researchfiles'
COS_UPLOADS_API_KEY_ID=os.getenv('COS_UPLOADS_API_KEY_ID','')
COS_UPLOADS_RESOURCE_CRN=os.getenv('COS_UPLOADS_RESOURCE_CRN','')


# In DEBUG mode. static are served with this. 
# At bottom of this file is production (non-DEBUG) setting to use COS storage and locations.
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# 1 year session cookie TTL.
SESSION_COOKIE_AGE = 31536000
SESSION_COOKIE_SAMESITE = False
SESSION_COOKIE_SECURE = True


## Note: No custom sign-in/out URL go here. All done via normal app URL and views.

## Django first allows easy dev access via Django and wont error on LDAP for a local user/dev testing.
AUTHENTICATION_BACKENDS = [
	'django.contrib.auth.backends.ModelBackend',
]

## This is used when a view requires authentication and needs to redirect the user to the sigin-in page.
LOGIN_URL = '/research/signin/'
LOGIN_REDIRECT_URL = '/'

LDAP_URL = ''

SLACK_ALERT_URL = os.getenv('DJANGO_SLACK_ALERT_URL', '')
SLACK_OMNIA_NOTIFICATIONS_URL = os.getenv('SLACK_OMNIA_NOTIFICATIONS_URL', '')

HIJACK_ALLOW_GET_REQUESTS = True
HIJACK_LOGIN_REDIRECT_URL = '/'	 # Where admins are redirected to after hijacking a user
HIJACK_LOGOUT_REDIRECT_URL = '/'  # Where admins are redirected to after releasing a user

CDN_FILES_URL = ''

X_FRAME_OPTIONS = 'SAMEORIGIN'
#SECURE_REFERRER_POLICY = 'unsafe-url' # Default: 'same-origin'


DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

REQUEST_LOG_IP = False
REQUEST_IGNORE_PATHS = (
	r'^djangoadmin/',
	r'^research/api/pv/',
	r'^favicon.ico',
)
REQUEST_TRAFFIC_MODULES = (
	'request.traffic.UniqueUser',
	'request.traffic.UniqueVisit',
	'request.traffic.Hit',
	'request.traffic.Error404',
)
REQUEST_PLUGINS = (
	'request.plugins.TrafficInformation',
	'request.plugins.LatestRequests',
	'request.plugins.TopPaths',
	'request.plugins.TopErrorPaths',
	'request.plugins.TopReferrers',
	'request.plugins.TopBrowsers',
	'request.plugins.ActiveUsers',
)


## Import local settings that may exist to override production settings above.
## (settings_local.py)
try:
	from .local_settings import *
except ImportError:
	pass

# These are only used in production/when not in debug mode.
if not DEBUG:
	SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
	SECURE_SSL_REDIRECT = True
	# USE COS and URL for static files collectstatic push and embedding.
	# Compressor with COS requires more investigation for settings. Not really worth it.
	DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
	STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

if DEBUG and DATABASES['default']['HOST'] != 'localhost':
	print('##############################\n##\n##  WARNING, YOU ARE USING PRODUCTION DATABASE\n##\n##############################')
