# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase
from django.db import IntegrityError

from .factory import EnvironmentFactory, PlanFactory, EnvironmentProdFactory


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

    def test_migrate_to(self):
        env = EnvironmentFactory()
        env_dest_1 = EnvironmentFactory()
        env_dest_2 = EnvironmentFactory()

        env_dest_1.migrate_environment = env
        env_dest_1.save()

        env_dest_2.migrate_environment = env
        env_dest_2.save()

        migrate_to = env.migrate_to.all()
        self.assertEqual(len(migrate_to), 2)
        self.assertIn(env_dest_1, migrate_to)
        self.assertIn(env_dest_2, migrate_to)

    def test_get_stage_by_id_dev(self):
        env = EnvironmentFactory()
        stage_test = env.get_stage_by_id(1)

        self.assertEqual(stage_test, "Dev")

    def test_get_stage_by_id_prod(self):
        env = EnvironmentFactory()
        stage_test = env.get_stage_by_id(2)

        self.assertEqual(stage_test, "Prod")

    def test_get_stage_by_id_invalid(self):
        env = EnvironmentFactory()
        stage_test = env.get_stage_by_id(0)

        self.assertEqual(stage_test, None)

    def test_get_dev_envs(self):
        env = EnvironmentFactory()
        env_get = env.dev_envs()

        self.assertIn(env.name, env_get)

    def test_get_prod_envs(self):
        env = EnvironmentProdFactory()
        env_get = env.prod_envs()

        self.assertIn(env.name, env_get)
