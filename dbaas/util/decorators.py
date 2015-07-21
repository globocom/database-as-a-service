# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
from dbaas.settings import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD
import redis
from functools import wraps

LOG = logging.getLogger(__name__)


REDIS_CLIENT = redis.Redis(
    host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD)


def only_one(key="", timeout=None):
    """Enforce only one celery task at a time."""
    def real_decorator(function):
        """Decorator."""
        @wraps(function)
        def wrapper(*args, **kwargs):
            """Caller."""
            have_lock = False
            lock = REDIS_CLIENT.lock(key, timeout=timeout)
            try:
                have_lock = lock.acquire(blocking=False)
                if have_lock:
                    function(*args, **kwargs)
                else:
                    LOG.info("key %s locked..." % key)
            finally:
                if have_lock:
                    lock.release()
        return wrapper
    return real_decorator
