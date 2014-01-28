# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.conf import settings

import os
import logging
from celery.utils.log import get_task_logger
from dbaas.celery import app

from util import call_script
 
LOG = get_task_logger(__name__)

@app.task
def clone_database(origin_database, dest_database):

    task_name = "clone_database"
    LOG.debug("task name: %s" % clone_database.name)
    LOG.debug("origin_database: %s" % origin_database)
    LOG.debug("dest_database: %s" % dest_database)

    return