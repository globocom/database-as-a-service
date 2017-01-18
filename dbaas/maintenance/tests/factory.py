from __future__ import absolute_import, unicode_literals
import factory
from logical.tests.factory import DatabaseFactory
from physical.tests.factory import PlanFactory
from notification.tests.factory import TaskHistoryFactory
from .. import models


class DatabaseUpgradeFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.DatabaseUpgrade

    database = factory.SubFactory(DatabaseFactory)
    source_plan = factory.SubFactory(PlanFactory)
    target_plan = factory.SubFactory(PlanFactory)
    task = factory.SubFactory(TaskHistoryFactory)

