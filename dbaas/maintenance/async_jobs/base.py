from copy import copy

from notification.models import TaskHistory
from util import get_worker_name
from workflow.workflow import steps_for_instances, rollback_for_instances_full


__all__ = ('BaseJob',)


class BaseJob(object):
    step_manger_class = None
    get_steps_method = None
    success_msg = ''
    error_msg = ''
    success_auto_rollback_msg = ''
    error_auto_rollback_msg = ''

    def __init__(self, request, database, task, since_step=None,
                 step_manager=None, scheduled_task=None,
                 auto_rollback=False, auto_cleanup=False):

        self.request = request
        self.database = database
        self.task = self.register_task_history(task)
        self.step_manager = self._create_step_manager(
            previous_step_manager=step_manager,
            scheduled_task=scheduled_task,
            database=database,
            task=self.task
        )
        self.current_step = self.step_manager.current_step
        self.auto_rollback = auto_rollback
        self.auto_cleanup = auto_cleanup
        self.scheduled_task = scheduled_task

    @property
    def steps(self):
        if self.get_steps_method is None:
            raise Exception(('You must set your get_steps method name '
                             'class in variable get_steps_method'))
        get_steps_func = getattr(self.database.infra, self.get_steps_method)
        return get_steps_func()

    @property
    def instances(self):
        raise NotImplementedError('You must override this method')

    def register_task_history(self, task):
        return TaskHistory.register(
            request=self.request, task_history=task, user=task.user,
            worker_name=get_worker_name()
        )

    def _create_step_manager(self, previous_step_manager, scheduled_task,
                             database, task):
        if self.step_manger_class is None:
            raise Exception(('You must set your step_manager class in variable'
                            'step_manager_class'))
        step_manager = self.step_manger_class()
        if previous_step_manager is None:
            previous_step_manager = self.step_manger_class.objects.filter(
                can_do_retry=True,
                database=database,
                status=self.step_manger_class.ERROR
            ).last()
        if previous_step_manager:
            step_manager = copy(previous_step_manager)
            step_manager.id = None
            step_manager.started_at = None
            step_manager.current_step = previous_step_manager.current_step
            step_manager.task_schedule = (
                previous_step_manager.task_schedule
            )
        step_manager.database = database
        step_manager.task = task
        if scheduled_task:
            step_manager.task_schedule = scheduled_task
        step_manager.set_running()
        step_manager.save()

        return step_manager

    def reload_step_manager(self):
        self.step_manager = self.step_manger_class.objects.get(
            id=self.step_manager.id
        )

    def rollback(self, steps, instances, new_task, rollback_step_manager):
        return rollback_for_instances_full(
            self.steps, self.instances, new_task,
            rollback_step_manager.get_current_step,
            rollback_step_manager.update_step,
            rollback_step_manager
        )

    def run_auto_cleanup_if_configured(self, step_manager=None, force=False):
        if self.auto_cleanup or force:
            step_manager = step_manager or self.step_manager
            if hasattr(step_manager, 'cleanup'):
                step_manager.cleanup(self.instances)

    def run_auto_rollback_if_configured(self):
        if self.auto_rollback:
            new_task = copy(self.task)
            new_task.id = None
            new_task.details = ''
            new_task.task_name += '_rollback'
            new_task.task_status = new_task.STATUS_RUNNING
            new_task.save()
            rollback_step_manager = copy(self.step_manager)
            rollback_step_manager.id = None
            rollback_step_manager.task_schedule = None
            rollback_step_manager.can_do_retry = 0
            rollback_step_manager.save()
            result = self.rollback(
                self.steps, self.instances, new_task, rollback_step_manager
            )
            if result:
                rollback_step_manager.set_success()
                self.task.set_status_success(
                    self.success_auto_rollback_msg
                )
            else:
                self.run_auto_cleanup_if_configured(
                    rollback_step_manager, force=True
                )
                rollback_step_manager.set_error()
                self.task.set_status_error(self.error_auto_rollback_msg)

    def run(self):
        result = steps_for_instances(
            self.steps,
            self.instances,
            self.task,
            self.step_manager.update_step,
            self.current_step,
            step_manager=self.step_manager
        )
        self.reload_step_manager()
        if result:
            self.step_manager.set_success()
            self.task.set_status_success(self.success_msg)
        else:
            self.step_manager.set_error()
            self.task.set_status_error(self.error_msg)
            self.run_auto_rollback_if_configured()
            self.run_auto_cleanup_if_configured()
