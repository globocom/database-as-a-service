# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging

LOG = logging.getLogger(__name__)


class BaseProvider(object):
    """
    BaseProvider interface
    """
    # def __init__(self, *args, **kwargs):
    # 
    #     if 'databaseinfra' in kwargs:
    #         self.databaseinfra = kwargs.get('databaseinfra')
    #     else:
    #         raise TypeError(_("DatabaseInfra is not defined"))

    def create_instance(self, databaseinfra):
        raise NotImplementedError()

    def destroy_instance(self, instance):
        raise NotImplementedError()

    def check_ssh(self, host):
        raise NotImplementedError()
