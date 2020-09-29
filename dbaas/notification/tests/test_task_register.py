# coding:utf-8
from mock import MagicMock, patch
from unittest import TestCase
from logical.tests import factory as logical_factory
from physical.tests import factory as physical_factory
from notification.models import TaskHistory
from notification.tasks import TaskRegister


class CreateTaskTestCase(TestCase):

    def setUp(self):
        self.task_params = {
            'task_name': 'fake_task_name',
            'arguments': 'fake arguments'
        }

    def tearDown(self):
        TaskHistory.objects.all().delete()

    def test_create_obj_task_history(self):
        resp = TaskRegister.create_task(self.task_params)

        self.assertTrue(isinstance(resp, TaskHistory))
        self.assertEqual(resp.task_name, 'fake_task_name')
        self.assertEqual(resp.arguments, 'fake arguments')
        self.assertEqual(resp.object_id, None)
        self.assertEqual(resp.object_class, None)

    def test_create_object_ref_when_have_database(self):
        '''
        When the key 'database' is present on task_params
        the code save the id on task_history.object_id and
        your class on task_history.object_class
        '''

        fake_database = MagicMock()
        fake_database.id = 999
        fake_database._meta.db_table = 'logical_database'
        self.task_params.update({'database': fake_database})
        resp = TaskRegister.create_task(self.task_params)

        self.assertEqual(resp.object_id, 999)
        self.assertEqual(resp.object_class, 'logical_database')


@patch.object(TaskRegister, 'create_task')
class TaskCallBaseTestCase(object):

    method_to_call = None
    delay_to_mock = ''
    call_params = {}
    create_fields_to_validate = []
    delay_fields_to_validate = []

    def setUp(self):
        self.task_params = {
            'task_name': 'fake_task_name',
            'arguments': 'fake arguments'
        }

    def _validate_fields_in_params(self, fields, params):
        fail_msg_tmpl = "Field <{}> not found in {}"

        for field in fields:
            self.assertIn(field, params, fail_msg_tmpl.format(field, params))

    def test_default_calls(self, mocked_create):

        with patch(self.delay_to_mock) as mocked_delay:
            func = getattr(TaskRegister, self.method_to_call)
            func(**self.call_params)

            self.assertTrue(mocked_create.called)

            create_task_param = mocked_create.call_args[0][0]
            self._validate_fields_in_params(
                self.create_fields_to_validate,
                create_task_param
            )

            delay_params = mocked_delay.call_args[1]
            self._validate_fields_in_params(
                self.delay_fields_to_validate,
                delay_params
            )


class DatabaseDiskResizeCallTestCase(TestCase, TaskCallBaseTestCase):

    method_to_call = 'database_disk_resize'
    delay_to_mock = 'notification.tasks.database_disk_resize.delay'
    call_params = {
        'database': MagicMock(),
        'user': 'user',
        'disk_offering': 'disk_offering'
    }
    create_fields_to_validate = ['task_name', 'arguments', 'database']
    delay_fields_to_validate = ['database', 'user', 'disk_offering', 'task_history']


class DatabaseDiskResizeCallWithUserTestCase(DatabaseDiskResizeCallTestCase):

    method_to_call = 'database_disk_resize'
    delay_to_mock = 'notification.tasks.database_disk_resize.delay'
    call_params = {
        'database': MagicMock(),
        'user': 'user',
        'disk_offering': 'disk_offering',
        'register_user': True
    }
    create_fields_to_validate = ['task_name', 'arguments', 'database', 'user']
    delay_fields_to_validate = ['database', 'user', 'disk_offering', 'task_history']

    @patch.object(TaskRegister, 'create_task')
    @patch('notification.tasks.database_disk_resize.delay')
    def test_database_disk_resize_with_task_name(self, mocked_delay, mocked_create):
        TaskRegister.database_disk_resize(
            database=MagicMock(),
            user='user',
            disk_offering='disk_offering',
            task_name='custom task name'
        )

        self.assertTrue(mocked_create.called)

        create_task_param = mocked_create.call_args[0][0]
        self.assertEqual(create_task_param['task_name'], 'custom task name')


class DatabaseDestroyCallTestCase(TestCase, TaskCallBaseTestCase):

    method_to_call = 'database_destroy'
    delay_to_mock = 'notification.tasks.destroy_database.delay'
    call_params = {
        'database': MagicMock(),
        'user': 'user',
    }
    create_fields_to_validate = ['task_name', 'arguments', 'database', 'user']
    delay_fields_to_validate = ['database', 'user', 'task_history']


class DatabaseResizeCallTestCase(TestCase, TaskCallBaseTestCase):

    method_to_call = 'database_resize'
    delay_to_mock = 'notification.tasks.resize_database.delay'
    call_params = {
        'database': MagicMock(),
        'user': 'user',
        'offering': 'offering'
    }
    create_fields_to_validate = ['task_name', 'arguments', 'database', 'user']
    delay_fields_to_validate = ['database', 'user', 'task', 'offering']


class DatabaseResizeRetryCallTestCase(TestCase, TaskCallBaseTestCase):

    method_to_call = 'database_resize_retry'
    delay_to_mock = 'notification.tasks.resize_database.delay'
    call_params = {
        'database': MagicMock(),
        'user': 'user',
        'offering': 'offering',
        'original_offering': 'original_offering',
        'since_step': 'since_step'
    }
    create_fields_to_validate = ['task_name', 'arguments', 'database', 'user']
    delay_fields_to_validate = [
        'database', 'user', 'task', 'offering',
        'original_offering', 'since_step'
    ]


