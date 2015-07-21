# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.conf import settings
from dbaas import features

import logging

LOG = logging.getLogger(__name__)


def get_ldap_connection():
    import ldap
    server = settings.AUTH_LDAP_SERVER_URI
    user_pw = settings.AUTH_LDAP_BIND_PASSWORD
    dn = settings.AUTH_LDAP_BIND_DN
    conn = None

    LOG.debug("connecting to LDAP")
    conn = ldap.initialize(server)
    conn.bind_s(dn, user_pw)
    LOG.debug("Done")

    return conn


def find_ldap_groups_from_user(username=None):
    groups = []
    if features.LDAP_ENABLED and username:
        import ldap
        user_search = settings.AUTH_LDAP_USER_SEARCH_STR
        group_search = settings.AUTH_LDAP_GROUP_SEARCH_STR
        LOG.debug("group search: %s" % group_search)
        LOG.debug("searching ldap groups for username %s" % username)
        try:
            conn = get_ldap_connection()
            # searchFilter = "username=%s" % username
            # user_result = conn.search_s(user_search, ldap.SCOPE_SUBTREE, search_filter,
            #                         None)
            # LOG.debug(user_result)
            group_result = conn.search_s(
                group_search, ldap.SCOPE_SUBTREE, "memberUid=%s" % username, None)

            for entry in group_result:
                group_name = entry[0].split(',')[0].split('=')[1].strip()
                if group_name != username:
                    groups.append("ldap_" + group_name)
        except Exception, e:
            LOG.error("Ops... something went wrong: %s" % e)

        finally:
            conn.unbind()
            LOG.info("LDAP connection closed")
    LOG.info("ldap groups found for username %s: %s" % (username, groups))
    return groups
