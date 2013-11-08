# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import boto.ec2.connection
import boto.ec2.regioninfo
# import mock
from django.test import TestCase
from django.test.utils import override_settings
# from drivers import DriverFactory
from physical.tests import factory as factory_physical
# from logical.tests import factory as factory_logical
# from ..mongodb import MongoDB
from .. import ec2
from moto import mock_ec2
# from moto.ec2 import ec2_backend

class Ec2ProviderTestCase(TestCase):
    """
    Tests MongoDB Engine
    """

    def setUp(self):
        self.databaseinfra = factory_physical.DatabaseInfraFactory()
        # self.instance = factory_physical.InstanceFactory(databaseinfra=self.databaseinfra)
        self.provider = ec2.Ec2Provider()


    def tearDown(self):
        self.databaseinfra.delete()
        self.driver = self.databaseinfra = None

    @mock_ec2
    @override_settings(EC2_REGION="us-west-2")
    def test_get_ec2_api_must_return_a_EC2Connection(self):
        self.assertTrue(isinstance(ec2.get_ec2_api(), boto.ec2.connection.EC2Connection))

    @mock_ec2
    @override_settings(EC2_ACCESS_KEY='test-key')
    @override_settings(EC2_SECRET_KEY='test-secret-key')
    @override_settings(EC2_URL='https://myprovider.com/with/any/path')
    def test_get_ec2_api_must_support_a_connection_with_specific_providers(self):
        conn = ec2.get_ec2_api()
        self.assertEqual(443, conn.port)
        self.assertEqual('test-key', conn.access_key)
        self.assertEqual('test-secret-key', conn.secret_key)
        self.assertEqual('myprovider.com', conn.host)
        self.assertEqual('/with/any/path', conn.path)

    @mock_ec2
    @override_settings(EC2_ACCESS_KEY='test-key')
    @override_settings(EC2_SECRET_KEY='test-secret-key')
    @override_settings(EC2_URL=None)
    @override_settings(EC2_REGION="us-west-2")
    def test_get_ec2_api_must_support_a_connection_with_aws_region(self):
        conn = ec2.get_ec2_api()
        self.assertEqual(443, conn.port)
        self.assertEqual('test-key', conn.access_key)
        self.assertEqual('test-secret-key', conn.secret_key)
        self.assertEqual('ec2.us-west-2.amazonaws.com', conn.host)
        self.assertEqual('/', conn.path)

    @mock_ec2
    @override_settings(EC2_URL=None)
    @override_settings(EC2_REGION="us-west-2")
    def test_create_instance(self):
        instance = self.provider.create_instance(self.databaseinfra)
        self.assertIsNotNone(instance)
        self.assertEqual(self.databaseinfra, instance.databaseinfra)
        self.assertEqual(False, instance.is_active)
        self.assertIsNotNone(instance.address)
        self.assertEqual(12345, instance.port)

