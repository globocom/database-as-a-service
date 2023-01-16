from dbaas.celery import app

from celery.utils.log import get_task_logger
from simple_audit.models import AuditRequest

from notification.models import TaskHistory
from util import email_notifications, get_worker_name

LOG = get_task_logger(__name__)


@app.task(bind=True)
def database_disk_resize(self, database, disk_offering, task_history, user):
    from workflow.steps.util.volume_provider import ResizeVolume, Resize2fs

    AuditRequest.new_request("database_disk_resize", user, "localhost")

    if not database.pin_task(task_history):
        task_history.error_in_lock(database)
        return False

    databaseinfra = database.databaseinfra
    old_disk_offering = database.databaseinfra.disk_offering
    resized = []

    try:
        worker_name = get_worker_name()
        task_history = TaskHistory.register(
            request=self.request, task_history=task_history,
            user=user, worker_name=worker_name
        )

        task_history.update_details(
            persist=True,
            details='\nLoading Disk offering'
        )

        databaseinfra.disk_offering = disk_offering
        databaseinfra.save()

        for instance in databaseinfra.get_driver().get_database_instances():

            task_history.update_details(
                persist=True,
                details='\nChanging instance {} to '
                        'NFS {}'.format(instance, disk_offering)
            )
            ResizeVolume(instance).do()
            Resize2fs(instance).do()
            resized.append(instance)

        task_history.update_details(
            persist=True,
            details='\nUpdate DBaaS metadata from {} to {}'.format(
                old_disk_offering, disk_offering
            )
        )

        task_history.update_status_for(
            status=TaskHistory.STATUS_SUCCESS,
            details='\nDisk resize successfully done.'
        )

        database.finish_task()
        return True

    except Exception as e:
        error = "Disk resize ERROR: {}".format(e)
        LOG.error(error)

        if databaseinfra.disk_offering != old_disk_offering:
            task_history.update_details(
                persist=True, details='\nUndo update DBaaS metadata'
            )
            databaseinfra.disk_offering = old_disk_offering
            databaseinfra.save()

        for instance in resized:
            task_history.update_details(
                persist=True,
                details='\nUndo NFS change for instance {}'.format(instance)
            )
            ResizeVolume(instance).do()

        task_history.update_status_for(TaskHistory.STATUS_ERROR, details=error)
        database.finish_task()
    finally:
        AuditRequest.cleanup_request()


class TaskRegisterBase:
    TASK_CLASS = TaskHistory

    @classmethod
    def create_task(cls, params):
        database = params.pop('database', None)

        task = cls.TASK_CLASS()

        if database:
            task.object_id = database.id
            task.object_class = database._meta.db_table
            database_name = database.name
        else:
            database_name = params.pop('database_name', '')

        task.database_name = database_name

        for k, v in params.iteritems():
            setattr(task, k, v)

        task.save()

        return task

    @classmethod
    def database_disk_resize(cls,
                             database,
                             user,
                             disk_offering,
                             task_name=None,
                             register_user=True,
                             **kw):

        task_params = {
            'task_name': ('database_disk_resize' if task_name is None
                          else task_name),
            'arguments': 'Database name: {}'.format(database.name),
            'database': database,
            'relevance': TaskHistory.RELEVANCE_CRITICAL
        }

        task_params.update(**{'user': user} if register_user else {})
        task = cls.create_task(task_params)
        database_disk_resize.delay(
            database=database,
            user=user,
            disk_offering=disk_offering,
            task_history=task
        )

        return task