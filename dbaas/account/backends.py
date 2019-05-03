# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import re
import json
import commands
import requests
import logging
from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from account.models import Team
from logical.models import Database, Credential
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied


LOG = logging.getLogger(__name__)


class DbaasBackend(ModelBackend):
    perm_manage_quarantine_database = "logical.can_manage_quarantine_databases"

    @staticmethod
    def get_ip():
        local = '127.0.0.1'
        interface = ''
        status, interfaces = commands.getstatusoutput('/sbin/ifconfig -a')
        if status == 0:
            pattern = re.compile('inet [^0-9]*([0-9.]*).*')
            for line in interfaces.split('\n'):
                m = pattern.search(line)
                if m:
                    ip = m.group(1)
                    if ip[0:4] != '127.' and not interface:
                        interface = ip
        return interface or local

#    def authenticate(self, username, password):
#        if not settings.DBAAS_OAUTH2_LOGIN_ENABLE:
#            return None
#        url = '{}/api/2.0/signin'.format(settings.DBAAS_AUTH_API_URL)
#        if '@' not in username:
#            username += '@corp.globo.com'
#        data = {
#            "mail": username,
#            "password": password,
#            "twofactor": "disable",
#            "src": self.get_ip(),
#            "info": "DBaaS"
#        }
#        resp = requests.post(url, data=json.dumps(data))
#        if resp.ok:
#            ldap_user_data = resp.json().get('data', {})
#            UserModel = get_user_model()
#            try:
#                user = UserModel.objects.get(
#                    username=ldap_user_data.get('username'),
#                    email=ldap_user_data.get('mail')
#                )
#            except UserModel.DoesNotExist:
#                return None
#            else:
#                return user

    @staticmethod
    def can_login(user):
        from account.models import Role

        role_dba = Role.objects.get(name='role_dba')

        dba_groups = role_dba.team_set.values_list('id', flat=True)
        return (user.is_superuser or
                user.team_set.filter(id__in=dba_groups))

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
