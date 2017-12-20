# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import logging
import simple_audit
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.db import models
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields.encrypted import EncryptedCharField

from util.models import BaseModel
from drivers import DatabaseInfraStatus
from system.models import Configuration
from physical.errors import NoDiskOfferingGreaterError, NoDiskOfferingLesserError


LOG = logging.getLogger(__name__)


class Environment(BaseModel):
    name = models.CharField(
        verbose_name=_("Environment"), max_length=100, unique=True)
    min_of_zones = models.PositiveIntegerField(default=1)

    migrate_environment = models.ForeignKey(
        'Environment', related_name='migrate_to', blank=True, null=True
    )

    def __unicode__(self):
        return '%s' % (self.name)

    def active_plans(self):
        return self.plans.filter(is_active=True)


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
        help_text="Script that will be sent as an user-data to provision the virtual machine"
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

    def __unicode__(self):
        return "%s_%s" % (self.name, self.version)

    @property
    def is_redis(self):
        return self.name == 'redis'


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
        max_length = 100,
        choices = TYPE_CHOICES,
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
    script = models.ForeignKey(
        Script, related_name='replication_topologies', null=True, blank=True
    )
    parameter = models.ManyToManyField(
        Parameter,
        verbose_name=_("Parameter"),
        related_name='replication_topologies',
        blank=True
    )


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
            last_offering = DiskOffering.last_offering_available_for_auto_resize()
        except NoDiskOfferingLesserError:
            return False
        else:
            return self.id == last_offering.id


class Plan(BaseModel):

    PREPROVISIONED = 0
    CLOUDSTACK = 1

    PROVIDER_CHOICES = (
        (PREPROVISIONED, 'Pre Provisioned'),
        (CLOUDSTACK, 'Cloud Stack'),
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
        help_text=_("What is the maximum size of each database (MB). 0 means unlimited.")
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

    name = models.CharField(verbose_name=_("DatabaseInfra Name"),
                            max_length=100,
                            unique=True,
                            help_text=_("This could be the fqdn associated to the databaseinfra."))
    user = models.CharField(verbose_name=_("DatabaseInfra User"),
                            max_length=100,
                            help_text=_(
                                "Administrative user with permission to manage databases, create users and etc."),
                            blank=True,
                            null=False)
    password = EncryptedCharField(
        verbose_name=_("DatabaseInfra Password"), max_length=255, blank=True, null=False)
    engine = models.ForeignKey(
        Engine, related_name="databaseinfras", on_delete=models.PROTECT)
    plan = models.ForeignKey(
        Plan, related_name="databaseinfras", on_delete=models.PROTECT)
    environment = models.ForeignKey(
        Environment, related_name="databaseinfras", on_delete=models.PROTECT)
    capacity = models.PositiveIntegerField(
        default=1, help_text=_("How many databases is supported"))
    per_database_size_mbytes = models.IntegerField(default=0,
                                                   verbose_name=_(
                                                       "Max database size (MB)"),
                                                   help_text=_("What is the maximum size of each database (MB). 0 means unlimited."))
    endpoint = models.CharField(verbose_name=_("DatabaseInfra Endpoint"),
                                max_length=255,
                                help_text=_(
                                    "Usually it is in the form host:port[,host_n:port_n]. If the engine is mongodb this will be automatically generated."),
                                blank=True,
                                null=True)

    endpoint_dns = models.CharField(verbose_name=_("DatabaseInfra Endpoint (DNS)"),
                                    max_length=255,
                                    help_text=_(
                                        "Usually it is in the form host:port[,host_n:port_n]. If the engine is mongodb this will be automatically generated."),
                                    blank=True,
                                    null=True)
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

    def __unicode__(self):
        return self.name

    class Meta:
        permissions = (
            ("view_databaseinfra", "Can view database infras"),
        )

    def clean(self, *args, **kwargs):
        if (not self.environment_id or not self.plan_id) or not self.plan.environments.filter(pk=self.environment_id).exists():
            raise ValidationError({'engine': _("Invalid environment")})

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
        return DatabaseInfraParameter.objects.filter(databaseinfra=self).exists()

    @property
    def available(self):
        """ How many databases still supports this datainfra.
        Returns
            0 if datainfra is full
            < 0 if datainfra is overcapacity
            > 0 if datainfra can support more databases
        """
        return self.capacity - self.used

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
            plan=plan, environment=environment, instances__is_active=True).distinct()
        LOG.debug('Total of datainfra with filter plan %s and environment %s: %s',
                  plan, environment, len(datainfras))
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
            except:
                # To make cache possible if the database hangs the connection
                # with no reply
                info = DatabaseInfraStatus(databaseinfra_model=self.__class__)
                info.databases_status[self.databases.all()[0].name] = DatabaseInfraStatus(
                    databaseinfra_model=self.__class__)
                info.databases_status[
                    self.databases.all()[0].name].is_alive = False

                cache.set(key, info)
        return info

    @property
    def disk_used_size_in_kb(self):
        greater_disk = None
        for instance in self.instances.all():
            for disk in instance.hostname.nfsaas_host_attributes.all():
                if disk.nfsaas_used_size_kb > greater_disk:
                    greater_disk = disk.nfsaas_used_size_kb
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
            self.cs_dbinfra_offering.get().offering.memory_size_mb
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
        try:
            dbinfraparameter = DatabaseInfraParameter.objects.get(
                databaseinfra=self,
                parameter__name=parameter_name
            )
        except DatabaseInfraParameter.DoesNotExist:
            return None
        else:
            return dbinfraparameter.value

    @property
    def hosts(self):
        hosts = set()
        for instance in self.instances.all():
            hosts.add(instance.hostname)
        return hosts


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

    def __unicode__(self):
        return self.hostname

    class Meta:
        permissions = (
            ("view_host", "Can view hosts"),
        )

    def update_os_description(self, ):
        from util import get_host_os_description

        try:
            os = get_host_os_description(self)
        except Exception as e:
            error = "Could not get os description for host {}. Error: {}"
            error = error.format(self, e)
            LOG.error(error)
        else:
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
    def active_disk(self):
        return self.nfsaas_host_attributes.get(is_active=True)


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

    DATABASE_TYPE = (
        (NONE, 'None'),
        (MYSQL, 'MySQL'),
        (MONGODB, 'MongoDB'),
        (MONGODB_ARBITER, 'Arbiter'),
        (REDIS, 'Redis'),
        (REDIS_SENTINEL, 'Sentinel'),
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
    def is_alive(self):
        return self.status == self.ALIVE

    @property
    def is_database(self):
        return self.instance_type in (self.MYSQL, self.MONGODB, self.REDIS)

    @property
    def is_redis(self):
        return self.instance_type == self.REDIS

    @property
    def is_sentinel(self):
        return self.instance_type == self.REDIS_SENTINEL

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
        except AuthenticationError, e:
            LOG.exception(e)
            # at django 1.5, model validation throught form doesn't use field name in ValidationError.
            # I put here, because I expected this problem can be solved in next
            # versions
            raise ValidationError({'user': e.message})
        except ConnectionError, e:
            LOG.exception(e)
            raise ValidationError({'instance': e.message})
        except GenericDriverError, e:
            LOG.exception(e)
            raise ValidationError(e.message)

    def check_status(self):
        try:
            status = self.databaseinfra.get_driver().check_status(
                instance=self)
            return status
        except:
            return False

    @property
    def is_current_write(self):
        try:
            driver = self.databaseinfra.get_driver()
            return driver.check_instance_is_master(instance=self)
        except:
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
                'current_value': databaseinfra.get_dbaas_parameter_default_value(
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
