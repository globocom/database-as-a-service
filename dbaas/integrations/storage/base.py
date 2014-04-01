# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging

LOG = logging.getLogger(__name__)


class BaseProvider(object):
    """
    BaseProvider interface
    """
    
    def create_disk(self, environment, plan, host):
        raise NotImplementedError()

    def destroy_disk(self, environment, plan, host):
        raise NotImplementedError()
