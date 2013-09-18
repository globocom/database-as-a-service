# -*- coding:utf-8 -*-
from django.utils import unittest
from django.test.client import Client
from django.test import TestCase
from django.utils import simplejson
from django.test.client import RequestFactory
from django.db import IntegrityError

from .models import Host


class HostTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.new_host = Host.objects.create(fqdn="new_host.localhost", 
                                    environment_id=1,
                                    is_active=True,
                                    type='1')

    def tearDown(self):
        self.new_host.delete()

    def test_create_host(self):
        
        host = Host.objects.create(fqdn="test.localhost", 
                                    environment_id=1,
                                    is_active=True,
                                    type='1')
        
        self.assertTrue(host.id)


    def test_error_duplicate_host(self):
        
        self.assertRaises(IntegrityError, Host.objects.create, fqdn="new_host.localhost", 
                                                                environment_id=1, 
                                                                is_active=True, 
                                                                type='1')
