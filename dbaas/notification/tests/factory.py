# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import factory
import dbaas_aclapi
import random
from .. import models
from logical.tests.factory import DatabaseFactory


class TaskHistoryFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.TaskHistory

    task_name = factory.Sequence(lambda n: 'task_name_{0}'.format(n))
    task_id = factory.Sequence(lambda n: 'task_id_{0}'.format(n))
    user = factory.Sequence(lambda n: 'user_{0}'.format(n))
    task_status = models.TaskHistory.STATUS_WAITING
    object_id = None
    object_class = None


class DatabaseBindFactory(factory.DjangoModelFactory):
    FACTORY_FOR = dbaas_aclapi.models.DatabaseBind

    database = factory.SubFactory(DatabaseFactory)
    bind_address = '{}.{}.{}.{}'.format(
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255)
    )
