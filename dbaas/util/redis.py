# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.conf import settings
import redis

from dbaas.settings import REDIS_HOST,REDIS_PORT,REDIS_DB,REDIS_PASSWORD

def redis_client():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD)