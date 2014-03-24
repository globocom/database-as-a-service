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

        # if databaseinfra is None:
        #     raise TypeError(_("DatabaseInfra is not defined"))

        provider_class = cls.get_provider_class("ec2")
        return provider_class()
