# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
from django.test import TestCase
from . import factory
from physical.models import Environment

LOG = logging.getLogger(__name__)


class IntegrationCredentialTestCase(TestCase):

    def setUp(self):
        self.integration_nfsaas = factory.IntegrationCredentialNFSaaSFactory()
        self.integration_cloudstack  = factory.IntegrationTypeCloudStackFactory()

    def tearDown(self):
        self.integration_nfsaas.delete()
        self.integration_cloudstack.delete()


    def test_integration_environment(self):
        self.assertIsInstance(self.integration_cloudstack.environments.all()[0], Environment)
        self.assertIsInstance(self.integration_nfsaas.environments.all()[0], Environment)

    def test_cloudstack_credential(self):
        self.assertEqual(self.integration_cloudstack.integration_type.type, 1)
        self.assertTrue(self.integration_cloudstack)

    def test_nfsaas_credential(self):
        self.assertEqual(self.integration_nfsaas.integration_type.type, 2)
        self.assertTrue(self.integration_nfsaas)
