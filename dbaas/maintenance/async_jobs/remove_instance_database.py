from maintenance.async_jobs import BaseJob
from maintenance.models import RemoveInstanceDatabase


__all__ = ('RemoveInstanceDatabase',)


class RemoveInstanceDatabaseJob(BaseJob):
    step_manger_class = RemoveInstanceDatabase
    get_steps_method = 'remove_readonly_instance_steps'
    success_msg = 'Instance removed with success'
    error_msg = 'Could not remove instance'

    def __init__(self, request, database, task, instance, since_step=None,
                 step_manager=None, scheduled_task=None,
                 auto_rollback=False, auto_cleanup=False):
        super(RemoveInstanceDatabaseJob, self).__init__(
            request, database, task, since_step,
            step_manager, scheduled_task,
            auto_rollback, auto_cleanup
        )
        self._instance = instance

    @property
    def instances(self):
        return [self._instance]
