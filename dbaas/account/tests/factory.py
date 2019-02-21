# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib.auth.models import User
import factory
from .. import models


class AccountUserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.AccountUser

    username = factory.Sequence(lambda n: 'user_{0}'.format(n))
    email = factory.Sequence(lambda n: 'user_{0}@email.test.com'.format(n))

class UserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = User

    username = factory.Sequence(lambda n: 'user_{0}'.format(n))
    email = factory.Sequence(lambda n: 'user_{0}@email.test.com'.format(n))


class RoleFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Role

    name = factory.Sequence(lambda n: 'role_{0}'.format(n))


class OraganizationFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Organization

    name = factory.Sequence(lambda n: 'organization_{0}'.format(n))


class TeamFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Team

    name = factory.Sequence(lambda n: 'team_{0}'.format(n))
    email = factory.Sequence(lambda n: 'team_{0}@email.test.com'.format(n))
    contacts = factory.Sequence(lambda n: '{0} - contact'.format(n))

    role = factory.SubFactory(RoleFactory)
    organization = factory.SubFactory(OraganizationFactory)
