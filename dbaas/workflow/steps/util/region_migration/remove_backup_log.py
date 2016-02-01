# -*- coding: utf-8 -*-
import logging
from dbaas_cloudstack.models import HostAttr as CsHostAttr
from util import full_stack
from util import exec_remote_command
from workflow.steps.util import get_backup_log_configuration_dict
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0014

LOG = logging.getLogger(__name__)


class RemoveBackupLog(BaseStep):

    def __unicode__(self):
        return "Removing backup log..."

    def do(self, workflow_dict):
        try:

            backup_log_dict = get_backup_log_configuration_dict(environment=workflow_dict['source_environment'],
                                                                databaseinfra=workflow_dict['databaseinfra'])
            if backup_log_dict is None:
                return True

            host = workflow_dict['source_hosts'][0]
            host_csattr = CsHostAttr.objects.get(host=host)

            exec_remote_command(server=host.address,
                                username=host_csattr.vm_user,
                                password=host_csattr.vm_password,
                                command=backup_log_dict['CLEAN_BACKUP_LOG_SCRIPT'])

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0014)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        try:

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0014)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
