from django.db import models


class DatabaseMaintenanceTaskManager(models.Manager):
    use_for_related_fields = True

    def need_retry(self, **kwargs):
        """ This method checks wheather a maintenance task needs retry or not.
        It returns the task itself or False when there's no task that have
        failed. This implementation only works for models composed by a
        database(type Database) attribute."""
        database = kwargs.get('database', None)
        last_task = self.filter(database=database).last()

        if (last_task and last_task.status == self.model.ERROR and
                last_task.can_do_retry):
            return last_task

        return False

    def last_available_retry(self, **kwargs):
        retry_filter = {"can_do_retry": True}
        retry_filter.update(kwargs)
        return self.filter(**retry_filter).last()
