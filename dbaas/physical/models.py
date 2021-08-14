#  *- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import logging
import os

import simple_audit
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils.html import format_html
from django.utils.module_loading import import_by_path
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields.encrypted import (EncryptedCharField,
                                                   EncryptedTextField)
from slugify import slugify

from drivers import DatabaseInfraStatus
from physical.errors import (NoDiskOfferingGreaterError,
                             NoDiskOfferingLesserError)
from physical.commands import HostCommands
from physical.ssh import HostSSH
from physical.database_scripts import DatabaseScript
from system.models import Configuration
from util.models import BaseModel


LOG = logging.getLogger(__name__)


class Offering(BaseModel):
    name = models.CharField(
        verbose_name=_("Name"), max_length=100, help_text="Offering name"
    )
    cpus = models.FloatField(verbose_name=_("Number of CPUs"), default=0,)
    memory_size_mb = models.IntegerField(
        verbose_name=_("Memory (MB)"), default=0,
    )
    environments = models.ManyToManyField(
        'Environment', verbose_name=_("Environments"), related_name='offerings'
    )

    def __unicode__(self):
        return '{}'.format(self.name)

    @classmethod
    def get_equivalent_offering(cls, database, to_environment):
        current_offer = database.infra.offering
        offers = cls.objects.filter(
            cpus__gte=current_offer.cpus,
            memory_size_mb__gte=current_offer.memory_size_mb,
            environments__in=[to_environment]
        ).order_by("cpus", "memory_size_mb")

        if offers.exists():
            return offers.first()

        raise Exception("There's no equivalent offer")


class Environment(BaseModel):

    DEV = 1
    PROD = 2
    STAGE_CHOICES = (
        (DEV, 'Dev'),
        (PROD, 'Prod'),
    )

    CLOUDSTACK = 1
    AWS = 2
    KUBERNETES = 3
    GCP = 4

    PROVISIONER_CHOICES = (
        (CLOUDSTACK, 'Cloud Stack'),
        (AWS, 'AWS'),
        (KUBERNETES, 'Kubernetes'),
        (GCP, 'GCP')
    )

    name = models.CharField(
        verbose_name=_("Environment"), max_length=100, unique=True)
    min_of_zones = models.PositiveIntegerField(default=1)
    migrate_environment = models.ForeignKey(
        'Environment', related_name='migrate_to', blank=True, null=True
    )
    cloud = models.ForeignKey(
        'Cloud', related_name='environment_cloud',
        unique=False, null=False, blank=False, on_delete=models.PROTECT)
    stage = models.IntegerField(choices=STAGE_CHOICES, default=DEV)
    provisioner = models.IntegerField(
        choices=PROVISIONER_CHOICES, default=CLOUDSTACK
    )
    location_description = models.CharField(
        verbose_name=_("Location description"),
        max_length=255,
        blank=True,
        null=True,
        default=None,
        help_text=_("Environment location description.")
    )
    tsuru_deploy = models.BooleanField(
        verbose_name="Tsuru deploy enabled",
        default=False,
        help_text=(
            "Check this option if this environment can be deployed by tsuru")
    )

    def __unicode__(self):
        return '%s' % (self.name)

    def active_plans(self):
        return self.plans.filter(is_active=True)

    @classmethod
    def _get_envs_by(cls, field_name, field_val):
        return cls.objects.filter(**{field_name: field_val}).values_list(
            'name', flat=True
        )

    @classmethod
    def _get_envs_by_stage(cls, stage):
        return cls._get_envs_by('stage', stage)

    @classmethod
    def _get_envs_by_provisioner(cls, provisioner):
        return cls._get_envs_by('provisioner', provisioner)

    @classmethod
    def prod_envs(cls):
        return cls._get_envs_by_stage(cls.PROD)

    @classmethod
    def dev_envs(cls):
        return cls._get_envs_by_stage(cls.DEV)

    @classmethod
    def k8s_envs(cls):
        return cls._get_envs_by_provisioner(cls.KUBERNETES)

    @classmethod
    def get_stage_by_id(cls, id):
        for st in cls.STAGE_CHOICES:
            if st[0] == id:
                return st[1]
        return None


class EnvironmentGroup(BaseModel):
    name = models.CharField(max_length=100, help_text="Group name")
    environments = models.ManyToManyField(Environment, related_name='groups')

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name


class EngineType(BaseModel):

    name = models.CharField(
        verbose_name=_("Engine name"), max_length=100, unique=True
    )
    is_in_memory = models.BooleanField(
        verbose_name="Is in memory database",
        default=False,
        help_text="Check this option if this is in memory engine, e.g. Redis"
    )

    class Meta:
        permissions = (
            ("view_enginetype", "Can view engine types"),
        )
        ordering = ('name', )

    def __unicode__(self):
        return "%s" % (self.name,)


class Engine(BaseModel):
    engine_type = models.ForeignKey(
        EngineType, verbose_name=_("Engine types"), related_name="engines",
        on_delete=models.PROTECT
    )
    version = models.CharField(
        verbose_name=_("Engine version"), max_length=100,
    )
    path = models.CharField(
        verbose_name=_("Engine path"), max_length=255, blank=True, null=True,
        help_text=_("Path to look for the engine's executable file.")
    )
    template_name = models.CharField(
        verbose_name=_("Template Name"), max_length=200, blank=True, null=True,
        help_text="Template name registered in your provision system"
    )
    user_data_script = models.TextField(
        verbose_name=_("User data script"), blank=True, null=True,
        help_text=("Script that will be sent as an user-data to provision the "
                   "virtual machine")
    )
    engine_upgrade_option = models.ForeignKey(
        "Engine", null=True, blank=True, related_name='backwards_engine',
        verbose_name=_("Engine version upgrade"), on_delete=models.SET_NULL
    )
    has_users = models.BooleanField(default=True)
    write_node_description = models.CharField(
        verbose_name=_("Write name"), blank=True, null=True, default='',
        help_text="Ex: Master or Primary", max_length=100,
    )
    read_node_description = models.CharField(
        verbose_name=_("Read name"), blank=True, null=True, default='',
        help_text="Ex: Slave or Secondary", max_length=100,
    )
    major_version = models.PositiveIntegerField(
        verbose_name=_("Engine major version"), blank=True, null=True
    )
    minor_version = models.PositiveIntegerField(
        verbose_name=_("Engine minor version"), blank=True, null=True
    )
    is_active = models.BooleanField(
        verbose_name=_("Is engine active"), default=True
    )

    class Meta:
        unique_together = (
            ('version', 'engine_type', )
        )
        permissions = (
            ("view_engine", "Can view engines"),
        )
        ordering = ('engine_type__name', 'version')

    @property
    def name(self):
        return self.engine_type.name

    @property
    def full_name(self):
        return "{}_{}".format(self.name, self.version)

    @property
    def full_name_initial_version(self):
        return "{}_{}".format(self.name, self.full_inicial_version)

    @property
    def full_name_for_host_provider(self):
        return self.full_name_initial_version.replace(".", "_")

    @property
    def version2(self):
        return "{}.{}".format(self.major_version, self.minor_version)

    @property
    def full_inicial_version(self):
        patch = self.patchs.get(is_initial_patch=True)

        return "{}.{}.{}".format(
            self.major_version,
            self.minor_version,
            patch.patch_version)

    @property
    def default_engine_patch(self):
        return self.patchs.get(is_initial_patch=True)

    def __unicode__(self):
        return self.full_name

    @property
    def is_redis(self):
        return self.name == 'redis'

    def available_patches(self, database):
        engine_patch = database.infra.engine_patch
        available_patches = self.patchs.exclude(
            is_initial_patch=True
        )

        if engine_patch and engine_patch.engine == self:
            available_patches = available_patches.filter(
                patch_version__gt=engine_patch.patch_version
            )

        return available_patches


