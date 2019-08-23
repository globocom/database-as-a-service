import os


REDIS_PORT = os.getenv('DBAAS_NOTIFICATION_BROKER_PORT', '6379')
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
BROKER_URL = os.getenv(
    'DBAAS_NOTIFICATION_BROKER_URL',
    'redis://{}:{}/0'.format(REDIS_HOST, REDIS_PORT)
)
CELERYD_TASK_TIME_LIMIT = 10800
CELERY_TRACK_STARTED = True
CELERY_IGNORE_RESULT = False
CELERY_RESULT_BACKEND = 'djcelery.backends.cache:CacheBackend'
CELERYBEAT_MAX_LOOP_INTERVAL = 5
CELERY_TIMEZONE = os.getenv('DJANGO_TIME_ZONE', 'America/Sao_Paulo')
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'
CELERYD_LOG_FORMAT = ("[%(asctime)s: %(processName)s %(name)s %(levelname)s] "
                      "%(message)s")
CELERY_ALWAYS_EAGER = False
CELERYD_LOG_COLOR = False
CELERYD_PREFETCH_MULTIPLIER = 1
