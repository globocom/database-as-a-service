# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import simple_audit
import logging
from sets import Set
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
        #app_label = 'auth'

class Role(Group):
    class Meta:
        proxy = True
        #app_label = 'auth'

class TeamUsersManager(models.Manager):
    """manager for returning """
    def get_query_set(self):
        return User.objects.filter(id__in=[user.id for user in Team.users_without_team()])

class Team(BaseModel):
    
    name = models.CharField(_('name'), max_length=80, unique=True)
    role = models.ForeignKey(Role)
    users = models.ManyToManyField(User)

    objects = models.Manager() # The default manager.
    user_objects = TeamUsersManager() # The Dahl-specific manager.

    # class Meta:
    #     app_label = 'auth'

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.name,)
    
    @classmethod
    def get_all_permissions_for(cls, user=None):
        """return all permissions for user"""
        permissions = []
        if not user.is_active:
            return set(permissions)
        else:
            teams = Team.objects.filter(users=user)
            if teams.count() > 1:
                LOG.warning("user %s is in more than one team! %s" % teams)

            for team in teams:
                permissions = permissions + list(team.role.permissions.all())
            
            return set(["%s.%s" % (p.content_type.app_label, p.codename) for p in permissions])
            #return permissions

    @classmethod
    def users_without_team(cls):
        """get all users without team"""
        users = []
        all_users = Set(User.objects.all())
        teams = Team.objects.all()
        for team in teams:
            for user in team.users.all():
                if user not in users:
                    users.append(user)
        
        return list(all_users.difference(Set(users)))

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
def user_post_save_wrapper(kwargs={}):
    user = kwargs.get('instance')
    created = kwargs.get('created')
    if created:
        LOG.debug("new user %s created" % user)
        user.is_active = True
        user.is_staff = True
        user.save()

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
def account_user_post_save(sender, **kwargs):
    user_post_save_wrapper(kwargs)
    #sync_ldap_groups_with_user(user=user)

@receiver(post_save, sender=User)
def user_post_save(sender, **kwargs):
    user_post_save_wrapper(kwargs)

# def user_m2m_changed(sender, **kwargs):
#     """
#     Using m2m signal to sync user.groups relation in the db with the ones in the LDAP. The action post_clear
#     must be used in order to accomplish this. (https://docs.djangoproject.com/en/1.5/ref/signals/)
#     Remember, remember: only the groups that exists in ldap AND in the database will be synced.
#     You can however, add a group to user that is not created in ldap.
#     """
#     # LOG.debug("m2m_changed kwargs: %s" % kwargs)
#     user = kwargs.get('instance')
#     action = kwargs.get('action')
#     if action == 'post_clear':
#         LOG.info("user %s m2m_changed post_clear signal" % user)
#         #sync_ldap_groups_with_user(user=user)
# 
# 
# m2m_changed.connect(user_m2m_changed, sender=User.groups.through)
# m2m_changed.connect(user_m2m_changed, sender=AccountUser.groups.through)
