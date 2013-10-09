# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test.client import Client
from django.test import TestCase
from django.test.client import RequestFactory
from django.db import IntegrityError

from ..models import Node
from .factory import InstanceFactory


class NodeTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.instance = InstanceFactory()
        self.new_node = Node.objects.create(address="new_node.localnode",
                                    port=123,
                                    is_active=True,
                                    instance=self.instance,
                                    type='1')

    def tearDown(self):
        self.new_node.delete()

    def test_create_node(self):
        
        node = Node.objects.create(address="test.localnode",
                                    port=123,
                                    is_active=True,
                                    instance=self.instance,
                                    type='1')
        
        self.assertTrue(node.id)


    def test_error_duplicate_node(self):
        
        self.assertRaises(IntegrityError, Node.objects.create, address="new_node.localnode",
                                                                port=123,
                                                                is_active=True, 
                                                                instance=self.instance,
                                                                type='1')