class EnginePatch(BaseModel):
    engine = models.ForeignKey(
        Engine, verbose_name=_("Engine"),
        related_name='patchs'
    )
    patch_version = models.PositiveIntegerField(
        verbose_name=_("Engine patch version")
    )
    is_initial_patch = models.BooleanField(
        verbose_name=_("Is initial patch"),
        default=False
    )
    patch_path = models.CharField(
        verbose_name=_("Path of installation file"),
        blank=True, null=True, default='',
        max_length=200,
    )

    patch_path_ol7 = models.CharField(
        verbose_name=_("Path of installation file in OL7"),
        blank=True, null=True, default='',
        max_length=200,
    )

    required_disk_size_gb = models.FloatField(
        verbose_name=_("Required Disk Size (GB)"),
        null=True, blank=True
    )

    @property
    def full_version(self):
        return "{}.{}.{}".format(
            self.engine.major_version,
            self.engine.minor_version,
            self.patch_version
        )

    def __str__(self):
        return self.full_version

    def __unicode__(self):
        return self.full_version


class Parameter(BaseModel):
    engine_type = models.ForeignKey(
        EngineType,
        verbose_name=_("Engine type"),
        related_name="enginetype",
        on_delete=models.PROTECT
    )
    name = models.CharField(
        verbose_name=_("Parameter Name"),
        max_length=200
    )

    description = models.TextField(
        verbose_name=_("Description"),
        max_length=200,
        blank=True, null=True
    )

    allowed_values = models.CharField(
        verbose_name=_("Allowed Values"),
        max_length=200,
        blank=True, null=True,
        default=''
    )

    TYPE_CHOICES = (
        ('', ''),
        ('string', 'String'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
    )

    parameter_type = models.CharField(
        verbose_name=_("Type"),
        max_length=100,
        choices=TYPE_CHOICES,
        default='',
    )

    custom_method = models.CharField(
        verbose_name=_("Custom Method"), max_length=200,
        help_text="Custom method with steps for changing this parameter.",
        blank=True, null=True
    )

    dynamic = models.BooleanField(
        verbose_name=_("Dynamic"),
        help_text="Check this option if the parameter is dynamic. That is, \
        it can be changed without restart the database.",
        default=True
    )

    class Meta:
        unique_together = (
            ('name', 'engine_type', )
        )
        permissions = (
            ("view_parameter", "Can view parameter"),
        )
        ordering = ('engine_type__name', 'name')

    def __unicode__(self):
        return '{}: {}'.format(self.engine_type, self.name)


class Script(BaseModel):

    name = models.CharField(max_length=100)
    initialization = models.CharField(max_length=300, help_text="File path")
    configuration = models.CharField(max_length=300, help_text="File path")
    start_database = models.CharField(max_length=300, help_text="File path")
    start_replication = models.CharField(
        max_length=300, help_text="File path", null=True, blank=True
    )
    metric_collector = models.CharField(
        max_length=300, help_text="File path", null=True, blank=True
    )
    configure_log = models.CharField(
        max_length=300, help_text="File path", null=True, blank=True
    )

    def _get_content(self, file_name):
        path = file_name

        if not os.path.exists(path):
            physical_path = os.path.dirname(os.path.abspath(__file__))
            path = '{}/scripts/{}'.format(physical_path, file_name)

        with open(path) as f:
            return f.read()

    @property
    def initialization_template(self):
        return self._get_content(self.initialization)

    @property
    def configuration_template(self):
        return self._get_content(self.configuration)

    @property
    def start_database_template(self):
        return self._get_content(self.start_database)

    @property
    def start_replication_template(self):
        return self._get_content(self.start_replication)

    @property
    def metric_collector_template(self):
        return self._get_content(self.metric_collector)

    @property
    def configure_log_template(self):
        return self._get_content(self.configure_log)


class ReplicationTopology(BaseModel):

    class Meta:
        verbose_name_plural = "replication topologies"

    name = models.CharField(
        verbose_name=_("Topology name"), max_length=200
    )
    engine = models.ManyToManyField(
        Engine, verbose_name=_("Engine"), related_name='replication_topologies'
    )
    class_path = models.CharField(
        verbose_name=_("Replication Class"), max_length=200,
        help_text="your.module.name.Class"
    )
    details = models.CharField(max_length=200, null=True, blank=True)
    has_horizontal_scalability = models.BooleanField(
        verbose_name="Horizontal Scalability", default=False
    )
    can_resize_vm = models.BooleanField(
        verbose_name="Can Resize VM", default=True
    )
    can_clone_db = models.BooleanField(
        verbose_name="Can Clone DB", default=True
    )
    can_switch_master = models.BooleanField(
        verbose_name="Can Switch Master", default=True
    )
    can_upgrade_db = models.BooleanField(
        verbose_name="Can Upgrade DB", default=True
    )
    can_change_parameters = models.BooleanField(
        verbose_name="Can Change Parameters", default=True
    )
    can_reinstall_vm = models.BooleanField(
        verbose_name="Can Reinstall VM", default=True
    )
    can_setup_ssl = models.BooleanField(
        verbose_name="Can Setup SSL", default=False
    )
    can_recreate_slave = models.BooleanField(
        verbose_name="Can Recreate Slave", default=False
    )
    script = models.ForeignKey(
        Script, related_name='replication_topologies', null=True, blank=True
    )
    parameter = models.ManyToManyField(
        Parameter,
        verbose_name=_("Parameter"),
        related_name='replication_topologies',
        blank=True
    )

    def get_replication_topology_instance(self):
        topology_class = import_by_path(self.class_path)

        return topology_class()


class DiskOffering(BaseModel):

    name = models.CharField(
        verbose_name=_("Offering"), max_length=255, unique=True)
    size_kb = models.PositiveIntegerField(verbose_name=_("Size KB"))

    def size_gb(self):
        if self.size_kb:
            return round(self.converter_kb_to_gb(self.size_kb), 2)
    size_gb.short_description = "Size GB"

    def size_bytes(self):
        return self.converter_kb_to_bytes(self.size_kb)
    size_bytes.short_description = "Size Bytes"

    @classmethod
    def converter_kb_to_gb(cls, value):
        if value:
            return (value / 1024.0) / 1024.0

    @classmethod
    def converter_kb_to_bytes(cls, value):
        if value:
            return value * 1024.0

    @classmethod
    def converter_gb_to_kb(cls, value):
        if value:
            return (value * 1024) * 1024

    def __unicode__(self):
        return '{}'.format(self.name)

    @classmethod
    def first_greater_than(cls, base_size, exclude_id=None):
        disks = DiskOffering.objects.filter(
            size_kb__gt=base_size
        ).exclude(
            id=exclude_id
        ).order_by('size_kb')

        if not disks:
            raise NoDiskOfferingGreaterError(base_size)

        return disks[0]

    @classmethod
    def last_offering_available_for_auto_resize(cls):
        parameter_in_kb = cls.converter_gb_to_kb(
            Configuration.get_by_name_as_int(
                name='auto_resize_max_size_in_gb', default=100
            )
        )

        disks = DiskOffering.objects.filter(
            size_kb__lte=parameter_in_kb
        ).order_by('-size_kb')

        if not disks:
            raise NoDiskOfferingLesserError(parameter_in_kb)

        return disks[0]

    def __gt__(self, other):
        if other:
            return self.size_kb > other.size_kb

        return True

    def __lt__(self, other):
        if other:
            return self.size_kb < other.size_kb

        return True

    @property
    def is_last_auto_resize_offering(self):
        try:
            last_offering = (
                DiskOffering.last_offering_available_for_auto_resize()
            )
        except NoDiskOfferingLesserError:
            return False
        else:
            return self.id == last_offering.id


class Plan(BaseModel):

    PREPROVISIONED = 0
    CLOUDSTACK = 1

    PROVIDER_CHOICES = (
        (PREPROVISIONED, 'Pre Provisioned'),
        (CLOUDSTACK, 'Cloud Stack')
    )

    name = models.CharField(
        verbose_name=_("Plan name"), max_length=100, unique=True
    )
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(
        verbose_name=_("Is plan active"), default=True
    )
    is_ha = models.BooleanField(verbose_name=_("Is plan HA"), default=False)
    engine = models.ForeignKey(
        Engine, verbose_name=_("Engine"),
        related_name='plans'
    )
    replication_topology = models.ForeignKey(
        ReplicationTopology, verbose_name=_("Replication Topology"),
        related_name='replication_topology', null=True
    )
    has_persistence = models.BooleanField(
        verbose_name="Disk persistence", default=True,
        help_text="Check this option if the plan will save data in disk"
    )
    environments = models.ManyToManyField(Environment, related_name='plans')
    provider = models.IntegerField(choices=PROVIDER_CHOICES, default=0)
    max_db_size = models.IntegerField(
        default=0, verbose_name=_("Max database size (MB)"),
        help_text=_(("What is the maximum size of each database (MB). 0 "
                     "means unlimited."))
    )
    engine_equivalent_plan = models.ForeignKey(
        "Plan", null=True, blank=True,
        verbose_name=_("Engine version upgrade plan"),
        on_delete=models.SET_NULL,
        related_name='backwards_plan'
    )
    disk_offering = models.ForeignKey(
        DiskOffering, related_name="plans",
        on_delete=models.PROTECT, null=True, blank=True
    )
    migrate_plan = models.ForeignKey(
        "Plan", related_name='migrate_to', null=True, blank=True
    )
    stronger_offering = models.ForeignKey(
        Offering, related_name='main_offerings', null=True, blank=True
    )
    weaker_offering = models.ForeignKey(
        Offering, related_name='weaker_offerings', null=True, blank=True
    )
    migrate_engine_equivalent_plan = models.ForeignKey(
        "Plan", null=True, blank=True,
        verbose_name=_("Engine migrate plan"),
        on_delete=models.SET_NULL,
        related_name='backwards_engine_plan'
    )

    persistense_equivalent_plan = models.ForeignKey(
        "Plan", null=True, blank=True,
        verbose_name=_("Persisted/NoPersisted equivalent plan"),
        on_delete=models.SET_NULL,
        related_name='backwards_persisted_plan',
        help_text=_(("For persisted plans, the equivalent not persisted plan. "
                     "For not persisted plans, the equivalent persisted plan"
                     ))
    )

    @property
    def engine_type(self):
        return self.engine.engine_type

    @property
    def engines(self):
        return Engine.objects.filter(id=self.engine_id)

    @property
    def is_pre_provisioned(self):
        return self.provider == Plan.PREPROVISIONED

    @property
    def is_cloudstack(self):
        return self.provider == Plan.CLOUDSTACK

    @property
    def tsuru_label(self):

        return slugify("{}-{}".format(self.name, self.environment()))

    @property
    def available_plans_for_migration(self):
        if self.migrate_engine_equivalent_plan:
            return [self.migrate_engine_equivalent_plan]

        return []

#    @property
#    def stronger_offering(self):
#        return self.offerings.filter(weaker=False).first()
#
#    @property
#    def weaker_offering(self):
#        return self.offerings.filter(weaker=True).first()

    def get_equivalent_plan_for_env(self, env):
        filters = {
            "engine": self.engine,
            "environments": env,
            "replication_topology__in":
            self.replication_topology
                .core_replication_topologies
                .first().replication_topology
                .all(),
            "is_ha": self.is_ha,
            "has_persistence": self.has_persistence
        }
        return self._meta.model.objects.filter(
            **filters
        ).order_by(
            'stronger_offering__memory_size_mb',
            'stronger_offering__cpus'
        ).first()

    def __unicode__(self):
        return "%s" % (self.name)

    def environment(self):
        return ', '.join([e.name for e in self.environments.all()])

    class Meta:
        permissions = (
            ("view_plan", "Can view plans"),
        )

    @property
    def cloudstack_attr(self):
        if not self.is_cloudstack:
            return None

        return self.cs_plan_attributes.first()

    def validate_min_environment_bundles(self, environment):
        if self.is_ha and self.is_cloudstack:
            bundles_actives = self.cloudstack_attr.bundles_actives.count()

            if bundles_actives < environment.min_of_zones:
                raise EnvironmentError(
                    'Plan {} should has at least {} active bundles to {} '
                    'environment, currently have {}. Please contact '
                    'admin.'.format(
                        self.name, environment.min_of_zones,
                        environment.name, bundles_actives
                    )
                )

        return True

    @property
    def script(self):
        return self.replication_topology.script


class PlanAttribute(BaseModel):

    name = models.CharField(
        verbose_name=_("Plan attribute name"), max_length=200)
    value = models.CharField(
        verbose_name=_("Plan attribute value"), max_length=200)
    plan = models.ForeignKey(Plan, related_name="plan_attributes")

    def __unicode__(self):
        return "%s=%s (plan=%s)" % (self.name, self.value, self.plan)

    class Meta:
        permissions = (
            ("view_planattribute", "Can view plan attributes"),
        )


class DatabaseInfra(BaseModel):

    ALIVE = 1
    DEAD = 0
    ALERT = 2

    INFRA_STATUS = (
        (ALIVE, "Alive"),
        (DEAD, "Dead"),
        (ALERT, "Alert"))

    ALLOWTLS = 1
    PREFERTLS = 2
    REQUIRETLS = 3

    SSL_MODE = (
        (ALLOWTLS, "allowTLS"),
        (PREFERTLS, "preferTLS"),
        (REQUIRETLS, "requireTLS"))

    # migration stage
    NOT_STARTED = 0
    STAGE_1 = 1
    STAGE_2 = 2
    STAGE_3 = 3

    MIGRATION_STAGES = (
        (NOT_STARTED, "Not Started"),
        (STAGE_1, "Stage 1"),
        (STAGE_2, "Stage 2"),
        (STAGE_3, "Stage 3"))

    name = models.CharField(
        verbose_name=_("DatabaseInfra Name"),
        max_length=100,
        unique=True,
        help_text=_("This could be the fqdn associated to the databaseinfra."))
    user = models.CharField(
        verbose_name=_("DatabaseInfra User"),
        max_length=100,
        help_text=_(("Administrative user with permission to manage databases,"
                     " create users and etc.")),
        blank=True,
        null=False
    )
    password = EncryptedCharField(
        verbose_name=_("DatabaseInfra Password"),
        max_length=255, blank=True, null=False
    )
    engine = models.ForeignKey(
        Engine, related_name="databaseinfras", on_delete=models.PROTECT)
    plan = models.ForeignKey(
        Plan, related_name="databaseinfras", on_delete=models.PROTECT)
    environment = models.ForeignKey(
        Environment, related_name="databaseinfras", on_delete=models.PROTECT)
    capacity = models.PositiveIntegerField(
        default=1, help_text=_("How many databases is supported"))
    per_database_size_mbytes = models.IntegerField(
        default=0,
        verbose_name=_("Max database size (MB)"),
        help_text=_(("What is the maximum size of each database (MB). 0 means "
                     "unlimited."))
    )
    endpoint = models.CharField(
        verbose_name=_("DatabaseInfra Endpoint"),
        max_length=255,
        help_text=_(("Usually it is in the form host:port[,host_n:port_n]. "
                     "If the engine is mongodb this will be automatically "
                     "generated.")),
        blank=True,
        null=True
    )
    endpoint_dns = models.CharField(
        verbose_name=_("DatabaseInfra Endpoint (DNS)"),
        max_length=255,
        help_text=_(("Usually it is in the form host:port[,host_n:port_n]. "
                     "If the engine is mongodb this will be automatically "
                     "generated.")),
        blank=True,
        null=True
    )
    disk_offering = models.ForeignKey(
        DiskOffering, related_name="databaseinfras",
        on_delete=models.PROTECT, null=True
    )
    database_key = models.CharField(
        verbose_name=_("Database Key"), max_length=255, blank=True, null=True,
        help_text=_("Databases like MongoDB use a key file to replica set"),
    )
    name_prefix = models.CharField(
        verbose_name=_("DatabaseInfra Name Prefix"),
        max_length=10,
        blank=True,
        null=True,
        help_text=_("The prefix used on databaseinfra name."))
    name_stamp = models.CharField(
        verbose_name=_("DatabaseInfra Name Stamp"),
        max_length=20,
        blank=True,
        null=True,
        help_text=_("The stamp used on databaseinfra name sufix."))
    last_vm_created = models.IntegerField(
        verbose_name=_("Last VM created"),
        blank=True, null=True,
        help_text=_("Number of the last VM created."))
    ssl_configured = models.BooleanField(
        verbose_name=_("SSL is Configured"),
        default=False)
    ssl_mode = models.IntegerField(
        choices=SSL_MODE,
        verbose_name=_("SSL Mode"),
        null=True,
        blank=True,
        default=None)
    backup_hour = models.IntegerField(
        verbose_name=_("Backup hour"),
        blank=False,
        null=False,
        help_text=_("Value default"))
    engine_patch = models.ForeignKey(
        EnginePatch, related_name="databaseinfras",
        on_delete=models.PROTECT, null=True)
    maintenance_window = models.IntegerField(
        default=0,
        blank=False,
        null=False,
        help_text=_("Window of maintenance")
    )
    maintenance_day = models.IntegerField(
        default=0,
        blank=False,
        null=False,
        help_text=_("Maintenance day")
    )

    pool = models.ForeignKey(
        'physical.Pool',
        related_name="infra",
        null=True, blank=True
    )

    service_account = models.CharField(
        verbose_name=_("Service Account"),
        max_length=255,
        blank=True,
        null=True,
    )

    migration_stage = models.IntegerField(
        choices=MIGRATION_STAGES,
        verbose_name=_("Migration Stage"),
        null=False,
        blank=False,
        default=NOT_STARTED)

    def __unicode__(self):
        return self.name

    class Meta:
        permissions = (
            ("view_databaseinfra", "Can view database infras"),
        )

    def clean(self, *args, **kwargs):
        plan_exists = self.plan.environments.filter(
            pk=self.environment_id
        ).exists()

        if (not self.environment_id or not self.plan_id) or not plan_exists:
            raise ValidationError({'engine': _("Invalid environment")})

    @property
    def configure_backup_hour(self):
        return Configuration.get_by_name_as_int(
            'backup_hour'
        )

    @property
    def configure_maintenance_window(self):
        return Configuration.get_by_name_as_int(
            'maintenance_window'
        )

    @property
    def configure_maintenance_day(self):
        return Configuration.get_by_name_as_int(
            'maintenance_day'
        )

    @property
    def offering(self):
        database_instances = self.get_driver().get_database_instances()

        return database_instances and database_instances[0].offering

    @property
    def engine_name(self):
        if self.engine and self.engine.engine_type:
            return self.engine.engine_type.name

        return None

    @property
    def per_database_size_bytes(self):
        if self.disk_offering and self.engine.engine_type.name != 'redis':
            return self.disk_offering.size_bytes()

        return int(
            self.get_parameter_value_by_parameter_name('maxmemory') or
            self.get_dbaas_parameter_default_value('maxmemory')
        )

    @property
    def used(self):
        """ How many databases is allocated in this datainfra """

        return self.databases.count()

    @property
    def has_custom_parameter(self):
        return DatabaseInfraParameter.objects.filter(
            databaseinfra=self
        ).exists()

    @property
    def available(self):
        """ How many databases still supports this datainfra.
        Returns
            0 if datainfra is full
            < 0 if datainfra is overcapacity
            > 0 if datainfra can support more databases
        """

        return self.capacity - self.used

    @property
    def set_require_ssl_for_users(self):
        return self.get_driver().set_require_ssl_for_users

    @property
    def set_require_ssl_for_databaseinfra(self):
        return self.get_driver().set_require_ssl_for_databaseinfra

    @classmethod
    def get_unique_databaseinfra_name(cls, base_name):
        """
        try diferent names if first exists, like NAME-1, NAME-2, ...
        """
        i = 0
        name = base_name

        while DatabaseInfra.objects.filter(name=name).exists():
            i += 1
            name = "%s-%d" % (base_name, i)
        LOG.info("databaseinfra unique name to be returned: %s" % name)

        return name

    @classmethod
    def get_active_for(cls, plan=None, environment=None):
        """Return active databaseinfras for selected plan and environment"""
        datainfras = DatabaseInfra.objects.filter(
            plan=plan,
            environment=environment,
            instances__is_active=True
        ).distinct()
        LOG.debug(
            ('Total of datainfra with filter plan {} and environment '
             '{}: {}').format(plan, environment, len(datainfras))
        )

        return datainfras

    @classmethod
    def best_for(cls, plan, environment, name):
        """ Choose the best DatabaseInfra for another database """
        datainfras = list(
            DatabaseInfra.get_active_for(plan=plan, environment=environment))

        if not datainfras:
            return None
        datainfras.sort(key=lambda di: -di.available)
        best_datainfra = datainfras[0]

        if best_datainfra.available <= 0:
            return None

        return best_datainfra

    @property
    def earliest_ssl_expire_at(self):
        return self.instances.earliest(
            'hostname__ssl_expire_at'
        ).hostname.ssl_expire_at

    def check_instances_status(self):
        alive_instances = self.instances.filter(status=Instance.ALIVE).count()
        dead_instances = self.instances.filter(status=Instance.DEAD).count()

        if dead_instances == 0:
            status = self.ALIVE
        elif alive_instances == 0:
            status = self.DEAD
        else:
            status = self.ALERT

        return status

    def get_driver(self):
        import drivers

        return drivers.factory_for(self)

    def get_info(self, force_refresh=False):
        if not self.pk:
            return None
        key = "datainfra:info:%d" % self.pk
        info = None

        if not force_refresh:
            # try use cache
            info = cache.get(key)

        if info is None:
            try:
                info = self.get_driver().info()
                cache.set(key, info)
            except Exception:
                # To make cache possible if the database hangs the connection
                # with no reply
                db_name = self.databases.all()[0].name
                info = DatabaseInfraStatus(databaseinfra_model=self.__class__)
                info.databases_status[db_name] = DatabaseInfraStatus(
                    databaseinfra_model=self.__class__)
                info.databases_status[db_name].is_alive = False

                cache.set(key, info)

        return info

    @property
    def disk_used_size_in_kb(self):
        greater_disk = None

        for instance in self.instances.all():
            for disk in instance.hostname.volumes.all():
                if disk.used_size_kb > greater_disk:
                    greater_disk = disk.used_size_kb

        return greater_disk

    @property
    def disk_used_size_in_gb(self):
        disk_used_size_in_kb = self.disk_used_size_in_kb

        if disk_used_size_in_kb:
            return round(disk_used_size_in_kb * (1.0 / 1024.0 / 1024.0), 2)

        return disk_used_size_in_kb

    def update_database_key(self):
        self.database_key = self.get_driver().database_key
        self.save()

    def update_name_prefix_and_stamp(self):
        instance = self.instances.all()[0]
        hostname = instance.hostname.hostname
        prefix = hostname.split('-')[0]
        stamp = hostname.split('-')[2].split('.')[0]
        self.name_prefix = prefix
        self.name_stamp = stamp
        self.save()

    def update_last_vm_created(self):
        hosts = []

        for instance in self.instances.all():
            hosts.append(instance.hostname.hostname)
        self.last_vm_created = len(set(hosts))
        self.save()

    def get_dbaas_parameter_default_value(self, parameter_name):
        from physical.configurations import configuration_factory
        parameter_name = parameter_name.replace('-', '_')
        configuration = configuration_factory(
            self,
            # self.cs_dbinfra_offering.get().offering.memory_size_mb
            self.offering.memory_size_mb
        )

        return getattr(configuration, parameter_name).default

    def get_parameter_value(self, parameter):
        try:
            dbinfraparameter = DatabaseInfraParameter.objects.get(
                databaseinfra=self,
                parameter=parameter
            )
        except DatabaseInfraParameter.DoesNotExist:
            return None
        else:
            return dbinfraparameter.value

    def get_parameter_value_by_parameter_name(self, parameter_name):
        parameter_name_hyphen = parameter_name.replace('_', '-')
        try:
            dbinfraparameter = DatabaseInfraParameter.objects.get(
                Q(parameter__name=parameter_name)
                | Q(parameter__name=parameter_name_hyphen),
                databaseinfra=self,
            )
        except DatabaseInfraParameter.DoesNotExist:
            return None
        else:
            return dbinfraparameter.value

    @property
    def hosts(self):
        hosts = []

        for instance in self.instances.all():
            if instance.hostname not in hosts:
                hosts.append(instance.hostname)

        return hosts

    @property
    def topology(self):
        return (self.plan.replication_topology
                .get_replication_topology_instance())

    def recreate_slave_steps(self):
        return self.topology.get_recreate_slave_steps()

    def restart_database_steps(self):
        return self.topology.get_restart_database_steps()

    def update_ssl_steps(self):
        return self.topology.get_update_ssl_steps()

    def remove_readonly_instance_steps(self):
        return self.topology.get_remove_readonly_instance_steps()

    def check_rfs_size(self, size):
        """This method checks if hosts size are equal or greater than a given
        value."""

        for host in self.hosts:
            if host.root_size_gb < size:
                return False

        return True


class Host(BaseModel):
    hostname = models.CharField(
        verbose_name=_("Hostname"), max_length=255, unique=True)
    address = models.CharField(verbose_name=_("Host address"), max_length=255)
    monitor_url = models.URLField(
        verbose_name=_("Monitor Url"), max_length=500, blank=True, null=True)
    future_host = models.ForeignKey(
        "Host", null=True, blank=True, on_delete=models.SET_NULL)
    os_description = models.CharField(
        verbose_name=_("Operating system description"),
        max_length=255, null=True, blank=True)
    offering = models.ForeignKey(Offering, null=True)
    user = models.CharField(max_length=255, blank=True, null=True)
    password = EncryptedCharField(max_length=255, blank=True, null=True)
    private_key = EncryptedTextField(
        verbose_name="Private Key", blank=True, null=True
    )
    identifier = models.CharField(
        verbose_name=_("Identifier"),
        max_length=255, default=''
    )
    root_size_gb = models.FloatField(
        verbose_name=_("RFS Size (GB)"), null=True, blank=True
    )
    ssl_expire_at = models.DateField(
        verbose_name=_("ssl_expire_at"),
        auto_now_add=False,
        blank=True,
        null=True)
    version = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        return self.hostname

    class Meta:
        permissions = (
            ("view_host", "Can view hosts"),
        )

    def update_os_description(self, ):
        from util import get_host_os_description
        os = get_host_os_description(self)
        self.os_description = os
        self.save()

    def database_instance(self):
        for instance in self.instances.all():
            if instance.is_database:
                return instance

        return None

    def non_database_instance(self):
        for instance in self.instances.all():
            if not instance.is_database:
                return instance

        return None

    @property
    def is_database(self):
        return self.database_instance() is not None

    @property
    def past_host(self):
        return self.host_set.first()

    @property
    def infra(self):
        instance = self.instances.first()
        if not instance:
            instance = self.past_host.instances.first()
        return instance.databaseinfra

    @property
    def driver(self):
        return self.infra.get_driver()

    @property
    def commands(self):
        return HostCommands(self)

    @property
    def ssh(self):
        return HostSSH(
            address=self.address,
            username=self.user,
            password=self.password,
            private_key=self.private_key
        )

    @staticmethod
    def run_script(address, username, script,
                   password=None, private_key=None):
        return HostSSH(
            address=address,
            username=username,
            password=password,
            private_key=private_key
        ).run_script(script)

    @property
    def is_ol6(self):
        return ' 6.' in self.os_description

    @property
    def is_ol7(self):
        return ' 7.' in self.os_description


class Volume(BaseModel):
    host = models.ForeignKey(
        Host, related_name="volumes",
        null=True,
        on_delete=models.SET_NULL
    )
    identifier = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    total_size_kb = models.IntegerField(null=True, blank=True)
    used_size_kb = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        name = "Volume: {}".format(self.identifier)

        if not self.is_active:
            name = "(Inactive){}".format(name)

        return name


class Instance(BaseModel):

    DEAD = 0
    ALIVE = 1
    INITIALIZING = 2

    INFRA_STATUS = (
        (DEAD, 'Dead'),
        (ALIVE, 'Alive'),
        (INITIALIZING, 'Initializing')
    )

    NONE = 0
    MYSQL = 1
    MONGODB = 2
    MONGODB_ARBITER = 3
    REDIS = 4
    REDIS_SENTINEL = 5
    MYSQL_PERCONA = 6

    DATABASE_TYPE = (
        (NONE, 'None'),
        (MYSQL, 'MySQL'),
        (MONGODB, 'MongoDB'),
        (MONGODB_ARBITER, 'Arbiter'),
        (REDIS, 'Redis'),
        (REDIS_SENTINEL, 'Sentinel'),
        (MYSQL_PERCONA, 'MySQLPercona'),
    )

    dns = models.CharField(verbose_name=_("Instance dns"), max_length=200)
    address = models.CharField(
        verbose_name=_("Instance address"), max_length=200)
    port = models.IntegerField(verbose_name=_("Instance port"))
    databaseinfra = models.ForeignKey(
        DatabaseInfra, related_name="instances", on_delete=models.CASCADE)
    is_active = models.BooleanField(
        verbose_name=_("Is instance active"), default=True)
    hostname = models.ForeignKey(Host, related_name="instances")
    status = models.IntegerField(choices=INFRA_STATUS, default=2)
    instance_type = models.IntegerField(choices=DATABASE_TYPE, default=0)
    future_instance = models.ForeignKey(
        "Instance", null=True, blank=True, on_delete=models.SET_NULL)
    read_only = models.BooleanField(
        verbose_name=_("Is instance read only"), default=False)
    shard = models.IntegerField(null=True, blank=True)
    used_size_in_bytes = models.FloatField(null=True, blank=True)
    total_size_in_bytes = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = (
            ('address', 'port',)
        )
        permissions = (
            ("view_instance", "Can view instances"),
        )

    @property
    def initialization_variables(self):
        return self.databaseinfra.get_driver().initialization_parameters(self)

    @property
    def scripts(self):
        return DatabaseScript(self)

    @property
    def is_alive(self):
        return self.status == self.ALIVE

    @property
    def is_database(self):
        return self.instance_type in (
            self.MYSQL, self.MONGODB, self.REDIS, self.MYSQL_PERCONA
        )

    @property
    def offering(self):
        try:
            host_offering = self.hostname.offering
        except Offering.DoesNotExist:
            host_offering = None

        if host_offering:
            return host_offering

        if not self.is_database:
            return self.databaseinfra.plan.weaker_offering

        return self.databaseinfra.plan.stronger_offering

    @property
    def is_redis(self):
        return self.instance_type == self.REDIS

    @property
    def is_sentinel(self):
        return self.instance_type == self.REDIS_SENTINEL

    @property
    def is_mysql(self):
        return self.instance_type in (self.MYSQL, self.MYSQL_PERCONA)

    @property
    def connection(self):
        return "%s:%s" % (self.address, self.port)

    def __unicode__(self):
        return "%s:%s" % (self.dns, self.port)

    def clean(self, *args, **kwargs):
        if self.instance_type == self.MONGODB_ARBITER or not self.is_active:
            # no connection check is needed

            return

        LOG.debug('Checking instance %s (%s) status...',
                  self.connection, self.databaseinfra)
        # self.clean_fields()

        if not self.databaseinfra.engine_id:
            raise ValidationError({'engine': _("No engine selected")})

        from drivers import factory_for
        from drivers.errors import GenericDriverError, ConnectionError, \
            AuthenticationError

        try:
            engine = factory_for(self.databaseinfra)
            # validate instance connection before saving
            engine.check_status(instance=self)
            LOG.debug('Instance %s is ok', self)
        except AuthenticationError as e:
            LOG.exception(e)
            # at django 1.5, model validation throught form doesn't use field
            # name in ValidationError.
            # I put here, because I expected this problem can be solved in next
            # versions
            raise ValidationError({'user': e.message})
        except ConnectionError as e:
            LOG.exception(e)
            raise ValidationError({'instance': e.message})
        except GenericDriverError as e:
            LOG.exception(e)
            raise ValidationError(e.message)

    def check_status(self):
        try:
            status = self.databaseinfra.get_driver().check_status(
                instance=self)

            return status
        except Exception:
            return False

    @property
    def is_slave(self):
        return not self.is_current_write

    @property
    def is_current_write(self):
        try:
            driver = self.databaseinfra.get_driver()

            return driver.check_instance_is_master(
                instance=self, default_timeout=True
            )
        except Exception:
            return False

    def status_html(self):
        html_default = '<span class="label label-{}">{}</span>'

        if self.status == self.DEAD:
            status = html_default.format("important", "Dead")
        elif self.status == self.ALIVE:
            status = html_default.format("success", "Alive")
        elif self.status == self.INITIALIZING:
            status = html_default.format("warning", "Initializing")
        else:
            status = html_default.format("info", "N/A")

        return format_html(status)

    def update_status(self):
        self.status = Instance.DEAD

        if self.check_status():
            self.status = Instance.ALIVE

        self.save(update_fields=['status'])

    @property
    def static_ip(self):
        try:
            return Ip.objects.get(
                identifier=Ip.identifier_template.format(
                    self.dns.split(".")[0]
                )
            )
        except Ip.DoesNotExist:
            return

    @property
    def has_static_ip_allocated_by_dns(self):

        return Ip.objects.filter(
            identifier=Ip.identifier_template.format(
                self.dns.split(".")[0]
            ).exists()
        )


class DatabaseInfraParameter(BaseModel):

    databaseinfra = models.ForeignKey(DatabaseInfra)
    parameter = models.ForeignKey(Parameter)
    value = models.CharField(max_length=200)
    current_value = models.CharField(max_length=200)
    applied_on_database = models.BooleanField(default=False)
    reset_default_value = models.BooleanField(default=False)

    class Meta:
        unique_together = (
            ('databaseinfra', 'parameter', )
        )

    def __unicode__(self):
        return "{}_{}:{}".format(self.databaseinfra.name,
                                 self.parameter.name, self.value)

    @classmethod
    def update_parameter_value(cls, databaseinfra, parameter, value):
        obj, created = cls.objects.get_or_create(
            databaseinfra=databaseinfra,
            parameter=parameter,
            defaults={
                'value': value,
                'current_value': databaseinfra.get_dbaas_parameter_default_value(  # noqa
                    parameter_name=parameter.name
                )
            },
        )

        if created:
            return True

        if obj.value == value:
            return False

        obj.value = value
        obj.applied_on_database = False
        obj.reset_default_value = False
        obj.save()

        return True

    @classmethod
    def set_reset_default(cls, databaseinfra, parameter):
        try:
            obj = cls.objects.get(databaseinfra=databaseinfra,
                                  parameter=parameter)
        except cls.DoesNotExist:
            return False
        else:
            obj.reset_default_value = True
            obj.applied_on_database = False
            obj.value = databaseinfra.get_dbaas_parameter_default_value(
                parameter_name=parameter.name
            )
            obj.save()

            return True

    @classmethod
    def get_databaseinfra_reseted_parameters(cls, databaseinfra):
        return cls.objects.filter(
            databaseinfra=databaseinfra,
            applied_on_database=False,
            reset_default_value=True,
        )

    @classmethod
    def get_databaseinfra_changed_parameters(cls, databaseinfra):
        return cls.objects.filter(
            databaseinfra=databaseinfra,
            applied_on_database=False,
        )

    @classmethod
    def get_databaseinfra_changed_not_reseted_parameters(cls, databaseinfra):
        return cls.objects.filter(
            databaseinfra=databaseinfra,
            applied_on_database=False,
            reset_default_value=False,
        )

    @classmethod
    def load_database_configs(cls, infra):
        parameters = infra.plan.replication_topology.parameter.all()
        physical_parameters = infra.get_driver().get_configuration()

        for parameter in parameters:
            if parameter.name not in physical_parameters:
                LOG.warning(
                    'Parameter {} not found in physical configuration'.format(
                        parameter.name
                    )
                )

                continue

            physical_value = str(physical_parameters[parameter.name])
            default_value = infra.get_dbaas_parameter_default_value(
                parameter_name=parameter.name
            )

            if physical_value != default_value:
                LOG.info('Updating parameter {} value {} to {}'.format(
                    parameter, default_value, physical_value
                ))
                obj, created = cls.objects.get_or_create(
                    databaseinfra=infra,
                    parameter=parameter,
                    defaults={
                        'value': physical_value,
                        'current_value': physical_value,
                        'applied_on_database': True,
                        'reset_default_value': False
                    },
                )

                if not created:
                    obj.value = physical_value
                    obj.current_value = physical_value
                    obj.applied_on_database = True
                    obj.reset_default_value = False
                    obj.save()


class TopologyParameterCustomValue(BaseModel):
    topology = models.ForeignKey(
        ReplicationTopology, related_name="param_custom_values"
    )
    parameter = models.ForeignKey(
        Parameter, related_name="topology_custom_values"
    )
    attr_name = models.CharField(
        verbose_name='Custom engine attribute',
        max_length=200
    )

    class Meta():
        unique_together = ('topology', 'parameter')


class VipWithoutFutureVip(models.Manager):
    def get_queryset(self):
        return super(VipWithoutFutureVip, self).get_queryset().exclude(
            original_vip__isnull=False
        )


class Vip(BaseModel):
    objects = VipWithoutFutureVip()
    original_objects = models.Manager()
    infra = models.ForeignKey(
        DatabaseInfra, related_name="vips")
    identifier = models.CharField(verbose_name=_("Identifier"), max_length=200)
    original_vip = models.ForeignKey(
        "Vip", null=True, blank=True, on_delete=models.SET_NULL
    )

    def __unicode__(self):
        return 'Vip of infra {}'.format(self.infra.name)

    @classmethod
    def get_vip_from_databaseinfra(cls, databaseinfra):
        from workflow.steps.util.base import VipProviderClient
        vip_identifier = cls.objects.get(infra=databaseinfra).identifier
        client = VipProviderClient(databaseinfra.environment)

        return client.get_vip(vip_identifier)


class Cloud(BaseModel):
    name = models.CharField(
        verbose_name="Name", max_length=100, help_text="Cloud name")

    def __unicode__(self):
        return self.name


class Pool(BaseModel):
    name = models.CharField(
        verbose_name=_("Pool Name"), max_length=200, unique=True)

    cluster_name = models.CharField(
        verbose_name=_("Cluster name"), max_length=255)

    cluster_id = models.CharField(
        verbose_name=_("Cluster ID"), max_length=255)

    project_id = models.CharField(
        verbose_name=_("Project ID"), max_length=255, default="")

    cluster_endpoint = models.CharField(
        verbose_name=_("Cluster EndPoint"), max_length=255,
        blank=False, null=False
    )

    rancher_endpoint = models.CharField(
        verbose_name=_("Rancher EndPoint"), max_length=255)

    rancher_token = EncryptedCharField(
        verbose_name=_("Rancher Token"),
        max_length=255, blank=False, null=False
    )

    dbaas_token = EncryptedCharField(
        verbose_name=_("DBaaS Token"), max_length=255, blank=False, null=False
    )

    environment = models.ForeignKey(
        'Environment', related_name='pools'
    )

    domain = models.CharField(
        verbose_name=_("Domain"), max_length=255, blank=False, null=False
    )

    vpc = models.CharField(
        verbose_name=_("VPC"), max_length=255, blank=False, null=False,
        help_text=_("VPC used by K8S network")
    )

    storageclass = models.CharField(
        verbose_name=_("Storage Class"),
        max_length=255, blank=False, null=False,
        help_text=_("K8S Storage class created by dbaas-pool")
    )

    teams = models.ManyToManyField('account.Team', related_name='pools')

    def __unicode__(self):
        return '{}'.format(self.name)

    @property
    def as_headers(self):
        return {
            "K8S-Token": self.rancher_token,
            "K8S-Endpoint": self.cluster_endpoint,
            "K8S-Project-Id": self.project_id,
            "K8S-Domain": self.domain,
            "K8S-Storage-Type": self.storageclass,
            "K8S-Verify-Ssl": "false",
        }


class Ip(BaseModel):

    identifier_template = "{}-static-ip"

    identifier = models.CharField(
        verbose_name=_("Ip Identifier"),
        max_length=200,
        null=True, blank=True
    )
    address = models.CharField(
        verbose_name=_("Ip address"), max_length=200)
    instance = models.ForeignKey(
        "Instance", null=True, blank=True, on_delete=models.SET_NULL)

    def __unicode__(self):
        return self.identifier


class VipInstanceGroup(BaseModel):
    vip = models.ForeignKey(Vip)
    name = models.CharField(verbose_name=_("Name"), max_length=60)
    identifier = models.CharField(verbose_name=_("Identifier"), max_length=200)

    def __unicode__(self):
        return 'Vip instance groups {}'.format(self.vip.infra.name)

    class Meta:
        unique_together = (
            ('vip', 'name')
        )


class CoreReplicationTopology(BaseModel):
    class Meta:
        verbose_name_plural = "core replication topologies"

    name = models.CharField(
        verbose_name=_("Core topology name"), max_length=200
    )
    replication_topology = models.ManyToManyField(
        ReplicationTopology, related_name='core_replication_topologies'
    )




##########################################################################
# Exceptions
##########################################################################


class PlanNotFound(Exception):
    pass


##########################################################################
# SIGNALS
##########################################################################


@receiver(pre_delete, sender=Instance)
def instance_pre_delete(sender, **kwargs):
    """
    instance pre delete
    """

    from backup.models import Snapshot
    import datetime

    instance = kwargs.get('instance')

    LOG.debug("instance %s pre-delete" % (instance))

    snapshots = Snapshot.objects.filter(
        instance=instance, purge_at__isnull=True)

    for snapshot in snapshots:
        LOG.debug("Setting snapshopt %s purge_at time" % (snapshot))
        snapshot.purge_at = datetime.datetime.now()
        snapshot.save()

    LOG.debug("instance pre-delete triggered")


@receiver(post_save, sender=DatabaseInfra)
def databaseinfra_post_save(sender, **kwargs):
    """
    databaseinfra post save
    """
    databaseinfra = kwargs.get('instance')
    LOG.debug("databaseinfra post-save triggered")
    LOG.debug("databaseinfra %s endpoint: %s" %
              (databaseinfra, databaseinfra.endpoint))


simple_audit.register(
    EngineType, Engine, Plan, PlanAttribute, DatabaseInfra, Instance)
