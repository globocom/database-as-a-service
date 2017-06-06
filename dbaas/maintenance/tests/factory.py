from __future__ import absolute_import, unicode_literals
import factory
import dbaas_cloudstack
from logical.tests.factory import DatabaseFactory
from physical.tests.factory import PlanFactory, EnvironmentFactory, EngineTypeFactory
from notification.tests.factory import TaskHistoryFactory
from .. import models


class CloudStackRegionFactory(factory.DjangoModelFactory):
    FACTORY_FOR = dbaas_cloudstack.models.CloudStackRegion

    name = factory.Sequence(lambda n: 'region_{0}'.format(n))
    environment = factory.SubFactory(EnvironmentFactory)


class CloudStackOfferingFactory(factory.DjangoModelFactory):
    FACTORY_FOR = dbaas_cloudstack.models.CloudStackOffering

    serviceofferingid = factory.Sequence(lambda n: '{0}'.format(n))
    name = factory.Sequence(lambda n: 'offering_{0}'.format(n))
    weaker = False
    region = factory.SubFactory(CloudStackRegionFactory)
    equivalent_offering = None
    cpus = 1L
    memory_size_mb = 1024L

class CloudStackPackFactory(factory.DjangoModelFactory):
    FACTORY_FOR = dbaas_cloudstack.models.CloudStackPack

    offering = factory.SubFactory(CloudStackOfferingFactory)
    engine_type = factory.SubFactory(EngineTypeFactory)
    name = factory.Sequence(lambda n: 'pack_{0}'.format(n))


class DatabaseUpgradeFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.DatabaseUpgrade

    database = factory.SubFactory(DatabaseFactory)
    source_plan = factory.SubFactory(PlanFactory)
    target_plan = factory.SubFactory(PlanFactory)
    task = factory.SubFactory(TaskHistoryFactory)


class DatabaseResizeFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.DatabaseResize

    database = factory.SubFactory(DatabaseFactory)
    source_offer = factory.SubFactory(CloudStackPackFactory)
    target_offer = factory.SubFactory(CloudStackPackFactory)
    task = factory.SubFactory(TaskHistoryFactory)


class DatabaseChangeParameterFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.DatabaseChangeParameter

    database = factory.SubFactory(DatabaseFactory)
    task = factory.SubFactory(TaskHistoryFactory)
