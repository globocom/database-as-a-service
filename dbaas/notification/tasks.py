# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.conf import settings

import os
import logging
from celery import states
from celery.utils.log import get_task_logger
from dbaas.celery import app

from util import call_script
from system.models import Configuration
 
LOG = get_task_logger(__name__)

CLONE_DATABASE_SCRIPT_NAME="dummy_clone.sh"

@app.task(bind=True)
def clone_database(self, origin_database, dest_database):

    task_name = "clone_database"
    LOG.debug("task name: %s" % clone_database.name)
    LOG.debug("origin_database: %s" % origin_database)
    LOG.debug("dest_database: %s" % dest_database)
    print "AAAAAAAA"
    print "*" * 30

    #origin
    # origin_instance=origin_database.databaseinfra.instances.all()[0]
    # 
    # db_orig=origin_database.name
    # user_orig=origin_database.databaseinfra.user
    # pass_orig=origin_database.databaseinfra.password
    # host_orig=origin_instance.address
    # port_orig=origin_instance.port
    # 
    # #destination
    # dest_instance=dest_database.databaseinfra.instances.all()[0]
    # 
    # db_dest=dest_database.name
    # user_dest=dest_database.databaseinfra.user
    # pass_dest=dest_database.databaseinfra.password
    # host_dest=dest_instance.address
    # port_dest=dest_instance.port
    # 
    # path_of_dump=Configuration.get_by_name('database_clone_dir')
    # engine=origin_database.databaseinfra.engine.name
    # 
    # args=[db_orig, user_orig, pass_orig, host_orig, port_orig, 
    #         db_dest, user_dest, pass_dest, host_dest, port_dest, 
    #         path_of_dump, engine
    # ]
    #call_script(CLONE_DATABASE_SCRIPT_NAME, working_dir=settings.SCRIPTS_PATH, args=args)
    return