# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import factory
from .. import models
from physical.tests.factory import EnvironmentFactory


class IntegrationTypeCloudStackFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.IntegrationType

    name = factory.Sequence(lambda n: 'name_{0}'.format(n))
    type = 1

class IntegrationTypeNFSaaSFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.IntegrationType

    name = factory.Sequence(lambda n: 'name_{0}'.format(n))
    type = 2


class IntegrationCredentialNFSaaSFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.IntegrationCredential

    user = factory.Sequence(lambda n: 'name_{0}'.format(n))
    password = factory.Sequence(lambda n: 'pass_{0}'.format(n))
    integration_type = factory.SubFactory(IntegrationTypeNFSaaSFactory)
    token = factory.Sequence(lambda n: 'token_{0}'.format(n))
    secret = factory.Sequence(lambda n: 'secret_{0}'.format(n))
    endpoint =factory.Sequence(lambda n: 'www.endpoint.glb_{0}'.format(n))
    
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

class IntegrationTypeCloudStackFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.IntegrationCredential

    user = factory.Sequence(lambda n: 'name_{0}'.format(n))
    password = factory.Sequence(lambda n: 'pass_{0}'.format(n))
    integration_type = factory.SubFactory(IntegrationTypeCloudStackFactory)
    token = factory.Sequence(lambda n: 'token_{0}'.format(n))
    secret = factory.Sequence(lambda n: 'secret_{0}'.format(n))
    endpoint =factory.Sequence(lambda n: 'endpoint_{0}'.format(n))
    
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