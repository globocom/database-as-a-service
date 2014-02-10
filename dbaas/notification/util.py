# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

from system.models import Configuration
from celery.utils.log import get_task_logger

LOG = get_task_logger(__name__)

def get_clone_args(origin_database, dest_database):
    
    #origin
    origin_instance=origin_database.databaseinfra.instances.all()[0]
    
    db_orig=origin_database.name
    user_orig=origin_database.databaseinfra.user
    pass_orig="PASSWORD_ORIGIN=%s" % origin_database.databaseinfra.password
    host_orig=origin_instance.address
    port_orig=origin_instance.port
    
    #destination
    dest_instance=dest_database.databaseinfra.instances.all()[0]
    
    db_dest=dest_database.name
    user_dest=dest_database.databaseinfra.user
    pass_dest="PASSWORD_DEST=%s" % dest_database.databaseinfra.password
    host_dest=dest_instance.address
    port_dest=dest_instance.port
    
    path_of_dump=Configuration.get_by_name('database_clone_dir')
    
    args=[db_orig, user_orig, pass_orig, host_orig, str(int(port_orig)), 
            db_dest, user_dest, pass_dest, host_dest, str(int(port_dest)), 
            path_of_dump
    ]
    
    return args
