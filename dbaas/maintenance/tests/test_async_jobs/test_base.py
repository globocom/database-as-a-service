from mock import patch, MagicMock, PropertyMock

from django.test import TestCase
from model_mommy import mommy

from maintenance.async_jobs import BaseJob
from dbaas.tests.helpers import DatabaseHelper


class BaseTestCase(TestCase):

    def setUp(self):
        self.fake_request = MagicMock()
        self.database = DatabaseHelper.create()
        self.fake_task_schedule = mommy.make(
            'maintenance.TaskSchedule',
            database=self.database
        )
        self.fake_previous_step_manager = mommy.make(
            'maintenance.UpdateSsl',
            database=self.database,
            current_step=9,
            can_do_retry=1,
            task_schedule=self.fake_task_schedule
        )
        self.fake_task = mommy.make(
            'TaskHistory',
            task_name='fake.task.name'
        )
        self._configure_job()

    @patch.object(BaseJob, '__init__', new=MagicMock(return_value=None))
    def _configure_job(self):
        self.base_job = BaseJob()
        self.base_job.auto_rollback = True
        self.base_job.get_steps_method = 'update_ssl_steps'
        self.base_job.database = self.database
        self.fake_step_manager_class = (
            self.fake_previous_step_manager._meta.model
        )
        self.base_job.step_manger_class = self.fake_step_manager_class


@patch('maintenance.async_jobs.base.steps_for_instances')
@patch.object(BaseJob, 'instances', new=PropertyMock())
class RunTestCase(BaseTestCase):
    def _configure_job(self):
        BaseJob.get_steps_method = 'update_ssl_steps'
        self.fake_step_manager_class = (
            self.fake_previous_step_manager._meta.model
        )
        BaseJob.step_manger_class = self.fake_step_manager_class
        with patch.object(BaseJob, 'register_task_history',
                          new=MagicMock(return_value=self.fake_task)):
            self.base_job = BaseJob(
                request=self.fake_request,
                database=self.database,
                task=self.fake_task
            )

    def test_params_first_run(self, steps_for_instances_mock):
        self.base_job.run()

        call_args = steps_for_instances_mock.call_args[0]
        call_kwargs = steps_for_instances_mock.call_args[1]

        param_task = call_args[2]
        param_since_step = call_args[4]
        param_step_manager = call_kwargs['step_manager']
        self.assertEqual(param_task, self.fake_task)
        self.assertNotEqual(
            param_step_manager,
            self.fake_previous_step_manager
        )
        self.assertEqual(param_since_step, 0)

    @patch('notification.models.TaskHistory.set_status_success')
    @patch('maintenance.models.UpdateSsl.set_success')
    def test_success(self, manager_set_success_mock, task_set_success_mock,
                     steps_for_instances_mock):
        steps_for_instances_mock.return_value = True
        self.base_job.run()

        self.assertTrue(task_set_success_mock.called)
        self.assertTrue(manager_set_success_mock.called)

    @patch('notification.models.TaskHistory.set_status_error')
    @patch('maintenance.models.UpdateSsl.set_error')
    @patch.object(BaseJob, 'run_auto_rollback_if_configured')
    def test_error(self, auto_rollback_mock, manager_set_error_mock,
                   task_set_error_mock, steps_for_instances_mock):
        steps_for_instances_mock.return_value = False
        self.base_job.run()
        self.assertTrue(task_set_error_mock.called)
        self.assertTrue(manager_set_error_mock.called)
        self.assertTrue(auto_rollback_mock.called)


@patch.object(BaseJob, 'instances', new=PropertyMock())
@patch('maintenance.models.UpdateSsl.cleanup')
class RunAutoCleanupTestCase(BaseTestCase):

    def setUp(self):
        super(RunAutoCleanupTestCase, self).setUp()
        self.base_job.step_manager = self.fake_previous_step_manager

    def test_cleanup_false_force_false(self, cleanup_mock):
        self.base_job.auto_cleanup = False
        self.base_job.run_auto_cleanup_if_configured(force=False)

        self.assertFalse(cleanup_mock.called)

    def test_cleanup_true_force_false(self, cleanup_mock):
        self.base_job.auto_cleanup = True
        self.base_job.run_auto_cleanup_if_configured(force=False)

        self.assertTrue(cleanup_mock.called)

    def test_cleanup_false_force_true(self, cleanup_mock):
        self.base_job.auto_cleanup = False
        self.base_job.run_auto_cleanup_if_configured(force=True)

        self.assertTrue(cleanup_mock.called)

    def test_cleanup_true_force_true(self, cleanup_mock):
        self.base_job.auto_cleanup = True
        self.base_job.run_auto_cleanup_if_configured(force=True)

        self.assertTrue(cleanup_mock.called)


