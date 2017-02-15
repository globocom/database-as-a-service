# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase
from django.db import IntegrityError

from .factory import EnvironmentFactory, PlanFactory


class EnvironmentTestCase(TestCase):

    def setUp(self):
        self.env = EnvironmentFactory(name='production')

    def test_create_host(self):

        env = EnvironmentFactory()
        self.assertTrue(env.id)

    def test_unique_host(self):

        another_instance = self.env
        another_instance.id = None

        self.assertRaises(IntegrityError, another_instance.save)

    def test_get_active_plans_with(self):
        plan1 = PlanFactory()
        plan2 = PlanFactory(is_active=False)
        plan3 = PlanFactory()

        plan1.environments.add(self.env)
        plan2.environments.add(self.env)
        plan3.environments.add(self.env)

        expected_result = set([plan1, plan3])
        result = set(self.env.active_plans())
        self.assertEqual(expected_result, result)
