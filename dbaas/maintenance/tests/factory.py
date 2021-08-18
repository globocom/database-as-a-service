from __future__ import absolute_import, unicode_literals
import factory
from logical.tests.factory import DatabaseFactory
from physical.tests.factory import (PlanFactory, EnvironmentFactory,
                                    EngineTypeFactory, OfferingFactory,
                                    EnvironmentFactory)
from notification.tests.factory import TaskHistoryFactory
from .. import models


class DatabaseUpgradeFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.DatabaseUpgrade

    database = factory.SubFactory(DatabaseFactory)
    source_plan = factory.SubFactory(PlanFactory)
    target_plan = factory.SubFactory(PlanFactory)
    task = factory.SubFactory(TaskHistoryFactory)


class DatabaseResizeFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.DatabaseResize

    database = factory.SubFactory(DatabaseFactory)
    source_offer = factory.SubFactory(OfferingFactory)
    target_offer = factory.SubFactory(OfferingFactory)
    task = factory.SubFactory(TaskHistoryFactory)


class DatabaseChangeParameterFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.DatabaseChangeParameter

    database = factory.SubFactory(DatabaseFactory)
    task = factory.SubFactory(TaskHistoryFactory)


class DatabaseMigrageFactoryStageZero(factory.DjangoModelFactory):
    FACTORY_FOR = models.DatabaseMigrate

    database = factory.SubFactory(DatabaseFactory)
    environment = factory.SubFactory(EnvironmentFactory)
    origin_environment = factory.SubFactory(EnvironmentFactory)
    offering = factory.SubFactory(OfferingFactory)
    origin_offering = factory.SubFactory(OfferingFactory)
    task = factory.SubFactory(TaskHistoryFactory)
    migration_stage = 0
