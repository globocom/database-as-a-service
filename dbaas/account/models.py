# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import simple_audit
import logging
from sets import Set
from django.db import models
from django.contrib.auth.models import User, Group, Permission
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import pre_save, post_save, pre_delete, m2m_changed
from django.dispatch import receiver
from django_extensions.db.fields.encrypted import EncryptedCharField

from util.models import BaseModel
from util.email_notifications import notify_new_user_creation
from .helper import find_ldap_groups_from_user
from system.models import Configuration
from dbaas.celery import app

LOG = logging.getLogger(__name__)


class AccountUser(User):

    class Meta:
        proxy = True
        verbose_name_plural = _("users")
        verbose_name = _("user")


class Role(Group):

    class Meta:
        proxy = True


class TeamUsersManager(models.Manager):

    """manager for returning """

    def get_query_set(self):
        return User.objects.filter(id__in=[user.id for user in Team.users_without_team()])


class Organization(BaseModel):
    name = models.CharField(
        verbose_name=_('Name'),
        help_text='Organization name',
        max_length=100, null=False, blank=False)
    grafana_orgid = models.CharField(
        verbose_name=_('Grafana Org ID'),
        help_text='Organization id used on grafana dashboard',
        max_length=10, null=True, blank=True)
    grafana_hostgroup = models.CharField(
        verbose_name=_('Grafana Hostgroup'),
        max_length=50, null=True, blank=True)
    grafana_datasource = models.CharField(
        verbose_name=_('Grafana Datasource'),
        max_length=50, null=True, blank=True)
    grafana_endpoint = models.CharField(
        verbose_name=_('Grafana Endpoint'),
        max_length=255, null=True, blank=True)
    external = models.BooleanField(
        verbose_name=_("External"), default=False,
        help_text='Whether the organization is external')

    def __unicode__(self):
        return self.name

    def get_grafana_hostgroup_external_org(self):
        if self.external and self.grafana_hostgroup:
            return self.grafana_hostgroup
        return None


class Team(BaseModel):

    name = models.CharField(_('name'), max_length=80, unique=True)
    email = models.EmailField(null=False, blank=False)
    database_alocation_limit = models.PositiveSmallIntegerField(_('DB Alocation Limit'),
                                                                default=2,
                                                                help_text="This limits the number of databases that a team can create. 0 for unlimited resources.")
    contacts = models.TextField(
        verbose_name=_("Emergency Contacts"), null=True, blank=True,
        help_text=_(
            "People to be reached in case of a critical incident. Eg.: 99999999 - Jhon Doe."
        )
    )
    role = models.ForeignKey(Role)
    users = models.ManyToManyField(User)
    objects = models.Manager()  # The default manager.
    user_objects = TeamUsersManager()  # The Dahl-specific manager.
    organization = models.ForeignKey(
        Organization, related_name="team_organization",
        unique=False, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        # putting permissions for account user and role in team model, because it
        # clashes with the proxied classes permissions
        permissions = (
            ("change_accountuser", "Can change account user"),
            ("add_accountuser", "Can add account user"),
            ("delete_accountuser", "Can delete account user"),
            ("change_role", "Can change role"),
            ("add_role", "Can add role"),
            ("delete_role", "Can delete role"),
        )
        ordering = ['name']

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.name,)

    def clean(self):
        if not self.contacts:
            raise ValidationError({'contacts': ('This field is required',)})

    @classmethod
    def get_all_permissions_for(cls, user=None):
        """return all permissions for user"""

        if not user.is_active:
            return set()
        else:
            teams = user.team_set.all()
            role_pks = [team.role.pk for team in teams]
            permissions = Permission.objects.select_related().filter(
                group__pk__in=role_pks)

            return set(["%s.%s" % (p.content_type.app_label, p.codename) for p in permissions])

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

    @classmethod
    def users_at_same_team(cls, current_user):
        """get all users in the same team of a given user"""

        if not current_user:
            return []

        users = []
        teams = cls.objects.filter(users=current_user)
        for team in teams:
            for user in team.users.all():
                if user not in users:
                    users.append(user)
        return users

    def databases_in_use_for(self, environment):
        #from physical.models import DatabaseInfra
        from logical.models import Database

        #infras = DatabaseInfra.objects.filter(environment=environment)
        dbs = Database.objects.filter(
            team=self, environment=environment)

        return dbs

    def environments_in_use_for(self):
        #from physical.models import DatabaseInfra
        from logical.models import Database

        #infras = DatabaseInfra.objects.filter(environment=environment)
        envs = Database.objects.filter(
            team=self).values_list('environment_id',flat=True)

        return envs

    def count_databases_in_use(self, environment):
        try:
            return len(self.databases_in_use_for(environment))
        except Exception, e:
            LOG.warning(
                "could not count databases in use for team %s, reason: %s" % (self, e))
            return 0

    @property
    def emergency_contacts(self):
        if self.contacts:
            return self.contacts
        return 'Not defined. Please, contact the team'


def sync_ldap_groups_with_user(user=None):
    """
    Sync ldap groups (aka team) with the user
    """
    LOG.debug("User %s groups before: %s" % (user, user.groups.all()))
    ldap_groups = find_ldap_groups_from_user(username=user.username)
    groups = Group.objects.filter(name__in=ldap_groups).exclude(
        user__username=user.username).order_by("name")
    LOG.info(
        "LDAP's team created in the system and not set to user %s: %s" % (user, groups))
    group = None
    if groups:
        group = groups[0]
        user.groups.add(group)
        LOG.info("group %s added to user %s" % (groups[0], user))

    LOG.debug("User %s groups: %s after" % (user, user.groups.all()))

    return group

simple_audit.register(Team, AccountUser, Role)


##########################################################################
# SIGNALS
##########################################################################
# all role name should start with role_
def user_post_save_wrapper(kwargs={}):
    user = kwargs.get('instance')
    created = kwargs.get('created')
    if created:
        LOG.debug("new user %s created" % user)
        user.is_active = True
        user.is_staff = True
        user.save()
        # notify new user create
        notify_new_user_creation(user)


@receiver(pre_save, sender=Role)
def role_pre_save(sender, **kwargs):
    role = kwargs.get('instance')
    if not role.name.startswith('role_'):
        role.name = "role_" + role.name


@receiver(pre_save, sender=User)
def user_pre_save(sender, **kwargs):
    user = kwargs.get('instance')
    user._meta.get_field('username').max_length = 100
    LOG.debug("user %s pre save signal" % user)


@receiver(post_save, sender=AccountUser)
def account_user_post_save(sender, **kwargs):
    user_post_save_wrapper(kwargs)
    # sync_ldap_groups_with_user(user=user)


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
