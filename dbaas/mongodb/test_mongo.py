# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils import unittest
from django.test.client import Client
from django.test import TestCase
from django.utils import simplejson
from django.test.client import RequestFactory
from django.db import IntegrityError

from base.models import Engine, EngineType, Node, Environment, Instance
from base.engine.factory import EngineFactory

from business.models import Product, Plan


class EngineTestCase(TestCase):
    """
    Tests Engine and EngineType
    """

    fixtures = ['config_business.yaml']
    
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.new_engine_type = EngineType.objects.create(name="Test")
        self.environment = Environment.objects.get(id=1)
        self.node = Node.objects.create(address="localhost", 
                                    port=27017, 
                                    environment=self.environment,
                                    type="1")
        self.product = Product.objects.create(name="supimpa")
        
        self.instance = Instance.objects.create(name="matrix",
                                                user="neo",
                                                password="trinity",
                                                node=self.node,
                                                engine=Engine.objects.get(id=1),
                                                product=self.product,
                                                plan=Plan.objects.get(name="small"))

    def tearDown(self):
        self.new_engine_type.delete()
        self.node.delete()
        self.product.delete()
        self.instance.delete()

    def test_create_engine_type(self):

        engine_type = EngineType.objects.create(name="John...1..2..3..")

        self.assertTrue(engine_type.id)

    def test_error_duplicate_engine_type(self):

        self.assertRaises(IntegrityError, EngineType.objects.create, name="Test")

    def test_create_engine_in_bd(self):

        engine_type = EngineType.objects.create(name="Maria")

        self.assertTrue(engine_type.id)

        engine = Engine.objects.create(version="1.2.3", engine_type=engine_type)

        self.assertTrue(engine.id)

    def test_mongodb_app_installed(self):

        self.assertTrue(EngineFactory.is_engine_available("mongodb")) 

    
    #test mongo methods
    def test_instantiate_mongodb(self):

        self.assertTrue(self.node.id)

        mongo_db = EngineFactory.factory(self.instance)

        self.assertIsNotNone(mongo_db)

        self.assertEqual(mongo_db.node.address, 'localhost')

    def test_mongodb_url(self):

        mongo_db = EngineFactory.factory(self.instance)

        self.assertEqual(mongo_db.url(), "mongodb://%s:%s" % (self.instance.name, mongo_db.port))

    def test_mongodb_port(self):

        mongo_db = EngineFactory.factory(self.instance)

        self.assertEqual(mongo_db.port(), 27017)

    def test_mongodb_address(self):

        mongo_db = EngineFactory.factory(self.instance)

        self.assertEqual(mongo_db.address(), "localhost")

    def test_mongodb_user(self):

        mongo_db = EngineFactory.factory(self.instance)

        self.assertEqual(mongo_db.user(), 'neo')

    def test_mongodb_password(self):

        mongo_db = EngineFactory.factory(self.instance)

        self.assertEqual(mongo_db.password(), "trinity")

    def test_mongodb_status(self):

        mongo_db = EngineFactory.factory(self.instance)

        self.assertRaises(NotImplementedError, mongo_db.status)

    def test_mongodb_create_user(self):

        mongo_db = EngineFactory.factory(self.instance)

        self.assertRaises(NotImplementedError, mongo_db.create_user, credential=None, )


    def test_mongodb_remove_user(self):

        mongo_db = EngineFactory.factory(self.instance)

        self.assertRaises(NotImplementedError, mongo_db.remove_user, credential=None)

    def test_mongodb_create_database(self):

        mongo_db = EngineFactory.factory(self.instance)

        self.assertRaises(NotImplementedError, mongo_db.create_database, database=None)


    def test_mongodb_remove_database(self):

        mongo_db = EngineFactory.factory(self.instance)

        self.assertRaises(NotImplementedError, mongo_db.remove_database, database=None)


    def test_mongodb_list_databases(self):

        mongo_db = EngineFactory.factory(self.instance)

        self.assertRaises(NotImplementedError, mongo_db.list_databases)
