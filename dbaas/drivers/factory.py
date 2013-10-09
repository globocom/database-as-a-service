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

        raise NotImplementedError()


    @classmethod
    def factory(cls, instance):

        if instance is None:
            raise TypeError(_("Instance is not defined"))

        driver_name = instance.engine_name.lower()
        driver_class = cls.get_driver_class(driver_name)
        return driver_class(instance=instance)

