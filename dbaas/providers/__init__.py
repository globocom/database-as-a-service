from __future__ import absolute_import, unicode_literals
from django.utils.translation import ugettext_lazy as _

from .base import *  # NOQA

__all__ = ['ProviderFactory']


class ProviderFactory(object):


    @classmethod
    def get_provider_class(cls, type):
        # TODO: import Engines dynamically
        if type == "ec2":
            from .ec2 import Ec2Provider
            return Ec2Provider

        raise NotImplementedError()


    @classmethod
    def factory(cls):

        # if instance is None:
        #     raise TypeError(_("Instance is not defined"))

        driver_name = instance.engine_name.lower()
        driver_class = cls.get_provider_class(driver_name)
        return driver_class(instance=instance)