# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test.client import Client
from django.test import TestCase
from django.test.client import RequestFactory
from django.db import IntegrityError

from ..models import Instance
from .factory import DatabaseInfraFactory, HostFactory, InstanceFactory


class InstanceTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.databaseinfra = DatabaseInfraFactory()
        self.hostname = HostFactory()
        self.new_instance = InstanceFactory(address="new_instance.localinstance",
                                    port=123,
                                    is_active=True,
                                    is_arbiter = False,
                                    databaseinfra=self.databaseinfra,
                                    type='1')

    def test_create_instance(self):
        
        instance = Instance.objects.create(address="test.localinstance",
                                    port=123,
                                    is_active=True,
                                    is_arbiter=False,
                                    hostname=self.hostname,
                                    databaseinfra=self.databaseinfra,
                                    type='1')
        
        self.assertTrue(instance.id)


    def test_error_duplicate_instance(self):
        
        another_instance = self.new_instance
        another_instance.id = None
        
        self.assertRaises(IntegrityError, another_instance.save)
