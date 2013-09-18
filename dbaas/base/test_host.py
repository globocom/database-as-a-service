# -*- coding:utf-8 -*-
from django.utils import unittest
from django.test.client import Client
from django.test import TestCase
from django.utils import simplejson
from django.test.client import RequestFactory
from django.db import IntegrityError

from .models import Node


class NodeTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.new_node = Node.objects.create(fqdn="new_node.localnode", 
                                    environment_id=1,
                                    is_active=True,
                                    type='1')

    def tearDown(self):
        self.new_node.delete()

    def test_create_node(self):
        
        node = Node.objects.create(fqdn="test.localnode", 
                                    environment_id=1,
                                    is_active=True,
                                    type='1')
        
        self.assertTrue(node.id)


    def test_error_duplicate_node(self):
        
        self.assertRaises(IntegrityError, Node.objects.create, fqdn="new_node.localnode", 
                                                                environment_id=1, 
                                                                is_active=True, 
                                                                type='1')
