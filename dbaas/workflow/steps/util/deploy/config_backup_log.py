# -*- coding: utf-8 -*-
import logging
from dbaas_cloudstack.models import HostAttr as CsHostAttr
from util import full_stack
from util import exec_remote_command
from util import build_context_script
from workflow.steps.util import test_bash_script_error
from workflow.steps.util import get_backup_log_configuration_dict
from workflow.steps.util import build_backup_log_script
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0014

LOG = logging.getLogger(__name__)


class ConfigBackupLog(BaseStep):

    def __unicode__(self):
        return "Configing backup log..."

    def do(self, workflow_dict):
        try:

            backup_log_dict = get_backup_log_configuration_dict(environment=workflow_dict['environment'],
                                                                databaseinfra=workflow_dict['databaseinfra'])
            if backup_log_dict is None:
                LOG.info("There is not any backup log configuration for this database...")
                return True

            for index, instance in enumerate(workflow_dict['instances']):

                if instance.instance_type == instance.MONGODB_ARBITER:
                    continue

                if instance.instance_type == instance.REDIS_SENTINEL:
                    continue

                host = instance.hostname

                LOG.info("Getting vm credentials...")
                host_csattr = CsHostAttr.objects.get(host=host)

                script = test_bash_script_error()
                script += build_backup_log_script()

                contextdict = backup_log_dict

                script = build_context_script(contextdict, script)
                output = {}
                return_code = exec_remote_command(server=host.address,
                                                  username=host_csattr.vm_user,
                                                  password=host_csattr.vm_password,
                                                  command=script,
                                                  output=output)

                if return_code != 0:
                    raise Exception(str(output))

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0014)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        try:
            LOG.info("Remove all backup log files")

            backup_log_dict = get_backup_log_configuration_dict(environment=workflow_dict['environment'],
                                                                databaseinfra=workflow_dict['databaseinfra'])
            if backup_log_dict is None:
                return True

            instance = workflow_dict['instances'][0]
            host = instance.hostname
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
