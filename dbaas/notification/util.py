# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

from system.models import Configuration
from celery.utils.log import get_task_logger
from dbaas_credentials import models
from util import get_credentials_for
from physical.models import Instance

LOG = get_task_logger(__name__)


def get_clone_args(origin_database, dest_database):

    # origin
    origin_instance = origin_database.databaseinfra.instances.all()[0]

    db_orig = origin_database.name
    pass_orig = origin_database.databaseinfra.password
    host_orig = origin_instance.address
    port_orig = origin_instance.port

    # destination
    dest_instance = dest_database.databaseinfra.instances.all()[0]

    db_dest = dest_database.name
    pass_dest = dest_database.databaseinfra.password
    host_dest = dest_instance.address
    port_dest = dest_instance.port

    path_of_dump = Configuration.get_by_name('database_clone_dir')

    if origin_database.databaseinfra.engine.engine_type.name != "redis":
        user_orig = origin_database.databaseinfra.user
        user_dest = dest_database.databaseinfra.user

        args = [db_orig, user_orig, pass_orig, host_orig, str(int(port_orig)),
                db_dest, user_dest, pass_dest, host_dest, str(int(port_dest)),
                path_of_dump
                ]
    else:

        sys_credentials = get_credentials_for(
            origin_database.environment, models.CredentialType.VM)
        sys_user_orig = sys_user_dest = sys_credentials.user
        sys_pass_orig = sys_pass_dest = sys_credentials.password

        if path_of_dump.endswith('/'):
            path_of_dump += 'dump.rdb'
        else:
            path_of_dump += '/dump.rdb'

        args = ['--remove_dump', "60", pass_orig, host_orig,
                str(int(port_orig)), sys_user_orig, sys_pass_orig,
                '/data/data/dump.rdb', pass_dest, host_dest,
                str(int(port_dest)), sys_user_dest, sys_pass_dest,
                '/data/data/dump.rdb', path_of_dump
                ]

        if dest_database.plan.is_ha:
            cluster_info = []

            for instance in dest_database.databaseinfra.instances.filter(instance_type=Instance.REDIS):
                cluster_info.append({"sys_user": sys_user_dest, "sys_pass": sys_pass_dest,
                                     "remote_path": "/data/data/dump.rdb", "host": instance.address,
                                     "redis_pass": pass_dest, "redis_port": str(int(port_dest))})

            args = ['--remove_dump', "60", pass_orig, host_orig,
                    str(int(port_orig)), sys_user_orig, sys_pass_orig,
                    '/data/data/dump.rdb', pass_dest, host_dest,
                    str(int(port_dest)), sys_user_dest, sys_pass_dest,
                    '/data/data/dump.rdb', path_of_dump, '--cluster_info', str(
                        cluster_info)
                    ]

    return args
