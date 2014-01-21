# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _
import re

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
        driver_name = driver_name.lower()
        # TODO: import Engines dynamically
        if re.match(r'^mongo.*', driver_name):
            from .mongodb import MongoDB
            return MongoDB
        elif re.match(r'^mysql.*', driver_name):
            from .mysqldb import MySQL
            return MySQL
        elif re.match(r'^fake.*', driver_name):
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
