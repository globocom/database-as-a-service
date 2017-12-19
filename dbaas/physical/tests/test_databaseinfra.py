# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import logging
import mock
from django.test import TestCase
from django.core.cache import cache
from django.contrib.admin.sites import AdminSite

from logical.tests import factory as factory_logical
from physical.admin.databaseinfra import DatabaseInfraAdmin
from physical.models import (DatabaseInfra, Plan, Instance, Host, Parameter,
                             DatabaseInfraParameter)
from dbaas_nfsaas.models import HostAttr
from dbaas_cloudstack.models import DatabaseInfraOffering, CloudStackOffering
from physical.tests import factory
from drivers.fake import FakeDriver


LOG = logging.getLogger(__name__)
EDITING_CLOUDSTACK_READ_ONLY_FIELDS = ('disk_offering', )
EDITING_PRE_PROVISIONED_READ_ONLY_FIELDS = tuple()


class PropertiesTestCase(TestCase):

    KB2GB_FACTOR = (1.0 * 1024 * 1024)

    @classmethod
    def setUpClass(cls):
        cls.databaseinfra = factory.DatabaseInfraFactory(
            name="__test__ mysqlinfra",
            user="root", password='Fake')
        cls.hostname = factory.HostFactory()
        cls.instance = factory.InstanceFactory(
            address="new_instance.localinstance",
            port=123, is_active=True,
            databaseinfra=cls.databaseinfra,
            hostname=cls.hostname
        )
        cls.nfaas_host_attr = factory.NFSaaSHostAttr(
            host=cls.hostname
        )

        cs_offering = factory.CloudStackOfferingFactory(memory_size_mb=9)
        cls.infra_offering = factory.DatabaseInfraOfferingFactory(
            databaseinfra=cls.databaseinfra,
            offering=cs_offering
        )

    @classmethod
    def tearDownClass(cls):
        HostAttr.objects.all().delete()
        Instance.objects.all().delete()
        Host.objects.all().delete()
        DatabaseInfra.objects.all().delete()
        Plan.objects.all().delete()
        CloudStackOffering.objects.all().delete()
        DatabaseInfraOffering.objects.all().delete()
        Parameter.objects.all().delete()
        DatabaseInfraParameter.objects.all().delete()

    def test_disk_used_size_in_gb_convert(self):
        '''
            Test property: disk_used_size_in_gb
            case: If this property convert to gb from kb
        '''

        self.nfaas_host_attr.nfsaas_used_size_kb = 2.5 * self.KB2GB_FACTOR  # 5GB
        self.nfaas_host_attr.save()

        self.assertEqual(self.databaseinfra.disk_used_size_in_gb, 2.5)

    def test_disk_used_size_in_gb_when_nfsaas_is_null(self):
        '''
            Test property: disk_used_size_in_gb
            case: When nfsaas_used_size_kb is NULL the property must return None
        '''

        self.nfaas_host_attr.nfsaas_used_size_kb = None
        self.nfaas_host_attr.save()

        self.assertEqual(self.databaseinfra.disk_used_size_in_gb, None)

    def test_disk_used_size_in_gb_when_nfsaas_is_0(self):
        '''
            Test property: disk_used_size_in_gb
            case: When nfsaas_used_size_kb is 0 the property must return 0
        '''

        self.nfaas_host_attr.nfsaas_used_size_kb = 0
        self.nfaas_host_attr.save()

        self.assertEqual(self.databaseinfra.disk_used_size_in_gb, 0)

    def test_size_for_redis_engine(self):
        '''
            Test property: per_database_size_bytes
            case: When engine type is redis the value must be from parameter table
        '''

        self.databaseinfra.engine.engine_type.name = 'redis'
        self.databaseinfra.engine.engine_type.save()
        factory.DatabaseInfraParameterFactory(
            value='110000', parameter__name='maxmemory',
            databaseinfra=self.databaseinfra
        )

        self.assertEqual(self.databaseinfra.per_database_size_bytes, 110000)

    def test_size_for_redis_engine_configuration(self):
        '''
            Test property: per_database_size_bytes
            case: When engine type is redis the value must be from configuration
                  when not found on parameter table
        '''

        self.databaseinfra.engine.engine_type.name = 'redis'
        self.databaseinfra.engine.engine_type.save()
        self.assertEqual(self.databaseinfra.per_database_size_bytes, 4718592)

    def test_size_for_not_redis_engine(self):
        '''
            Test property: per_database_size_bytes
            case: When engine type NOT is redis the value must be from disk_offering
        '''

        self.databaseinfra.engine.engine_type.name = 'mysql'
        self.databaseinfra.engine.engine_type.save()
        self.databaseinfra.disk_offering.size_kb = 10
        self.assertEqual(self.databaseinfra.per_database_size_bytes, 10240)


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
        factory.InstanceFactory(
            address="127.0.0.1", port=27017, databaseinfra=datainfra)
        self.assertEqual(datainfra, DatabaseInfra.best_for(
            plan=plan, environment=environment, name="test"))

    def test_best_for_with_only_two_datainfra_per_plan_and_environment_returns_rounding_robin_them(self):
        plan = factory.PlanFactory()
        environment = plan.environments.all()[0]
        datainfra1 = factory.DatabaseInfraFactory(
            plan=plan, environment=environment, capacity=10)
        factory.InstanceFactory(
            address="127.0.0.1", port=27017, databaseinfra=datainfra1)
        datainfra2 = factory.DatabaseInfraFactory(
            plan=plan, environment=environment, capacity=10)
        factory.InstanceFactory(
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
        factory.InstanceFactory(
            address="127.0.0.1", port=27017, databaseinfra=datainfra1, status=1)
        factory.InstanceFactory(
            address="127.0.0.2", port=27017, databaseinfra=datainfra1, status=1)

        self.assertEquals(
            datainfra1.check_instances_status(), DatabaseInfra.ALIVE)

    def test_check_instances_status_is_dead(self):
        plan = factory.PlanFactory()
        environment = plan.environments.all()[0]
        datainfra1 = factory.DatabaseInfraFactory(
            plan=plan, environment=environment, capacity=10)
        factory.InstanceFactory(
            address="127.0.0.1", port=27017, databaseinfra=datainfra1, status=0)
        factory.InstanceFactory(
            address="127.0.0.2", port=27017, databaseinfra=datainfra1, status=0)

        self.assertEquals(
            datainfra1.check_instances_status(), DatabaseInfra.DEAD)

    def test_check_instances_status_is_alert(self):
        plan = factory.PlanFactory()
        environment = plan.environments.all()[0]
        datainfra1 = factory.DatabaseInfraFactory(
            plan=plan, environment=environment, capacity=10)
        factory.InstanceFactory(
            address="127.0.0.1", port=27017, databaseinfra=datainfra1, status=1)
        factory.InstanceFactory(
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
        factory.InstanceFactory(
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
        self.assertEqual(
            EDITING_PRE_PROVISIONED_READ_ONLY_FIELDS, admin_read_only
        )

        infra_model.plan.provider = Plan.CLOUDSTACK
        admin_read_only = self.admin.get_readonly_fields(
            request=None, obj=infra_model
        )
        self.assertEqual(EDITING_CLOUDSTACK_READ_ONLY_FIELDS, admin_read_only)

    def test_read_only_fields_adding(self):
        admin_read_only = self.admin.get_readonly_fields(
            request=None, obj=None
        )
        self.assertNotEqual(
            EDITING_CLOUDSTACK_READ_ONLY_FIELDS, admin_read_only
        )
        self.assertEqual(tuple(), admin_read_only)

    def test_hosts(self):
        plan = factory.PlanFactory()
        environment = plan.environments.all()[0]
        datainfra = factory.DatabaseInfraFactory(
            plan=plan, environment=environment, capacity=1
        )
        instance = factory.InstanceFactory(
            address="127.0.0.1", port=27017, databaseinfra=datainfra
        )
        host_1 = instance.hostname
        instance = factory.InstanceFactory(
            address="127.0.0.2", port=27017, databaseinfra=datainfra
        )
        host_2 = instance.hostname
        factory.InstanceFactory(
            address="127.0.0.3", port=27017, databaseinfra=datainfra,
            hostname=host_2
        )

        self.assertIn(host_1, datainfra.hosts)
        self.assertIn(host_2, datainfra.hosts)
        self.assertEqual(len(datainfra.hosts), 2)
