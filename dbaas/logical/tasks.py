from logical.models import Database
from system.models import Configuration
from datetime import date, timedelta
from dbaas.celery import app
from util.decorators import only_one
from simple_audit.models import AuditRequest
from notification.models import TaskHistory
from account.models import AccountUser
import logging

LOG = logging.getLogger(__name__)


@app.task(acks_late=True, bind=True)
@only_one(key="purgequarantinekey", timeout=1000)
def purge_quarantine(self,):
    user = AccountUser.objects.get(username='admin')
    AuditRequest.new_request("purge_quarantine", user, "localhost")

    try:
        task_history = TaskHistory.register(request=self.request, user=user)
        task_history.relevance = TaskHistory.RELEVANCE_WARNING

        LOG.info(
            "id: {} | task: {} | kwargs: {} | args: {}".format(
                self.request.id, self.request.task,
                self.request.kwargs, str(self.request.args)
            )
        )

        quarantine_time = Configuration.get_by_name_as_int(
            'quarantine_retention_days'
        )
        quarantine_time_dt = date.today() - timedelta(days=quarantine_time)
        task_history.add_detail(
            "Quarantine date older than {}".format(quarantine_time_dt)
        )

        databases = Database.objects.filter(
            is_in_quarantine=True, quarantine_dt__lte=quarantine_time_dt
        )
        task_history.add_detail(
            "Databases to purge: {}".format(len(databases))
        )

        for database in databases:
            task_history.add_detail('Deleting {}...'.format(database), level=2)
            database.destroy(user)

        task_history.update_status_for(
            TaskHistory.STATUS_SUCCESS,
            details='Listed databases were destroyed successfully.'
        )
        return

    except Exception as e:
        task_history.update_status_for(
            TaskHistory.STATUS_ERROR, details="Error\n{}".format(e))
        return
    finally:
        AuditRequest.cleanup_request()
