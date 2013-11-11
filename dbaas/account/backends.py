# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib.auth.backends import ModelBackend
import logging

LOG = logging.getLogger(__name__)

class DbaasBackend(ModelBackend):

    def get_all_permissions(self, user_obj, obj=None):
        if user_obj.is_anonymous() or obj is not None:
            return set()
        if not hasattr(user_obj, '_perm_cache'):
            user_obj._perm_cache = set(["%s.%s" % (p.content_type.app_label, p.codename) for p in user_obj.user_permissions.select_related()])
            user_obj._perm_cache.update(self.get_group_permissions(user_obj))
        return user_obj._perm_cache

    def has_perm(self, user_obj, perm, obj=None):
        #LOG.debug("validating perm %s for user %s on object %s" % (perm, user_obj, obj))
        # We are using django_services in admin, but it does not provide any support to 
        # object level permission
        if not user_obj.is_active:
            return False
        else:
            return perm in user_obj.get_all_permissions(obj=None)
