# -*- coding:utf-8 -*-
from django.utils import unittest
from django.test.client import Client
from django.test import TestCase
from django.utils import simplejson
from django.test.client import RequestFactory

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

    # def test_new_owner_has_environments(self):
    #     owner_environments = OwnerEnvironment.objects.filter(owner=self.new_owner)
    #     self.assertTrue(owner_environments)
    # 
    # def test_delete_empty_owner(self):
    #     owner = Owner.objects.create(name="gustavo 12345")
    #     owner_id = owner.id
    #     owner_environments = OwnerEnvironment.objects.filter(owner=owner)
    # 
    #     self.assertTrue(owner_environments)
    # 
    #     owner.delete()
    # 
    #     # testa se o objeto foi realmente removido
    #     self.assertRaises(Owner.DoesNotExist, Owner.objects.get, id=owner_id)
    # 
    #     owner_environments = OwnerEnvironment.objects.filter(owner__id=owner_id)
    # 
    #     # testo se os owner environments foram apagados
    #     self.assertTrue(len(owner_environments) == 0)
