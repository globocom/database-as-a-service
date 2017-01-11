# -*- coding: utf-8 -*-
import logging
from util import full_stack
from util import exec_remote_command
from util import build_context_script
from dbaas_cloudstack.models import HostAttr as CS_HostAttr
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0023
from workflow.steps.util import test_bash_script_error
from workflow.steps.mongodb.util import build_change_mongodb_conf_file_script
from workflow.steps.mongodb.util import build_start_database_script
from workflow.steps.mongodb.util import build_stop_database_script
from workflow.steps.mongodb.util import build_clean_data_data_script
from workflow.steps.mongodb.util import build_wait_admin_be_created_script


LOG = logging.getLogger(__name__)


class ChangeMongoDBStorageEngine(BaseStep):

    def __unicode__(self):
        return "Changing Storage Engine to wiredTiger ..."

    def do(self, workflow_dict):
        try:

            databaseinfra = workflow_dict['databaseinfra']
            driver = databaseinfra.get_driver()

            secondary_instance = driver.get_slave_instances()[0]
            LOG.info('Changing Secondary binaries {}...'.format(secondary_instance))
            self.change_instance_binaries(instance=secondary_instance)

            master_instance = driver.get_master_instance()

            LOG.info('Switching Databases')
            driver.check_replication_and_switch(instance=secondary_instance,
                                                attempts=10000)
            new_secondary = master_instance

            LOG.info('Changing old master binaries {}...'.format(new_secondary))
            self.change_instance_binaries(instance=new_secondary)

            LOG.info('Switching Databases')
            driver.check_replication_and_switch(instance=new_secondary,
                                                attempts=10000)

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0023)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        return True

    def change_instance_binaries(self, instance):

        script = test_bash_script_error()
        script += build_change_mongodb_conf_file_script()
        script += build_stop_database_script(clean_data=False)
        script += build_clean_data_data_script()
        script += build_start_database_script()
        script += build_wait_admin_be_created_script()

        context_dict = {
        }

        script = build_context_script(context_dict, script)
        output = {}

        host = instance.hostname
        cs_host_attr = CS_HostAttr.objects.get(host=host)

        return_code = exec_remote_command(server=host.address,
                                          username=cs_host_attr.vm_user,
                                          password=cs_host_attr.vm_password,
                                          command=script,
                                          output=output)
        LOG.info(output)
        if return_code != 0:
            raise Exception(str(output))
