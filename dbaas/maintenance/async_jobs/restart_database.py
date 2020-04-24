from maintenance.async_jobs import BaseJob
from maintenance.models import RestartDatabase


__all__ = ('RestartDatabaseJob',)


class RestartDatabaseJob(BaseJob):
    step_manger_class = RestartDatabase
    get_steps_method = 'restart_database_steps'
    success_msg = 'Database restarted with success'
    error_msg = 'Could not restart database'

    @property
    def instances(self):
        return map(
            lambda host: host.instances.first(),
            self.database.infra.hosts
        )