@patch.object(BaseJob, 'rollback')
@patch.object(BaseJob, 'run_auto_cleanup_if_configured')
@patch.object(BaseJob, 'instances', new=PropertyMock())
class RunAutoRollbackTestCase(BaseTestCase):

    def test_do_not_run_if_not_configured(self, cleanup_mock, rollback_mock):
        self.base_job.auto_rollback = False
        self.base_job.run_auto_rollback_if_configured()

        self.assertFalse(rollback_mock.called)
        self.assertFalse(cleanup_mock.called)

    def test_params(self, cleanup_mock, rollback_mock):
        self.base_job.step_manager = self.fake_previous_step_manager
        self.base_job.task = self.fake_task
        self.base_job.run_auto_rollback_if_configured()

        call_args = rollback_mock.call_args[0]

        param_task = call_args[2]
        param_step_manager = call_args[3]
        self.assertNotEqual(param_task, self.fake_task)
        self.assertEqual(
            param_task.task_name,
            '{}_rollback'.format(self.fake_task.task_name)
        )
        self.assertNotEqual(
            param_step_manager,
            self.fake_previous_step_manager
        )
        self.assertIsNone(param_step_manager.task_schedule)
        self.assertFalse(param_step_manager.can_do_retry)

    @patch('notification.models.TaskHistory.set_status_success')
    @patch('maintenance.models.UpdateSsl.set_success')
    def test_rollback_success(self, manager_set_success_mock,
                              task_set_success_mock, cleanup_mock,
                              rollback_mock):
        self.base_job.step_manager = self.fake_previous_step_manager
        self.base_job.task = self.fake_task
        rollback_mock.return_value = True
        self.base_job.run_auto_rollback_if_configured()

        self.assertTrue(task_set_success_mock.called)
        self.assertTrue(manager_set_success_mock.called)
        self.assertFalse(cleanup_mock.called)

    @patch('notification.models.TaskHistory.set_status_error')
    @patch('maintenance.models.UpdateSsl.set_error')
    def test_rollback_error_without_cleanup(self, manager_set_error_mock,
                                            task_set_error_mock, cleanup_mock,
                                            rollback_mock):
        self.base_job.step_manager = self.fake_previous_step_manager
        self.base_job.task = self.fake_task
        rollback_mock.return_value = False
        self.base_job.run_auto_rollback_if_configured()

        self.assertTrue(task_set_error_mock.called)
        self.assertTrue(manager_set_error_mock.called)

    @patch('notification.models.TaskHistory.set_status_error')
    @patch('maintenance.models.UpdateSsl.set_error')
    def test_rollback_error_with_cleanup(self, manager_set_error_mock,
                                         task_set_error_mock,
                                         cleanup_mock,
                                         rollback_mock):
        self.base_job.step_manager = self.fake_previous_step_manager
        self.base_job.task = self.fake_task
        rollback_mock.return_value = False
        self.base_job.run_auto_rollback_if_configured()

        self.assertTrue(task_set_error_mock.called)
        self.assertTrue(manager_set_error_mock.called)
        self.assertTrue(cleanup_mock.called)
        cleanup_call_kwargs = cleanup_mock.call_args[1]
        self.assertIn('force', cleanup_call_kwargs)
        self.assertTrue(cleanup_call_kwargs['force'])


class CreateStepManagerTestCase(BaseTestCase):

    def test_create_copy_of_previous_manager(self):
        new_step_manager = self.base_job._create_step_manager(
            previous_step_manager=self.fake_previous_step_manager,
            scheduled_task=None,
            database=self.database,
            task=self.fake_task
        )

        self.assertNotEqual(
            self.fake_previous_step_manager,
            new_step_manager
        )
        self.assertEqual(new_step_manager.database, self.database)
        self.assertEqual(new_step_manager.task, self.fake_task)
        self.assertEqual(new_step_manager.status, new_step_manager.RUNNING)
        self.assertEqual(new_step_manager.current_step, 9)
        self.assertEqual(
            new_step_manager.task_schedule,
            self.fake_task_schedule
        )

    def test_create_copy_of_previous_manager_from_database(self):
        self.fake_previous_step_manager.status = (
            self.fake_previous_step_manager.ERROR
        )
        self.fake_previous_step_manager.save()
        new_step_manager = self.base_job._create_step_manager(
            previous_step_manager=None,
            scheduled_task=None,
            database=self.database,
            task=self.fake_task
        )

        self.assertNotEqual(
            self.fake_previous_step_manager,
            new_step_manager
        )
        self.assertEqual(new_step_manager.database, self.database)
        self.assertEqual(new_step_manager.task, self.fake_task)
        self.assertEqual(new_step_manager.status, new_step_manager.RUNNING)
        self.assertEqual(new_step_manager.current_step, 9)
        self.assertEqual(
            new_step_manager.task_schedule,
            self.fake_task_schedule
        )

    def test_create_copy_of_previous_manager_override_task_schedule(self):
        another_task_schedule = mommy.make(
            'maintenance.TaskSchedule',
            database=self.database
        )
        new_step_manager = self.base_job._create_step_manager(
            previous_step_manager=None,
            scheduled_task=another_task_schedule,
            database=self.database,
            task=self.fake_task
        )

        self.assertNotEqual(
            self.fake_previous_step_manager,
            new_step_manager
        )
        self.assertEqual(
            new_step_manager.task_schedule,
            another_task_schedule
        )

    def test_create_new_manager_when_dont_have_previous(self):
        another_task_schedule = mommy.make(
            'maintenance.TaskSchedule',
            database=self.database
        )
        self.fake_previous_step_manager.can_do_retry = False
        self.fake_previous_step_manager.save()
        new_step_manager = self.base_job._create_step_manager(
            previous_step_manager=None,
            scheduled_task=another_task_schedule,
            database=self.database,
            task=self.fake_task
        )

        self.assertEqual(new_step_manager.database, self.database)
        self.assertEqual(new_step_manager.task, self.fake_task)
        self.assertEqual(new_step_manager.status, new_step_manager.RUNNING)
        self.assertEqual(new_step_manager.current_step, 0)
        self.assertEqual(
            new_step_manager.task_schedule,
            another_task_schedule
        )
