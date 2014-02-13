# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import factory
from .. import models


class NotificationHistoryFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.TaskHistory

    task_name = factory.Sequence(lambda n: 'task_name_{0}'.format(n))
    task_id = factory.Sequence(lambda n: 'task_id_{0}'.format(n))
    user = factory.Sequence(lambda n: 'user_{0}'.format(n))
    task_status = "PENDING"


