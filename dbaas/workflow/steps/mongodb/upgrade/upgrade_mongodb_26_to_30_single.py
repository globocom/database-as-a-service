# -*- coding: utf-8 -*-
import logging
from util import full_stack
from util import exec_remote_command
from util import build_context_script
from dbaas_cloudstack.models import HostAttr as CS_HostAttr
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0023
from workflow.steps.util import test_bash_script_error
from workflow.steps.mongodb import util

LOG = logging.getLogger(__name__)


class UpgradeMongoDB_26_to_30(BaseStep):

    def __unicode__(self):
        return "Upgrade MongoDB 2.6 to 3.0 ..."

    def do(self, workflow_dict):
        try:

            instances = workflow_dict['instances']
            databaseinfra = workflow_dict['databaseinfra']

            connect_string = util.build_mongodb_connect_string(instances=instances,
                                                               databaseinfra=databaseinfra)

            script = test_bash_script_error()
            script += util.build_cp_mongodb_binary_file()
            script += util.build_stop_database_script(clean_data=False)
            script += util.build_change_release_alias_script()
            script += util.build_start_database_script()
            script += util.build_authschemaupgrade_script()
            script += util.build_change_limits_script()
            script += util.build_remove_reprecated_index_counter_metrics()

            context_dict = {
                'SOURCE_PATH': '/mnt/software/db/mongodb',
                'TARGET_PATH': '/usr/local/',
                'MONGODB_RELEASE_FILE': 'mongodb-linux-x86_64-3.0.8.tgz',
                'MONGODB_RELEASE_FOLDER': 'mongodb-linux-x86_64-3.0.8',
                'CONNECT_STRING': connect_string,
            }

            script = build_context_script(context_dict, script)
            output = {}

            host = instances[0].hostname
            cs_host_attr = CS_HostAttr.objects.get(host=host)

            return_code = exec_remote_command(server=host.address,
                                              username=cs_host_attr.vm_user,
                                              password=cs_host_attr.vm_password,
                                              command=script,
                                              output=output)
            LOG.info(output)
            if return_code != 0:
                raise Exception(str(output))

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0023)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        return True
