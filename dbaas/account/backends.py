# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib.auth.backends import ModelBackend
import logging

LOG = logging.getLogger(__name__)

class DbaasBackend(ModelBackend):
    
    def has_perm(self, user_obj, perm, obj=None):
        #LOG.debug("validating perm %s for user %s on object %s" % (perm, user_obj, obj))
        # We are using django_services in admin, but it does not provide any support to 
        # object level permission
        if not user_obj.is_active:
            return False
        else:
            return perm in user_obj.get_all_permissions(obj=None)
