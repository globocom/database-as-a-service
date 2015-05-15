# -*- coding: utf-8 -*-
import logging
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020
from workflow.steps.mysql.util import get_replication_information_from_file
from workflow.steps.util.restore_snapshot import use_database_initialization_script
from workflow.steps.mysql.util import change_master_to
from util import exec_remote_command
from physical.models import Instance

LOG = logging.getLogger(__name__)


class ChangeMaster(BaseStep):

    def __unicode__(self):
        return "Changing master..."

    def do(self, workflow_dict):
        try:
            databaseinfra = workflow_dict['databaseinfra']
            host = workflow_dict['host']

            master_host = workflow_dict['host']
            master_instance = Instance.objects.get(host=master_host)

            secondary_host = workflow_dict['not_primary_hosts'][0]
            secondary_instance = Instance.objects.get(host=secondary_host)

            master_log_file, master_log_pos = get_replication_information_from_file(host=master_host)

            for host in [master_host, secondary_host]:
                return_code, output = use_database_initialization_script(databaseinfra=databaseinfra,
                                                                         host=host,
                                                                         option='start')

                if return_code != 0:
                    raise Exception(str(output))

            change_master_to(instance=master_instance,
                             master_host=secondary_host.address,
                             bin_log_file=master_log_file,
                             bin_log_position=master_log_pos)

            change_master_to(instance=secondary_instance,
                             master_host=master_host.address,
                             bin_log_file=master_log_file,
                             bin_log_position=master_log_pos)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
