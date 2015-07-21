# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django.conf import settings
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
            user_obj._perm_cache = (
                Team.get_all_permissions_for(user=user_obj))

        return user_obj._perm_cache

    def has_perm(self, user_obj, perm, obj=None):
        #LOG.debug("validating perm %s for user %s on object (%s) %s" % (perm, user_obj, type(obj).__name__, obj))
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

    @staticmethod
    def change_password(username, old_password=None, new_password="globo123"):
        import ldap

        if not settings.LDAP_ENABLED:
            return super(DbaasBackend, self).change_password(username, old_password, new_password)
        else:
            conn = None
            server = settings.AUTH_LDAP_SERVER_URI
            dn = settings.AUTH_LDAP_BIND_DN
            user_pw = settings.AUTH_LDAP_BIND_PASSWORD
            user_search = settings.AUTH_LDAP_USER_SEARCH
            ret = None
            try:
                conn = ldap.initialize(server)
                conn.bind_s(dn, user_pw)
                dn_ = 'cn=%s,%s' % (username, user_search.base_dn)
                LOG.info("Changing dn password %s" % dn_)
                ret = conn.passwd_s(dn_, old_password, new_password)
                LOG.info("Return: %s" % ret)
            except Exception, e:
                LOG.error(
                    "Ops... got an error while changing password: %s" % e)
                ret = e
            finally:
                conn.unbind()

            return ret
