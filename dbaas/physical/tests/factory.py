# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import factory
# TODO: Remove this specific dbaas imports
from dbaas_nfsaas.models import HostAttr
from dbaas_cloudstack.models import DatabaseInfraOffering, CloudStackOffering
from physical import models


class EnvironmentFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Environment

    name = factory.Sequence(lambda n: 'env-{0}'.format(n))


class EngineTypeFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.EngineType
    FACTORY_DJANGO_GET_OR_CREATE = ('name',)

    name = "fake"


class EngineFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Engine
    FACTORY_DJANGO_GET_OR_CREATE = ('version', 'engine_type',)

    version = 'unique'
    engine_type = factory.SubFactory(EngineTypeFactory)


class HostFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Host

    hostname = factory.Sequence(lambda n: 'host{0}.mydomain.com'.format(n))


class DiskOfferingFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.DiskOffering

    name = factory.Sequence(lambda n: 'disk-offering-{0}'.format(n))
    size_kb = 1048576  # 1gb


class ReplicationTopologyFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.ReplicationTopology

    name = factory.Sequence(lambda n: 'disk-offering-{0}'.format(n))
    class_path = 'drivers.replication_topologies.base.FakeTestTopology'

class ParameterFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Parameter

    engine_type = factory.SubFactory(EngineTypeFactory)
    name = factory.Sequence(lambda n: 'parameter-{0}'.format(n))
    allowed_values = ''
    parameter_type = ''



class PlanFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Plan

    name = factory.Sequence(lambda n: 'plan-{0}'.format(n))
    is_active = True
    engine = factory.SubFactory(EngineFactory)
    provider = 0
    disk_offering = factory.SubFactory(DiskOfferingFactory)
    replication_topology = factory.SubFactory(ReplicationTopologyFactory)

    @factory.post_generation
    def environments(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for env in extracted:
                self.environments.add(env)
        else:
            self.environments.add(EnvironmentFactory())


class DatabaseInfraFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.DatabaseInfra

    name = factory.Sequence(lambda n: 'databaseinfra-{0}'.format(n))
    user = 'admin'
    password = '123456'
    endpoint = '127.0.0.1:1111'
    engine = factory.SubFactory(EngineFactory)
    capacity = 2
    per_database_size_mbytes = 5 * 1024 * 1024
    disk_offering = factory.SubFactory(DiskOfferingFactory)

    @factory.lazy_attribute
    def environment(self):
        # because environment is part of plan many-to-many relation, I use
        # lazy attribute instead subfactory, to ensure environment is persisted
        # since I used BUILD STRATEGY
        return EnvironmentFactory()

    @factory.lazy_attribute
    def plan(self):
        return PlanFactory(environments=[self.environment])


class CloudStackOfferingFactory(factory.DjangoModelFactory):
    FACTORY_FOR = CloudStackOffering

    serviceofferingid = '999'
    name = factory.Sequence(lambda n: 'CloudStackOffering-{0}'.format(n))
    weaker = False
    memory_size_mb = 998


class DatabaseInfraOfferingFactory(factory.DjangoModelFactory):
    FACTORY_FOR = DatabaseInfraOffering

    databaseinfra = factory.SubFactory(DatabaseInfraFactory)
    offering = factory.SubFactory(CloudStackOfferingFactory)


class InstanceFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Instance

    address = '127.0.0.1'
    port = 27017
    is_active = True
    databaseinfra = factory.SubFactory(DatabaseInfraFactory)
    hostname = factory.SubFactory(HostFactory)
    status = 1
    instance_type = 2
    total_size_in_bytes = 100
    used_size_in_bytes = 50


class NFSaaSHostAttr(factory.DjangoModelFactory):
    FACTORY_FOR = HostAttr

    host = factory.SubFactory(HostFactory)
    nfsaas_export_id = factory.Sequence(lambda n: n)
    nfsaas_path = factory.Sequence(lambda n: 'vol/testing-{0}'.format(n))
    nfsaas_path_host = factory.Sequence(lambda n: 'testing-{0}'.format(n))
    is_active = True
    nfsaas_size_kb = 1000
    nfsaas_used_size_kb = 10


class ParameterFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Parameter

    engine_type = factory.SubFactory(EngineTypeFactory)
    name = 'fake_parameter'


class DatabaseInfraParameterFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.DatabaseInfraParameter

    databaseinfra = factory.SubFactory(DatabaseInfraFactory)
    parameter = factory.SubFactory(ParameterFactory)
    value = ''
