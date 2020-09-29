# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import simple_audit
import logging
from django.db import models
from django.contrib.auth.models import User, Group, Permission
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import (pre_save, post_save, pre_delete,
                                      m2m_changed)
from django.dispatch import receiver
from django_extensions.db.fields.encrypted import EncryptedCharField

from util.models import BaseModel
from util.email_notifications import notify_new_user_creation
from .helper import find_ldap_groups_from_user
from system.models import Configuration
from dbaas.celery import app

from physical.models import Environment

LOG = logging.getLogger(__name__)


class AccountUser(User):

    class Meta:
        proxy = True
        verbose_name_plural = _("users")
        verbose_name = _("user")


class Role(Group):

    class Meta:
        proxy = True


class RoleEnvironment(BaseModel):
    role = models.OneToOneField(
        Role,
        on_delete=models.CASCADE,
        related_name='role_environment'
    )
    environments = models.ManyToManyField(
        Environment, related_name='roles', blank=True
    )

    def __unicode__(self):
        return str(self.role)


class TeamUsersManager(models.Manager):

    """manager for returning """

    def get_query_set(self):
        return User.objects.filter(
            id__in=[user.id for user in Team.users_without_team()]
        )


class Organization(BaseModel):
    name = models.CharField(
        verbose_name='Name',
        help_text='Organization name.',
        max_length=100, null=False, blank=False)
    grafana_orgid = models.CharField(
        verbose_name='Grafana Org ID',
        help_text='External organization id. Used on grafana dashboard.',
        max_length=10, null=True, blank=True)
    grafana_hostgroup = models.CharField(
        verbose_name='Grafana Hostgroup',
        help_text=('External grafana Hostgroup. Used to retrinct '
                   'access on metrics.'),
        max_length=50, null=True, blank=True)
    grafana_datasource = models.CharField(
        verbose_name='Grafana Datasource',
        help_text='Datasource used on external organization.',
        max_length=50, null=True, blank=True)
    grafana_endpoint = models.CharField(
        verbose_name='Grafana Endpoint',
        help_text='Endpoint used on external organization.',
        max_length=255, null=True, blank=True)
    external = models.BooleanField(
        verbose_name="External",
        default=False,
        help_text=('Whether the organization is external. If checked, '
                   'all fields become mandatory.')
    )

    def __unicode__(self):
        return self.name

    @property
    def databases(self):
        from logical.models import Database
        return Database.objects.filter(team__organization=self)

    def get_grafana_hostgroup_external_org(self):
        if self.external and self.grafana_hostgroup:
            return self.grafana_hostgroup
        return None

    def clean(self):
        if self.external:
            error = {}
            msg_field_required = ('This field is required',)
            if not self.grafana_orgid:
                error['grafana_orgid'] = msg_field_required
            if not self.grafana_hostgroup:
                error['grafana_hostgroup'] = msg_field_required
            if not self.grafana_datasource:
                error['grafana_datasource'] = msg_field_required
            if not self.grafana_endpoint:
                error['grafana_endpoint'] = msg_field_required

            if error:
                raise ValidationError(error)


