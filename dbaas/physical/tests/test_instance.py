# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test.client import Client
from django.test import TestCase
from django.test.client import RequestFactory
from django.db import IntegrityError

from ..models import Instance
from .factory import DatabaseInfraFactory


class InstanceTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.databaseinfra = DatabaseInfraFactory()
        self.new_instance = Instance.objects.create(address="new_instance.localinstance",
                                    port=123,
                                    is_active=True,
                                    databaseinfra=self.databaseinfra,
                                    type='1')

    def tearDown(self):
        self.new_instance.delete()

    def test_create_instance(self):
        
        instance = Instance.objects.create(address="test.localinstance",
                                    port=123,
                                    is_active=True,
                                    databaseinfra=self.databaseinfra,
                                    type='1')
        
        self.assertTrue(instance.id)


    def test_error_duplicate_instance(self):
        
        self.assertRaises(IntegrityError, Instance.objects.create, address="new_instance.localinstance",
                                                                port=123,
                                                                is_active=True, 
                                                                databaseinfra=self.databaseinfra,
                                                                type='1')
