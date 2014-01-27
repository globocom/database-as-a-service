# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import logging

from celery import shared_task

LOG = logging.getLogger(__name__)

@shared_task
def clone_database(database, credential):

    task_name = "clone_database"
    LOG.debug("task name: %s" % clone_database.name)

    return