# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import inspect
from util import get_replication_topology_instance

__all__ = ['DriverFactory']


class DriverFactory(object):

    @classmethod
    def is_driver_available(cls, name):
        try:
            cls.get_driver_class(name)
            return True
        except NotImplementedError:
            return False

    @classmethod
    def get_driver_class(cls, driver_name):
        from drivers import base, fake, mongodb, mysqldb, redis, mysqlpercona

        for module in [fake, mongodb, mysqldb, redis, mysqlpercona]:
            for name, klass in inspect.getmembers(module):
                if not inspect.isclass(klass):
                    continue

                if not issubclass(klass, base.BaseDriver):
                    continue

                if driver_name in klass.topology_name():
                    return klass

        raise NotImplementedError('No driver for {}'.format(driver_name))

    @classmethod
    def factory(cls, databaseinfra):
        class_path = databaseinfra.plan.replication_topology.class_path
        driver_name = get_replication_topology_instance(class_path).driver_name

        driver_class = cls.get_driver_class(driver_name)
        return driver_class(databaseinfra=databaseinfra)
