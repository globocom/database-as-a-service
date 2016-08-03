# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import mock
from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from logical.tests import factory as factory_logical
from ..admin.databaseinfra import DatabaseInfraAdmin
from ..models import DatabaseInfra
from . import factory
from drivers.fake import FakeDriver
from django.core.cache import cache
import logging

LOG = logging.getLogger(__name__)
EDITING_READ_ONLY_FIELDS = ('disk_offering', )


class DatabaseInfraTestCase(TestCase):

    def setUp(self):
        # to avoid caching, clear it before tests
        cache.clear()
        self.admin = DatabaseInfraAdmin(DatabaseInfra, AdminSite())

    def test_best_for_without_plan_and_environment_options_returns_None(self):
        plan = factory.PlanFactory()
        environment = plan.environments.all()[0]
        self.assertIsNone(
            DatabaseInfra.best_for(plan=plan, environment=environment, name="test"))

    def test_best_for_with_only_one_datainfra_per_plan_and_environment(self):
        plan = factory.PlanFactory()
        environment = plan.environments.all()[0]
        datainfra = factory.DatabaseInfraFactory(
            plan=plan, environment=environment)
        instance = factory.InstanceFactory(
            address="127.0.0.1", port=27017, databaseinfra=datainfra)
        self.assertEqual(datainfra, DatabaseInfra.best_for(
            plan=plan, environment=environment, name="test"))

    def test_best_for_with_only_two_datainfra_per_plan_and_environment_returns_rounding_robin_them(self):
        plan = factory.PlanFactory()
        environment = plan.environments.all()[0]
        datainfra1 = factory.DatabaseInfraFactory(
            plan=plan, environment=environment, capacity=10)
        instance1 = factory.InstanceFactory(
            address="127.0.0.1", port=27017, databaseinfra=datainfra1)
        datainfra2 = factory.DatabaseInfraFactory(
            plan=plan, environment=environment, capacity=10)
        instance2 = factory.InstanceFactory(
            address="127.0.0.2", port=27017, databaseinfra=datainfra2)
        for i in range(10):
            should_choose = (datainfra1, datainfra2)[i % 2]
            choosed = DatabaseInfra.best_for(
                plan=plan, environment=environment, name="test")
            self.assertEqual(should_choose, choosed)
            database = factory_logical.DatabaseFactory(databaseinfra=choosed)
            self.assertEqual(choosed, database.databaseinfra)

    def test_check_instances_status_is_alive(self):
        plan = factory.PlanFactory()
        environment = plan.environments.all()[0]
        datainfra1 = factory.DatabaseInfraFactory(
            plan=plan, environment=environment, capacity=10)
        instance1 = factory.InstanceFactory(
            address="127.0.0.1", port=27017, databaseinfra=datainfra1, status=1)
        instance2 = factory.InstanceFactory(
            address="127.0.0.2", port=27017, databaseinfra=datainfra1, status=1)

        self.assertEquals(
            datainfra1.check_instances_status(), DatabaseInfra.ALIVE)

    def test_check_instances_status_is_dead(self):
        plan = factory.PlanFactory()
        environment = plan.environments.all()[0]
        datainfra1 = factory.DatabaseInfraFactory(
            plan=plan, environment=environment, capacity=10)
        instance1 = factory.InstanceFactory(
            address="127.0.0.1", port=27017, databaseinfra=datainfra1, status=0)
        instance2 = factory.InstanceFactory(
            address="127.0.0.2", port=27017, databaseinfra=datainfra1, status=0)

        self.assertEquals(
            datainfra1.check_instances_status(), DatabaseInfra.DEAD)

    def test_check_instances_status_is_alert(self):
        plan = factory.PlanFactory()
        environment = plan.environments.all()[0]
        datainfra1 = factory.DatabaseInfraFactory(
            plan=plan, environment=environment, capacity=10)
        instance1 = factory.InstanceFactory(
            address="127.0.0.1", port=27017, databaseinfra=datainfra1, status=1)
        instance2 = factory.InstanceFactory(
            address="127.0.0.2", port=27017, databaseinfra=datainfra1, status=0)

        self.assertEquals(
            datainfra1.check_instances_status(), DatabaseInfra.ALERT)

    def test_best_for_with_only_over_capacity_datainfra_returns_None(self):
        """tests database infra capacity"""
        NUMBER_OF_DATABASES_TO_TEST = 4
        plan = factory.PlanFactory()
        environment = plan.environments.all()[0]
        datainfra = factory.DatabaseInfraFactory(
            plan=plan, environment=environment, capacity=NUMBER_OF_DATABASES_TO_TEST)
        instance = factory.InstanceFactory(
            address="127.0.0.1", port=27017, databaseinfra=datainfra)
        for i in range(NUMBER_OF_DATABASES_TO_TEST):
            self.assertEqual(datainfra, DatabaseInfra.best_for(
                plan=plan, environment=environment, name="test"))
            factory_logical.DatabaseFactory(databaseinfra=datainfra)
        self.assertIsNone(
            DatabaseInfra.best_for(plan=plan, environment=environment, name="test"))

    @mock.patch.object(FakeDriver, 'info')
    def test_get_info_use_caching(self, info):
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

    def test_read_only_fields_editing(self):
        infra_factory = factory.DatabaseInfraFactory()
        infra_model = DatabaseInfra.objects.get(pk=infra_factory.pk)

        admin_read_only = self.admin.get_readonly_fields(
            request=None, obj=infra_model
        )
        self.assertEqual(EDITING_READ_ONLY_FIELDS, admin_read_only)

    def test_read_only_fields_adding(self):
        admin_read_only = self.admin.get_readonly_fields(
            request=None, obj=None
        )
        self.assertNotEqual(EDITING_READ_ONLY_FIELDS, admin_read_only)
        self.assertEqual(tuple(), admin_read_only)
