# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _

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
        # TODO: import Engines dynamically
        if driver_name == "mongodb":
            from .mongodb import MongoDB
            return MongoDB
        elif driver_name == "fake":
            from .fake import FakeDriver
            return FakeDriver

        raise NotImplementedError()

    @classmethod
    def factory(cls, databaseinfra):

        if not (databaseinfra and databaseinfra.engine and databaseinfra.engine.engine_type):
            raise TypeError(_("DatabaseInfra is not defined"))

        driver_name = databaseinfra.engine.engine_type.name
        driver_class = cls.get_driver_class(driver_name)
        return driver_class(databaseinfra=databaseinfra)

