# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import mock
import logging
from django.test import TestCase
from django.db import IntegrityError
from drivers import base
from maintenance.tests import factory as maintenance_factory
from physical.tests import factory as physical_factory
from physical.models import DatabaseInfra
from logical.tests import factory
from notification.tests.factory import TaskHistoryFactory
from notification.models import TaskHistory
from logical.models import Database, DatabaseHistory


LOG = logging.getLogger(__name__)
ERROR_CLONE_WITHOUT_PERSISTENCE = \
    "Database does not have persistence cannot be cloned"
ERROR_CLONE_IN_QUARANTINE = "Database in quarantine cannot be cloned"
ERROR_CLONE_NOT_ALIVE = "Database is not alive and cannot be cloned"
ERROR_DELETE_PROTECTED = "Database {} is protected and cannot be deleted"
ERROR_DELETE_DEAD = "Database {} is not alive and cannot be deleted"
ERROR_UPGRADE_MONGO24 = "MongoDB 2.4 cannot be upgraded by this task."
ERROR_UPGRADE_IN_QUARANTINE = "Database in quarantine and cannot be upgraded."
ERROR_UPGRADE_IS_DEAD = "Database is dead and cannot be upgraded."
ERROR_UPGRADE_NO_EQUIVALENT_PLAN = "Source plan do not has equivalent plan to upgrade."
UPGRADE_URL = "/admin/logical/database/{}/upgrade/"
UPGRADE_RETRY_URL = "/admin/logical/database/{}/upgrade_retry/"


class FakeDriver(base.BaseDriver):

    def get_connection(self):
        return 'connection-url'


