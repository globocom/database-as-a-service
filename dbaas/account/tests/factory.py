# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import factory
from .. import models


class UserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.AccountUser

    name = factory.Sequence(lambda n: 'user_{0}'.format(n))





