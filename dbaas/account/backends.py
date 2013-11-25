# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django.contrib.auth.backends import ModelBackend
from account.models import Team
from logical.models import Database, Credential

LOG = logging.getLogger(__name__)

class DbaasBackend(ModelBackend):
    perm_manage_quarantine_database = "logical.can_manage_quarantine_databases"

    def get_all_permissions(self, user_obj, obj=None):
        # LOG.debug("get_all_permissions for user: %s" % user_obj)
        if user_obj.is_anonymous() or obj is not None:
            return set()
        if not hasattr(user_obj, '_perm_cache'):
            user_obj._perm_cache = set(["%s.%s" % (p.content_type.app_label, p.codename) for p in user_obj.user_permissions.select_related()])
            user_obj._perm_cache.update(self.get_group_permissions(user_obj))
            #get team permissions
            user_obj._perm_cache.update(Team.get_all_permissions_for(user=user_obj))

        return user_obj._perm_cache

    def has_perm(self, user_obj, perm, obj=None):
        LOG.debug("validating perm %s for user %s on object (%s) %s" % (perm, user_obj, type(obj).__name__, obj))
        # We are using django_services in admin, but it does not provide any support to 
        # object level permission
        if not user_obj.is_active:
            return False

        perms = user_obj.get_all_permissions(obj=None)

        if self.perm_manage_quarantine_database in perms:
            return perm in perms
        else:
            if not (perm in perms):
                return False

            # check specific permissions
            if type(obj) == Database:
                return Database.objects.filter(pk=obj.pk).filter(is_in_quarantine=False, team__in=[team.id for team in Team.objects.filter(users=user_obj)]).exists()
            elif type(obj) == Credential:
                return self.has_perm(user_obj, perm, obj=obj.database)
            return True
