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
    #     if 'instance' in kwargs:
    #         self.instance = kwargs.get('instance')
    #     else:
    #         raise TypeError(_("Instance is not defined"))

    def provision_instance(self, instance):
        """
        Provision's the instance
        """
        raise NotImplementedError()
    
    def destroy_instance(self, instance):
        raise NotImplementedError()

    def create_node(self, instance):
        raise NotImplementedError()

    def destroy_node(self, node):
        raise NotImplementedError()