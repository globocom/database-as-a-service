# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import mock
from django.test import TestCase
from logical.tests import factory as factory_logical
from ..models import DatabaseInfra
from . import factory
from drivers.fake import FakeDriver
from django.core.cache import cache


class DatabaseInfraTestCase(TestCase):

    def setUp(self):
        pass
        # self.client = Client()
        # self.factory = RequestFactory()
        # self.databaseinfra = DatabaseInfraFactory()
        # self.hostname = HostFactory()
        # self.new_instance = InstanceFactory(address="new_instance.localinstance",
        #                             port=123,
        #                             is_active=True,
        #                             is_arbiter = False,
        #                             databaseinfra=self.databaseinfra)

    def test_best_for_without_plan_and_environment_options_returns_None(self):
        plan = factory.PlanFactory()
        environment = plan.environments.all()[0]
        self.assertIsNone(DatabaseInfra.best_for(plan=plan, environment=environment))

    def test_best_for_with_only_one_datainfra_per_plan_and_environment_returns_it(self):
        plan = factory.PlanFactory()
        environment = plan.environments.all()[0]
        datainfra = factory.DatabaseInfraFactory(plan=plan, environment=environment)
        self.assertEqual(datainfra, DatabaseInfra.best_for(plan=plan, environment=environment))

    def test_best_for_with_only_two_datainfra_per_plan_and_environment_returns_rounding_robin_them(self):
        plan = factory.PlanFactory()
        environment = plan.environments.all()[0]
        datainfra1 = factory.DatabaseInfraFactory(plan=plan, environment=environment, capacity=10)
        datainfra2 = factory.DatabaseInfraFactory(plan=plan, environment=environment, capacity=10)
        for i in range(10):
            should_choose = (datainfra1, datainfra2)[i%2]
            choosed = DatabaseInfra.best_for(plan=plan, environment=environment)
            self.assertEqual(should_choose, choosed)
            database = factory_logical.DatabaseFactory(databaseinfra=choosed)
            self.assertEqual(choosed, database.databaseinfra)


    def test_best_for_with_only_over_capacity_datainfra_returns_None(self):
        NUMBER_OF_DATABASES_TO_TEST = 4
        plan = factory.PlanFactory()
        environment = plan.environments.all()[0]
        datainfra = factory.DatabaseInfraFactory(plan=plan, environment=environment, capacity=NUMBER_OF_DATABASES_TO_TEST)
        for i in range(NUMBER_OF_DATABASES_TO_TEST):
            self.assertEqual(datainfra, DatabaseInfra.best_for(plan=plan, environment=environment))
            factory_logical.DatabaseFactory(databaseinfra=datainfra)
        self.assertIsNone(DatabaseInfra.best_for(plan=plan, environment=environment))

    @mock.patch.object(FakeDriver, 'info')
    def test_get_info_use_caching(self, info):
        cache.clear()
        info.return_value = 'hahaha'
        datainfra = factory.DatabaseInfraFactory()
        self.assertIsNotNone(datainfra.get_info())

        # get another instance to ensure is not a local cache
        datainfra = DatabaseInfra.objects.get(pk=datainfra.pk)
        self.assertIsNotNone(datainfra.get_info())
        info.assert_called_once_with()


    @mock.patch.object(FakeDriver, 'info')
    def test_get_info_accept_force_refresh(self, info):
        info.return_value = 'hahaha'
        datainfra = factory.DatabaseInfraFactory()
        self.assertIsNotNone(datainfra.get_info())

        # get another instance to ensure is not a local cache
        datainfra = DatabaseInfra.objects.get(pk=datainfra.pk)
        self.assertIsNotNone(datainfra.get_info(force_refresh=True))
        self.assertEqual(2, info.call_count)

