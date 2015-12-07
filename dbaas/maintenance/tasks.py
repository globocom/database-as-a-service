from util import exec_remote_command
from datetime import datetime
from dbaas.celery import app
import models
import logging
from notification.models import TaskHistory
from util import get_worker_name
from util import build_context_script
from util import get_dict_lines
from django.core.exceptions import ObjectDoesNotExist
from registered_functions.functools import _get_function

LOG = logging.getLogger(__name__)


@app.task(bind=True)
def execute_scheduled_maintenance(self, maintenance_id):
    LOG.debug("Maintenance id: {}".format(maintenance_id))
    maintenance = models.Maintenance.objects.get(id=maintenance_id)

    models.Maintenance.objects.filter(id=maintenance_id,
                                      ).update(status=maintenance.RUNNING, started_at=datetime.now())
    LOG.info("Maintenance {} is RUNNING".format(maintenance,))

    worker_name = get_worker_name()
    task_history = TaskHistory.register(
        request=self.request, worker_name=worker_name)

    LOG.info("id: %s | task: %s | kwargs: %s | args: %s" % (
        self.request.id, self.request.task, self.request.kwargs, str(self.request.args)))

    task_history.update_details(persist=True,
                                details="Executing Maintenance: {}".format(maintenance))

    for hm in models.HostMaintenance.objects.filter(maintenance=maintenance):
        main_output = {}
        hm.status = hm.RUNNING
        hm.started_at = datetime.now()
        hm.save()

        if hm.host is None:
            hm.status = hm.UNAVAILABLEHOST
            hm.finished_at = datetime.now()
            hm.save()
            continue

        host = hm.host
        update_task = "\nRunning Maintenance on {}".format(host)

        try:
            cloudstack_host_attributes = host.cs_host_attributes.get()
        except ObjectDoesNotExist as e:
            LOG.warn(
                "Host {} does not have cloudstack attrs...{}".format(hm.host, e))
            hm.status = hm.UNAVAILABLECSHOSTATTR
            hm.finished_at = datetime.now()
            hm.save()
            continue

        param_dict = {}
        for param in models.MaintenanceParameters.objects.filter(maintenance=maintenance):
            param_function = _get_function(param.function_name)
            param_dict[param.parameter_name] = param_function(host.id)

        main_script = build_context_script(param_dict, maintenance.main_script)
        exit_status = exec_remote_command(server=host.address,
                                          username=cloudstack_host_attributes.vm_user,
                                          password=cloudstack_host_attributes.vm_password,
                                          command=main_script, output=main_output)

        if exit_status == 0:
            hm.status = hm.SUCCESS
        else:

            if maintenance.rollback_script:
                rollback_output = {}
                hm.status = hm.ROLLBACK
                hm.save()

                rollback_script = build_context_script(
                    param_dict, maintenance.rollback_script)
                exit_status = exec_remote_command(server=host.address,
                                                  username=cloudstack_host_attributes.vm_user,
                                                  password=cloudstack_host_attributes.vm_password,
                                                  command=rollback_script, output=rollback_output)

                if exit_status == 0:
                    hm.status = hm.ROLLBACK_SUCCESS
                else:
                    hm.status = hm.ROLLBACK_ERROR

                hm.rollback_log = get_dict_lines(rollback_output)

            else:
                hm.status = hm.ERROR

        update_task += "...status: {}".format(hm.status)

        task_history.update_details(persist=True,
                                    details=update_task)

        hm.main_log = get_dict_lines(main_output)
        hm.finished_at = datetime.now()
        hm.save()

    models.Maintenance.objects.filter(id=maintenance_id,
                                      ).update(status=maintenance.FINISHED, finished_at=datetime.now())

    task_history.update_status_for(TaskHistory.STATUS_SUCCESS,
                                   details='Maintenance executed succesfully')

    LOG.info("Maintenance: {} has FINISHED".format(maintenance,))