class DatabaseAddInstancesCallTestCase(TestCase, TaskCallBaseTestCase):

    method_to_call = 'database_add_instances'
    delay_to_mock = 'notification.tasks.add_instances_to_database.delay'
    call_params = {
        'database': MagicMock(),
        'user': 'user',
        'number_of_instances': 9,
        'number_of_instances_before_task': 3,
    }
    create_fields_to_validate = ['task_name', 'arguments', 'database', 'user']
    delay_fields_to_validate = [
        'database', 'user', 'task', 'number_of_instances'
    ]


class DatabaseRemoveInstancesCallTestCase(TestCase, TaskCallBaseTestCase):

    method_to_call = 'database_remove_instance'
    delay_to_mock = 'notification.tasks.remove_readonly_instance.delay'
    call_params = {
        'database': MagicMock(),
        'user': 'user',
        'instance': 'instance',
    }
    create_fields_to_validate = ['task_name', 'arguments', 'database', 'user']
    delay_fields_to_validate = [
        'user', 'task', 'instance'
    ]


class DatabaseAnalyzeCallTestCase(TestCase, TaskCallBaseTestCase):

    method_to_call = 'databases_analyze'
    delay_to_mock = 'dbaas_services.analyzing.tasks.analyze_databases.delay'
    call_params = {}
    create_fields_to_validate = ['task_name', 'arguments']
    delay_fields_to_validate = [
        'task_history'
    ]


class DatabaseCloneCallTestCase(TestCase, TaskCallBaseTestCase):

    method_to_call = 'database_clone'
    delay_to_mock = 'notification.tasks.clone_database.delay'
    call_params = {
        'origin_database': MagicMock(),
        'user': 'user',
        'clone_name': 'instance',
        'plan': 'plan',
        'environment': 'environment'
    }
    create_fields_to_validate = ['task_name', 'arguments', 'database', 'user']
    delay_fields_to_validate = [
        'origin_database', 'user', 'clone_name', 'plan', 'environment',
        'task_history'
    ]


class DatabaseCreateCallTestCase(TestCase, TaskCallBaseTestCase):

    method_to_call = 'database_create'
    delay_to_mock = 'notification.tasks.create_database.delay'
    call_params = {
        'user': 'user',
        'name': 'name',
        'plan': physical_factory.PlanFactory(),
        'environment': 'environment',
        'team': 'team',
        'project': 'project',
        'description': 'description',
        'subscribe_to_email_events': 'subscribe_to_email_events',
        'backup_hour': 'backup_hour',
        'maintenance_window': 'maintenance_window',
        'maintenance_day': 'maintenance_day',
    }
    create_fields_to_validate = ['task_name', 'arguments']
    delay_fields_to_validate = [
        'user', 'name', 'plan', 'environment', 'team', 'project',
        'description', 'subscribe_to_email_events', 'task', 'is_protected'
    ]


class DatabaseCreateCallWithUserTestCase(TestCase, TaskCallBaseTestCase):

    method_to_call = 'database_create'
    delay_to_mock = 'notification.tasks.create_database.delay'
    call_params = {
        'user': 'user',
        'name': 'name',
        'plan': physical_factory.PlanFactory(),
        'environment': 'environment',
        'team': 'team',
        'project': 'project',
        'description': 'description',
        'subscribe_to_email_events': 'subscribe_to_email_events',
        'register_user': True,
        'backup_hour': 'backup_hour',
        'maintenance_window': 'maintenance_window',
        'maintenance_day': 'maintenance_day',
    }
    create_fields_to_validate = ['task_name', 'arguments', 'user']
    delay_fields_to_validate = [
        'user', 'name', 'plan', 'environment', 'team', 'project',
        'description', 'subscribe_to_email_events', 'task', 'is_protected'
    ]


class DatabaseBackupCallTestCase(TestCase, TaskCallBaseTestCase):

    method_to_call = 'database_backup'
    delay_to_mock = 'backup.tasks.make_database_backup.delay'
    call_params = {'database': MagicMock(), 'user': 'fake.user_name'}
    create_fields_to_validate = ['task_name', 'arguments', 'database']
    delay_fields_to_validate = ['database', 'task']


class DatabaseRemoveBackupCallTestCase(TestCase, TaskCallBaseTestCase):

    method_to_call = 'database_remove_backup'
    delay_to_mock = 'backup.tasks.remove_database_backup.delay'
    call_params = {
        'database': MagicMock(),
        'snapshot': 'snapshot', 'user': 'fake.user_name'
    }
    create_fields_to_validate = ['task_name', 'arguments']
    delay_fields_to_validate = ['snapshot', 'task']


class RestoreSnapshotCallTestCase(TestCase, TaskCallBaseTestCase):

    def setUp(self):
        super(RestoreSnapshotCallTestCase, self).setUp()
        self.database = logical_factory.DatabaseFactory()
        self.call_params['database'] = self.database

    def tearDown(self):
        if self.database:
            self.database.delete()

    method_to_call = 'restore_snapshot'
    delay_to_mock = 'maintenance.tasks.restore_database.delay'
    call_params = {
        'database': MagicMock(),
        'user': 'user',
        'snapshot': 'snapshot'
    }
    create_fields_to_validate = ['task_name', 'arguments', 'database', 'user']
    delay_fields_to_validate = ['database', 'task', 'snapshot', 'user']