class Team(BaseModel):

    name = models.CharField(_('name'), max_length=80, unique=True)
    email = models.EmailField(null=False, blank=False)
    database_alocation_limit = models.PositiveSmallIntegerField(
        _('DB Alocation Limit'),
        default=2,
        help_text=("This limits the number of databases that a team can "
                   "create. 0 for unlimited resources.")
    )
    contacts = models.TextField(
        verbose_name=_("Emergency Contacts"), null=True, blank=True,
        help_text=_(
            ("People to be reached in case of a critical incident. "
             "Eg.: 99999999 - Jhon Doe.")
        )
    )
    role = models.ForeignKey(Role)
    users = models.ManyToManyField(User)
    objects = models.Manager()  # The default manager.
    user_objects = TeamUsersManager()  # The Dahl-specific manager.
    organization = models.ForeignKey(
        Organization, related_name="team_organization",
        unique=False, null=False, blank=False, on_delete=models.PROTECT)

    token = EncryptedCharField(
        verbose_name=_("Token"), max_length=255, blank=True, null=True
    )

    class Meta:
        # putting permissions for account user and role in team model,
        # because it clashes with the proxied classes permissions
        permissions = (
            ("change_accountuser", "Can change account user"),
            ("add_accountuser", "Can add account user"),
            ("delete_accountuser", "Can delete account user"),
            ("change_role", "Can change role"),
            ("add_role", "Can add role"),
            ("delete_role", "Can delete role"),
            ("view_team", "Can view team"),
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

            return set(
                ["%s.%s" % (p.content_type.app_label, p.codename)
                 for p in permissions]
            )

    @classmethod
    def users_without_team(cls):
        """get all users without team"""
        users = []
        all_users = set(User.objects.all())
        teams = Team.objects.all()
        for team in teams:
            for user in team.users.all():
                if user not in users:
                    users.append(user)

        return list(all_users.difference(set(users)))

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
        from logical.models import Database

        dbs = Database.objects.filter(
            team=self, environment=environment)

        return dbs

    def environments_in_use_for(self):
        from logical.models import Database

        envs = Database.objects.filter(team=self).values_list(
            'environment_id', flat=True
        )

        return envs

    def count_databases_in_use(self, environment):
        try:
            return len(self.databases_in_use_for(environment))
        except Exception, e:
            LOG.warning(
                ("could not count databases in use for team %s, "
                 "reason: %s" % (self, e))
            )
            return 0

    def generate_token(self):
        from uuid import uuid4
        return uuid4().hex

    @property
    def emergency_contacts(self):
        if self.contacts:
            return self.contacts
        return 'Not defined. Please, contact the team'

    @property
    def external(self):
        if self.organization and self.organization.external:
            return True
        return False


def sync_ldap_groups_with_user(user=None):
    """
    Sync ldap groups (aka team) with the user
    """
    LOG.debug("User %s groups before: %s" % (user, user.groups.all()))
    ldap_groups = find_ldap_groups_from_user(username=user.username)
    groups = Group.objects.filter(name__in=ldap_groups).exclude(
        user__username=user.username).order_by("name")
    LOG.info(
        ("LDAP's team created in the system and not set to "
         "user %s: %s" % (user, groups))
    )
    group = None
    if groups:
        group = groups[0]
        user.groups.add(group)
        LOG.info("group %s added to user %s" % (groups[0], user))

    LOG.debug("User %s groups: %s after" % (user, user.groups.all()))

    return group


simple_audit.register(Team, AccountUser, Role, Organization)


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
        must_send_mail = Configuration.get_by_name_as_int(
            'new_user_send_mail', 1
        )
        if must_send_mail:
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


@receiver(pre_save, sender=Team)
def team_pre_save(sender, **kwargs):
    from notification.tasks import TaskRegister

    team = kwargs.get('instance')
    if not team.id:
        team.token = team.generate_token()
        return
    before_update_team = Team.objects.get(pk=team.pk)
    if team.organization != before_update_team.organization:

        for database in team.databases.all():
            TaskRegister.update_organization_name_monitoring(
                database=database,
                organization_name=team.organization.name)

        if (before_update_team.organization and
                before_update_team.organization.external):

            for database in before_update_team.databases.all():
                TaskRegister.update_database_monitoring(
                    database=database,
                    hostgroup=(before_update_team
                               .organization.grafana_hostgroup),
                    action='remove')

        if team.organization and team.organization.external:
            for database in team.databases.all():
                TaskRegister.update_database_monitoring(
                    database=database,
                    hostgroup=team.organization.grafana_hostgroup,
                    action='add')


@receiver(pre_save, sender=Organization)
def organization_pre_save(sender, **kwargs):
    from notification.tasks import TaskRegister

    def add_monit(organization):
        for database in organization.databases:
            TaskRegister.update_database_monitoring(
                database=database,
                hostgroup=organization.grafana_hostgroup,
                action='add')

    def remove_monit(organization):
        for database in organization.databases:
            TaskRegister.update_database_monitoring(
                database=database,
                hostgroup=organization.grafana_hostgroup,
                action='remove')

    organization = kwargs.get('instance')
    if not organization.id:
        return
    before_update_org = Organization.objects.get(pk=organization.pk)

    if before_update_org.external != organization.external:
        if before_update_org.external:
            remove_monit(before_update_org)
        if organization.external:
            add_monit(organization)

    if before_update_org.grafana_hostgroup != organization.grafana_hostgroup:
        if before_update_org.external:
            remove_monit(before_update_org)
        if organization.external:
            add_monit(organization)

    if before_update_org.name != organization.name:
        for database in organization.databases:
            TaskRegister.update_organization_name_monitoring(
                database=database,
                organization_name=organization.name)