class DatabaseTestCase(TestCase):

    def setUp(self):
        self.instance = physical_factory.InstanceFactory()
        self.databaseinfra = self.instance.databaseinfra
        self.engine = FakeDriver(databaseinfra=self.databaseinfra)
        self.environment = physical_factory.EnvironmentFactory()
        self.plan_upgrade = physical_factory.PlanFactory()

    def tearDown(self):
        self.engine = None

    def test_create_database(self):

        database = Database(name="blabla", databaseinfra=self.databaseinfra,
                            environment=self.environment)
        database.save()

        self.assertTrue(database.pk)

    def test_create_duplicate_database_error(self):

        database = Database(name="bleble", databaseinfra=self.databaseinfra,
                            environment=self.environment)

        database.save()

        self.assertTrue(database.pk)

        self.assertRaises(IntegrityError, Database(name="bleble",
                                                   databaseinfra=self.databaseinfra,
                                                   environment=self.environment).save)

    def test_slugify_database_name_with_spaces(self):

        database = factory.DatabaseFactory.build(name="w h a t",
                                                 databaseinfra=self.databaseinfra,
                                                 environment=self.environment)

        database.full_clean()
        database.save()
        self.assertTrue(database.id)
        self.assertEqual(database.name, 'w_h_a_t')

    def test_slugify_database_name_with_dots(self):
        database = factory.DatabaseFactory.build(name="w.h.e.r.e",
                                                 databaseinfra=self.databaseinfra,
                                                 environment=self.environment)

        database.full_clean()
        database.save()
        self.assertTrue(database.id)
        self.assertEqual(database.name, 'w_h_e_r_e')

    def test_cannot_edit_database_name(self):

        database = factory.DatabaseFactory(name="w h a t",
                                           databaseinfra=self.databaseinfra,
                                           environment=self.environment)

        self.assertTrue(database.id)

        database.name = "super3"

        self.assertRaises(AttributeError, database.save)

    @mock.patch.object(DatabaseInfra, 'get_info')
    def test_new_database_bypass_datainfra_info_cache(self, get_info):
        def side_effect_get_info(force_refresh=False):
            m = mock.Mock()
            if not force_refresh:
                m.get_database_status.return_value = None
                return m
            m.get_database_status.return_value = object()
            return m

        get_info.side_effect = side_effect_get_info
        database = factory.DatabaseFactory(name="db1cache",
                                           databaseinfra=self.databaseinfra,
                                           environment=self.environment)
        self.assertIsNotNone(database.database_status)
        self.assertEqual(
            [mock.call(), mock.call(force_refresh=True)], get_info.call_args_list)

    def test_can_update_volume_used_disk_size(self):
        database = factory.DatabaseFactory()
        database.databaseinfra = self.databaseinfra

        volume = physical_factory.VolumeFactory()
        volume.host = self.instance.hostname
        volume.save()

        old_used_size = volume.used_size_kb
        volume = database.update_host_disk_used_size(
            host_address=self.instance.address, used_size_kb=300
        )
        self.assertNotEqual(volume.used_size_kb, old_used_size)
        self.assertEqual(volume.used_size_kb, 300)

        old_used_size = volume.used_size_kb
        volume = database.update_host_disk_used_size(
            host_address=self.instance.address, used_size_kb=500
        )
        self.assertNotEqual(volume.used_size_kb, old_used_size)
        self.assertEqual(volume.used_size_kb, 500)

    def test_cannot_update_volume_used_disk_size_host_not_volume(self):
        database = factory.DatabaseFactory()
        database.databaseinfra = self.databaseinfra

        volume = database.update_host_disk_used_size(
            host_address=self.instance.address, used_size_kb=300
        )
        self.assertIsNone(volume)

    def test_can_clone(self):
        database = factory.DatabaseFactory()
        database.status = database.ALIVE

        can_be_cloned, error = database.can_be_cloned()
        self.assertTrue(can_be_cloned)
        self.assertIsNone(error)

    def test_cannot_clone_no_persistence(self):
        database = factory.DatabaseFactory()
        database.status = database.ALIVE
        database.plan.has_persistence = False

        can_be_cloned, error = database.can_be_cloned()
        self.assertFalse(can_be_cloned)
        self.assertEqual(error, ERROR_CLONE_WITHOUT_PERSISTENCE)

    def test_cannot_clone_in_quarantine(self):
        database = factory.DatabaseFactory()
        database.status = database.ALIVE
        database.is_in_quarantine = True

        can_be_cloned, error = database.can_be_cloned()
        self.assertFalse(can_be_cloned)
        self.assertEqual(error, ERROR_CLONE_IN_QUARANTINE)

    def test_cannot_clone_dead(self):
        database = factory.DatabaseFactory()
        database.status = database.DEAD
        database.database_status = None

        can_be_cloned, error = database.can_be_cloned()
        self.assertFalse(can_be_cloned)
        self.assertEqual(error, ERROR_CLONE_NOT_ALIVE)

    def test_can_delete(self):
        database = factory.DatabaseFactory()
        database.status = database.ALIVE

        can_be_deleted, error = database.can_be_deleted()
        self.assertTrue(can_be_deleted)
        self.assertIsNone(error)

    @mock.patch('logical.models.factory_for')
    @mock.patch('logical.models.Database.automatic_create_first_credential')
    def test_insert_on_database_history_when_delete(self, cred_mock, factory_mock):
        database = factory.DatabaseFactory(
            name='test_fake_name',
            description='__test__ fake desc'
        )
        database_id = database.id
        database.is_in_quarantine = True
        database.is_protected = False
        database.status = database.ALIVE
        database.environment.name = '__test__ fake env'
        database.project.name = '__test__ proj name'
        database.team.name = '__test__ team name'
        database.plan.name = '__test__ plan name'
        database.databaseinfra.name = '__test__ infra name'
        database.databaseinfra.engine.version = 'v1.2.3'
        database.databaseinfra.plan.has_persistence = False
        database.databaseinfra.engine.engine_type.name = '__test__ fake engine type'
        database.databaseinfra.disk_offering.size_kb = 1234

        database.delete()

        deleted_databases = DatabaseHistory.objects.filter(database_id=database_id)
        self.assertEqual(len(deleted_databases), 1)
        deleted_database = deleted_databases[0]
        self.assertEqual(deleted_database.database_id, database_id)
        self.assertEqual(deleted_database.name, 'test_fake_name')
        self.assertEqual(deleted_database.description, '__test__ fake desc')
        self.assertEqual(deleted_database.engine, '__test__ fake engine type v1.2.3')
        self.assertEqual(deleted_database.project, '__test__ proj name')
        self.assertEqual(deleted_database.team, '__test__ team name')
        self.assertEqual(deleted_database.databaseinfra_name, '__test__ infra name')
        self.assertEqual(deleted_database.plan, '__test__ plan name')
        self.assertEqual(deleted_database.disk_size_kb, 1234)
        self.assertFalse(deleted_database.has_persistence)
        self.assertEqual(deleted_database.environment, '__test__ fake env')

    def test_cannot_delete_protected(self):
        database = factory.DatabaseFactory()
        database.status = database.ALIVE
        database.is_protected = True

        can_be_deleted, error = database.can_be_deleted()
        self.assertFalse(can_be_deleted)
        self.assertEqual(error, ERROR_DELETE_PROTECTED.format(database.name))

    def test_can_delete_protected_in_quarantine(self):
        database = factory.DatabaseFactory()
        database.status = database.ALIVE
        database.is_protected = True
        database.is_in_quarantine = True

        can_be_deleted, error = database.can_be_deleted()
        self.assertTrue(can_be_deleted)
        self.assertIsNone(error)

    def test_can_delete_in_quarantine(self):
        database = factory.DatabaseFactory()
        database.status = database.ALIVE
        database.is_in_quarantine = True

        can_be_deleted, error = database.can_be_deleted()
        self.assertTrue(can_be_deleted)
        self.assertIsNone(error)

    def test_can_upgrade(self):
        database = factory.DatabaseFactory()
        database.status = database.ALIVE
        database.databaseinfra.plan.engine_equivalent_plan = self.plan_upgrade

        can_do_upgrade, error = database.can_do_upgrade()
        self.assertTrue(can_do_upgrade)
        self.assertIsNone(error)

    def test_cannot_upgrade_mongo24(self):
        mongo = physical_factory.EngineTypeFactory()
        mongo.name = 'mongodb'

        mongo24 = physical_factory.EngineFactory()
        mongo24.engine_type = mongo
        mongo24.version = '2.4.xxx'

        database = factory.DatabaseFactory()
        database.status = database.ALIVE

        infra = database.databaseinfra
        infra.engine = mongo24
        database.databaseinfra = infra

        can_do_upgrade, error = database.can_do_upgrade()
        self.assertFalse(can_do_upgrade)
        self.assertEqual(error, ERROR_UPGRADE_MONGO24)

    def test_cannot_upgrade_in_quarantine(self):
        database = factory.DatabaseFactory()
        database.status = database.ALIVE
        database.is_in_quarantine = True

        can_do_upgrade, error = database.can_do_upgrade()
        self.assertFalse(can_do_upgrade)
        self.assertEqual(error, ERROR_UPGRADE_IN_QUARANTINE)

    def test_cannot_upgrade_dead(self):
        database = factory.DatabaseFactory()
        database.databaseinfra.plan.engine_equivalent_plan = self.plan_upgrade
        database.status = database.DEAD

        can_do_upgrade, error = database.can_do_upgrade()
        self.assertFalse(can_do_upgrade)
        self.assertEqual(error, ERROR_UPGRADE_IS_DEAD)

    def test_cannot_upgrade_no_equivalent_plan(self):
        database = factory.DatabaseFactory()
        database.status = database.ALIVE

        can_do_upgrade, error = database.can_do_upgrade()
        self.assertFalse(can_do_upgrade)
        self.assertEqual(error, ERROR_UPGRADE_NO_EQUIVALENT_PLAN)

    def test_get_upgrade_url(self):
        database = factory.DatabaseFactory()
        expected_url = UPGRADE_URL.format(database.id)
        returned_url = database.get_upgrade_url()
        self.assertEqual(returned_url, expected_url)

    def test_get_upgrade_retry_url(self):
        database = factory.DatabaseFactory()
        expected_url = UPGRADE_RETRY_URL.format(database.id)
        returned_url = database.get_upgrade_retry_url()
        self.assertEqual(returned_url, expected_url)

    def test_last_successful_upgrade(self):
        database = factory.DatabaseFactory()
        self.assertIsNone(database.last_successful_upgrade)

        upgrade = maintenance_factory.DatabaseUpgradeFactory()
        upgrade.database = database

        upgrade.save()
        self.assertIsNone(database.last_successful_upgrade)

        upgrade.set_success()
        self.assertEqual(database.last_successful_upgrade, upgrade)

    def test_last_successful_upgrade_with_error(self):
        database = factory.DatabaseFactory()
        upgrade = maintenance_factory.DatabaseUpgradeFactory()
        upgrade.database = database
        upgrade.set_error()
        self.assertIsNone(database.last_successful_upgrade)

    def test_current_task_lock(self):
        database = factory.DatabaseFactory()
        task1 = TaskHistoryFactory()
        task2 = TaskHistoryFactory()
        database.pin_task(task1)
        self.assertFalse(database.pin_task(task2))
        database.unpin_task()
        self.assertTrue(database.pin_task(task2))

    def test_lock_retry(self):
        database = factory.DatabaseFactory()
        task1 = TaskHistoryFactory()
        task2 = TaskHistoryFactory()
        task3 = TaskHistoryFactory()

        task1.task_status = TaskHistory.STATUS_ERROR
        task1.save()

        task2.task_name = task1.task_name
        task2.save()

        database.pin_task(task1)

        self.assertFalse(database.update_task(task3))
        self.assertTrue(database.update_task(task2))
        self.assertFalse(database.update_task(task2))

        database.unpin_task()
        self.assertTrue(database.pin_task(task3))
