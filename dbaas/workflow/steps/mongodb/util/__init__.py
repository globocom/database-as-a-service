# -*- coding: utf-8 -*-
import logging

LOG = logging.getLogger(__name__)


def build_mongodb_connect_string(instances, databaseinfra):
    connect_string = ""
    for instance in instances:
        if instance.instance_type != instance.MONGODB_ARBITER:
            if connect_string:
                connect_string += ','
            connect_string += instance.address + \
                ":" + str(instance.port)

    connect_string = databaseinfra.get_driver().get_replica_name() + \
        "/" + connect_string

    connect_string = " --host {} admin -u{} -p{}".format(
        connect_string, databaseinfra.user, databaseinfra.password)

    LOG.debug(connect_string)
    return connect_string
