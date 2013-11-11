# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import simple_audit
import logging
from django.db import models
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import pre_save, post_save, pre_delete, m2m_changed
from django.dispatch import receiver
from django_extensions.db.fields.encrypted import EncryptedCharField

from util.models import BaseModel
from .helper import find_ldap_groups_from_user

LOG = logging.getLogger(__name__)

class UserRepository(object):

    @staticmethod
    def get_groups_for(user=None):
        return user.groups.exclude(name__startswith="role") if user else []

    @staticmethod
    def get_roles_for(user=None):
        return user.groups.filter(name__startswith="role") if user else []


class AccountUser(User):
    class Meta:
        proxy = True
        verbose_name_plural = _("users")
        verbose_name = _("user")
        app_label = 'auth'


class Team(Group):
    class Meta:
        proxy = True
        app_label = 'auth'


class Role(Group):
    class Meta:
        proxy = True
        app_label = 'auth'


def sync_ldap_groups_with_user(user=None):
    """
    Sync ldap groups (aka team) with the user
    """
    LOG.debug("User %s groups before: %s" % (user, user.groups.all()))
    ldap_groups = find_ldap_groups_from_user(username=user.username)
    groups = Group.objects.filter(name__in=ldap_groups).exclude(user__username=user.username).order_by("name")
    LOG.info("LDAP's team created in the system and not set to user %s: %s" % (user, groups))
    group = None
    if groups:
        group = groups[0]
        user.groups.add(group)
        LOG.info("group %s added to user %s" % (groups[0], user))
    
    LOG.debug("User %s groups: %s after" % (user, user.groups.all()))
    
    return group

simple_audit.register(AccountUser, Team, Role)


#####################################################################################################
# SIGNALS
#####################################################################################################
#all role name should start with role_
@receiver(pre_save, sender=Role)
def role_pre_save(sender, **kwargs):
    role = kwargs.get('instance')
    if not role.name.startswith('role_'):
        role.name = "role_" + role.name

#all users should be is_staff True
@receiver(pre_save, sender=AccountUser)
def user_pre_save(sender, **kwargs):
    user = kwargs.get('instance')
    LOG.debug("user %s pre save signal" % user)

@receiver(post_save, sender=AccountUser)
def user_post_save(sender, **kwargs):
    user = kwargs.get('instance')
    created = kwargs.get('created')
    if created:
        LOG.debug("new user %s created" % user)
        user.is_active = True
        user.is_staff = True
        user.save()
        #sync_ldap_groups_with_user(user=user)


def user_m2m_changed(sender, **kwargs):
    """
    Using m2m signal to sync user.groups relation in the db with the ones in the LDAP. The action post_clear
    must be used in order to accomplish this. (https://docs.djangoproject.com/en/1.5/ref/signals/)
    Remember, remember: only the groups that exists in ldap AND in the database will be synced.
    You can however, add a group to user that is not created in ldap.
    """
    # LOG.debug("m2m_changed kwargs: %s" % kwargs)
    user = kwargs.get('instance')
    action = kwargs.get('action')
    if action == 'post_clear':
        LOG.info("user %s m2m_changed post_clear signal" % user)
        #sync_ldap_groups_with_user(user=user)


m2m_changed.connect(user_m2m_changed, sender=User.groups.through)

