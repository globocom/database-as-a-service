from logical.models import Database
from system.models import Configuration
from datetime import date, timedelta
from dbaas.celery import app
from util.decorators import only_one
from util.providers import destroy_infra
from simple_audit.models import AuditRequest
from notification.models import TaskHistory
from account.models import AccountUser
import logging

LOG = logging.getLogger(__name__)


@app.task(bind=True)
@only_one(key="purgequarantinekey", timeout=1000)
def purge_quarantine(self,):
    user = AccountUser.objects.get(username='admin')
    AuditRequest.new_request("purge_quarantine", user, "localhost")
    try:

        task_history = TaskHistory.register(request=self.request, user=user)

        LOG.info("id: %s | task: %s | kwargs: %s | args: %s" % (
            self.request.id, self.request.task, self.request.kwargs, str(self.request.args)))
        quarantine_time = Configuration.get_by_name_as_int(
            'quarantine_retention_days')
        quarantine_time_dt = date.today() - timedelta(days=quarantine_time)

        databases = Database.objects.filter(is_in_quarantine=True,
                                            quarantine_dt__lte=quarantine_time_dt)

        for database in databases:
            if database.plan.provider == database.plan.CLOUDSTACK:
                databaseinfra = database.databaseinfra

                destroy_infra(databaseinfra=databaseinfra, task=task_history)
            else:
                database.delete()

            LOG.info("The database %s was deleted, because it was set to quarentine %d days ago" % (
                database.name, quarantine_time))

        task_history.update_status_for(
            TaskHistory.STATUS_SUCCESS, details='Databases destroyed successfully')
        return

    except Exception:
        task_history.update_status_for(
            TaskHistory.STATUS_ERROR, details="Error")
        return
    finally:
        AuditRequest.cleanup_request()
