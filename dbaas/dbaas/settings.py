# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

# Django settings for dbaas project.
import os.path
import sys

# If is running on CI: if CI=1 or running inside jenkins
CI = os.getenv('CI', '0') == '1'

# Include base path in system path for Python old.
syspath = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if not syspath in sys.path:
    sys.path.insert(0, syspath)


def LOCAL_FILES(path):
    new_path = os.path.abspath(os.path.join(__file__, path))
    return new_path

try:
    from dbaas.version import RELEASE
except ImportError:
    RELEASE = None

# Armazena a raiz do projeto.
SITE_ROOT = LOCAL_FILES('../')
SCRIPTS_PATH = syspath + "/drivers/scripts/"

# Keyczar key's directory
ENCRYPTED_FIELD_KEYS_DIR = SITE_ROOT + '/keys'

DEBUG = os.getenv('DBAAS_DEBUG', '1') == '1'
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

# get environment variables for the database
DB_ENGINE = os.getenv('DBAAS_DATABASE_ENGINE', 'django.db.backends.mysql')
DB_NAME = os.getenv('DBAAS_DATABASE_NAME', 'dbaas')
DB_USER = os.getenv('DBAAS_DATABASE_USER', 'root')
DB_PASSWORD = os.getenv('DBAAS_DATABASE_PASSWORD', '')
DB_HOST = os.getenv('DBAAS_DATABASE_HOST', 'localhost')
DB_PORT = os.getenv('DBAAS_DATABASE_PORT', '')
SENTRY = os.getenv('DBAAS_SENTRY', None)
DB_DEFAULT_USER = os.getenv('DBAAS_MONGODB_DEFAULT_USER', 'admin')
DB_DEFAULT_PASSWORD = os.getenv('DBAAS_MONGODB_DEFAULT_PASSWORD', 'adminpwd')

DATABASES = {
    'default': {
        # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'ENGINE': DB_ENGINE,
        # Or path to database file if using sqlite3.
        'NAME': DB_NAME,
        # The following settings are not used with sqlite3:
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        # Empty for localhost through domain sockets or '127.0.0.1' for
        # localhost through TCP.
        'HOST': DB_HOST,
        # Set to empty string for default.
        'PORT': DB_PORT,
    }
}

# get variables for the analytics
GANALYTICS_TRACKING_CODE = os.getenv('DBAAS_ANALYTICS', '')


# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [os.getenv('DBAAS_HOST', None)]

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = os.getenv('DJANGO_TIME_ZONE', 'America/Sao_Paulo')

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = os.path.join(SITE_ROOT, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(os.getenv('DBAAS_STATIC_FILE', SITE_ROOT), RELEASE)
# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/%s/' % RELEASE

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(SITE_ROOT, 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'n3#i=z^st83t5-k_xw!v9t_ey@h=!&6!3e$l6n&sn^o9@f&jxv'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_audit.middleware.TrackingRequestOnThreadLocalMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
)

ROOT_URLCONF = 'dbaas.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'dbaas.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(SITE_ROOT, 'templates')
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dbaas',
    'account',
    'admin',
    'adminplus',
    'physical',
    'logical',
    'tsuru',
    'drivers',
    'dashboard',
    'system',
    'email_extras',
    'simple_audit',
    'django_services',
    'rest_framework',
    'bootstrap_admin',
    'django_extensions',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'raven.contrib.django.raven_compat',
    'ganalytics',
    'haystack',
    'django.contrib.flatpages',
    'ckeditor',
    'notification',
    'djcelery',
    'dbaas_cloudstack',
    'dbaas_credentials',
    'dbaas_nfsaas',
    'dbaas_dbmonitor',
    'dbaas_zabbix',
    'dbaas_dnsapi',
    'backup',
    'dbaas_aclapi',
    'dbaas_laas',
    'maintenance',
    'region_migration',
    'extra_dns',
    'dbaas_services.analyzing',
)


CKEDITOR_UPLOAD_PATH = ''
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': [
            ['Undo', 'Redo',
             '-', 'Bold', 'Italic', 'Underline',
             '-', 'Link', 'Unlink', 'Anchor',
             '-', 'Format',
             '-', 'SpellChecker', 'Scayt',
             '-', 'Maximize',
             ],
            ['HorizontalRule',
             '-', 'Table',
             '-', 'BulletedList', 'NumberedList',
             '-', 'Cut', 'Copy', 'Paste', 'PasteText', 'PasteFromWord',
             '-', 'SpecialChar',
             '-', 'Source',
             '-', 'About',
             ]
        ],
        'toolbarCanCollapse': False,
    }
}

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    'django.core.context_processors.request',
    'dbaas.views.external_links',
)

