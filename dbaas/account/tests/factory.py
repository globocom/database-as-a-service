# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import factory
from .. import models


class UserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.AccountUser

    username = factory.Sequence(lambda n: 'user_{0}'.format(n))
    email = factory.Sequence(lambda n: 'user_{0}@email.test.com'.format(n))


class RoleFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Role

    name = factory.Sequence(lambda n: 'role_{0}'.format(n))


class TeamFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Team

    name = factory.Sequence(lambda n: 'team_{0}'.format(n))
    email = factory.Sequence(lambda n: 'team_{0}@email.test.com'.format(n))

    role = factory.SubFactory(RoleFactory)
