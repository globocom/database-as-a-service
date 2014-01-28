# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import logging

from dbaas.celery import app

LOG = logging.getLogger(__name__)

@app.task
def clone_database(self, database, credential):

    task_name = "clone_database"
    LOG.debug("task name: %s" % clone_database.name)

    return