# backend for haystack
HAYSTACK_PATH = os.getenv(
    'HAYSTACK_PATH', os.path.join(SITE_ROOT, '../', 'whoosh_index'))
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': HAYSTACK_PATH,
    },
}

if not DB_ENGINE.endswith('sqlite3'):
    # support migrations
    INSTALLED_APPS += ('south',)

# http://django-email-extras.readthedocs.org/en/latest/
EMAIL_EXTRAS_USE_GNUPG = False
EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_PORT = os.getenv('EMAIL_PORT', 25)
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', False)

# conf to redis
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
REDIS_DB = os.getenv('REDIS_DB', 0)


SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'
SESSION_COOKIE_AGE = 43200  # 12 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Expire session when browser is closed
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

CACHES = {
    'default': {
        'BACKEND': os.getenv('DBAAS_CACHE_BACKEND', 'django.core.cache.backends.locmem.LocMemCache'),
        'LOCATION': os.getenv('DBAAS_CACHE_LOCATION', 'unique'),
        'TIMEOUT': int(os.getenv('DBAAS_CACHE_TIMEOUT', '60')),
    }
}

TEST_DISCOVER_ROOT = os.path.abspath(os.path.join(__file__, '../..'))
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = ['--verbosity=2', '--no-byte-compile', '-d', '-s']
if CI:
    NOSE_ARGS += ['--with-coverage', '--cover-package=application',
                  '--with-xunit', '--xunit-file=test-report.xml', '--cover-xml', '--cover-xml-file=coverage.xml']

# AUTHENTICATION_BACKENDS = (
#   'django_auth_ldap.backend.LDAPBackend',
#   'account.backends.DbaasBackend',
#   'django.contrib.auth.backends.ModelBackend',
# )

AUTHENTICATION_BACKENDS = [
    'account.backends.DbaasBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# enable m2m fields audit
DJANGO_SIMPLE_AUDIT_ACTIVATED = True
DJANGO_SIMPLE_AUDIT_M2M_FIELDS = True

##################################
# LDAP_AUTHENTICATION
##################################
LDAP_ENABLED = os.getenv('DBAAS_LDAP_ENABLED', '0')
if LDAP_ENABLED == "1":
    LDAP_ENABLED = True
else:
    LDAP_ENABLED = False

LDAP_CERTDIR = os.getenv('DBAAS_LDAP_CERTDIR', '')
LDAP_CACERTFILE = os.getenv('DBAAS_LDAP_CACERTFILE', '')
LDAP_CERTFILE = os.getenv('DBAAS_LDAP_CERTFILE', '')
LDAP_KEYFILE = os.getenv('DBAAS_LDAP_KEYFILE', '')

if LDAP_ENABLED:
    import ldap
    from django_auth_ldap.config import LDAPSearch, GroupOfNamesType

    ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, LDAP_CERTDIR + LDAP_CACERTFILE)
    ldap.set_option(ldap.OPT_X_TLS_CERTFILE, LDAP_CERTDIR + LDAP_CERTFILE)
    ldap.set_option(ldap.OPT_X_TLS_KEYFILE, LDAP_CERTDIR + LDAP_KEYFILE)

    # Baseline configuration.
    AUTH_LDAP_SERVER_URI = os.getenv('AUTH_LDAP_SERVER_URI', '')

    AUTH_LDAP_BIND_DN = os.getenv('AUTH_LDAP_BIND_DN', '')
    AUTH_LDAP_BIND_PASSWORD = os.getenv('AUTH_LDAP_BIND_PASSWORD', '')
    AUTH_LDAP_USER_SEARCH_STR = os.getenv('AUTH_LDAP_USER_SEARCH', '')
    AUTH_LDAP_USER_SEARCH = LDAPSearch(AUTH_LDAP_USER_SEARCH_STR,
                                       ldap.SCOPE_SUBTREE, "(&(uid=%(user)s)(!(nsaccountlock=TRUE)))")
    AUTH_LDAP_GROUP_SEARCH_STR = os.getenv('AUTH_LDAP_GROUP_SEARCH', '')
    AUTH_LDAP_GROUP_SEARCH = LDAPSearch(AUTH_LDAP_GROUP_SEARCH_STR,
                                        ldap.SCOPE_SUBTREE, "(objectClass=groupOfNames)"
                                        )
    AUTH_LDAP_GROUP_TYPE = GroupOfNamesType()
    AUTH_LDAP_ALWAYS_UPDATE_USER = True

    # Populate the Django user from the LDAP directory.
    AUTH_LDAP_USER_ATTR_MAP = {
        "first_name": "givenName",
        "last_name": "sn",
        "email": "mail"
    }

    AUTHENTICATION_BACKENDS = [
        'django_auth_ldap.backend.LDAPBackend'] + AUTHENTICATION_BACKENDS


REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'api.renderers.JSONHalRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser'
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': ('api.base.ObjectPermissions',),
    'DEFAULT_FILTER_BACKENDS': ('api.base.ObjectPermissionsFilter',),
    'EXCEPTION_HANDLER': 'api.base.custom_exception_handler',
    'PAGINATE_BY': 10,                 # Default to 10
    # Allow client to override, using `?page_size=xxx`.
    'PAGINATE_BY_PARAM': 'page_size',
    # Maximum limit allowed when using `?page_size=xxx`.
    'MAX_PAGINATE_BY': 100,
    'TEST_REQUEST_RENDERER_CLASSES': (
        'api.renderers.JSONHalRenderer',
    ),
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

LOGIN_URL = "/admin/"

# sentry configuration
RAVEN_CONFIG = {
    'dsn': SENTRY
}

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.

LOGGING_APP = os.getenv('LOGGING_APP', 'dbaas')
if os.path.exists('/var/run/syslog'):
    SYSLOG_FILE = '/var/run/syslog'
else:
    SYSLOG_FILE = '/dev/log'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'simple': {
            'format': '%(asctime)-23s %(levelname)-7s %(name)s \t %(message)s'
        },
        'syslog_formatter': {
            'format': '%s: #%%(name)s %%(message)s' % LOGGING_APP
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'syslog': {
            'class': 'logging.handlers.SysLogHandler',
            'formatter': 'syslog_formatter',
            'address': SYSLOG_FILE,
        },
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.db.backends': {
            'level': 'INFO'
        },
        'south': {
            'level': 'INFO'
        },
        'simple_audit.signal': {
            'level': 'INFO'
        },
        'factory': {
            'level': 'INFO'
        }
    },
    'root': {
        'handlers': ['console', 'syslog'],
        'level': 'DEBUG',
    }
}

if SENTRY:
    LOGGING['root']['handlers'] += ['sentry']

# logging to file
LOGFILE = os.getenv('DBAAS_LOGFILE', None)
if LOGFILE:
    # log only to file
    LOGGING['handlers']['logfile'] = {
        'class': 'logging.handlers.WatchedFileHandler',
        'formatter': 'simple',
        'filename': LOGFILE,
        'encoding': 'utf-8',
        'mode': 'a'
    }
    LOGGING['root']['handlers'].remove('console')
    LOGGING['root']['handlers'] += ['logfile']

# Credentials for EC2 Provider (I keep compliance with eucatools)
EC2_ACCESS_KEY = os.getenv('EC2_ACCESS_KEY', None)
EC2_SECRET_KEY = os.getenv('EC2_SECRET_KEY', None)
EC2_URL = os.getenv('EC2_URL', None)
EC2_REGION = os.getenv('EC2_REGION', None)  # us-east-1
EC2_SUBNET_ID = os.getenv('EC2_SUBNET_ID', None)  # 'vpc-1212'
EC2_AMI_ID = 'ami-b91043d0'

USER_ROLES = (
    'dba',
    'regular',
)

# CloudStack IaaS Integration credentials
CLOUD_STACK_ENABLED = os.getenv('CLOUD_STACK_ENABLED', '0')
if CLOUD_STACK_ENABLED == "1":
    CLOUD_STACK_ENABLED = True
else:
    CLOUD_STACK_ENABLED = False

NFSAAS_ENABLED = os.getenv('CLOUD_STACK_ENABLED', '0')
if NFSAAS_ENABLED == "1":
    NFSAAS_ENABLED = True
else:
    NFSAAS_ENABLED = False
