# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import unittest
from django.test import TestCase
from base.engine import base
from base.tests import factory

CONNECTION_TEST = 'connection-url'

class FakeEngine(base.BaseEngine):
    
    def get_connection(self):
        return CONNECTION_TEST


class EngineTestCase(TestCase):
    """
    Tests Engine and EngineType
    """

    def setUp(self):
        self.instance = factory.InstanceFactory()
        self.engine = FakeEngine(instance=self.instance)

    def tearDown(self):
        self.instance.delete()
        self.instance = self.engine = None

    def test_to_envs_with_none_returns_empty_dict(self):
        self.assertEquals({}, self.engine.to_envs(None))

    def test_to_envs_with_instance_object_must_return_a_dictionary(self):
        self.assertEquals({
            'INSTANCE_ID': str(self.instance.id),
            'INSTANCE_NAME': self.instance.name,
            'INSTANCE_PASSWORD': self.instance.password,
            'INSTANCE_USER': self.instance.user,
            'INSTANCE_CONNECTION': CONNECTION_TEST,
            }, self.engine.to_envs(self.instance))

    @unittest.skip("I didn't implement this method because he is not completed.")
    def test_call_script(self):
        self.fail()
