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

            databaseinfra = workflow_dict['databaseinfra']
            instances = workflow_dict['instances']
            driver = databaseinfra.get_driver()

            connect_string = util.build_mongodb_connect_string(instances=instances,
                                                               databaseinfra=databaseinfra)

            arbiter_instance = driver.get_non_database_instances()[0]
            LOG.info('Changing Arbiter binaries {}...'.format(arbiter_instance))
            self.change_instance_binaries(instance=arbiter_instance,
                                          connect_string=connect_string,
                                          run_authschemaupgrade=False)

            secondary_instance = driver.get_slave_instances()[0]
            LOG.info('Changing Secondary binaries {}...'.format(secondary_instance))
            self.change_instance_binaries(instance=secondary_instance,
                                          connect_string=connect_string,
                                          run_authschemaupgrade=False)

            master_instance = driver.get_master_instance()

            LOG.info('Switching Databases')
            driver.check_replication_and_switch(instance=secondary_instance)
            new_secondary = master_instance

            LOG.info('Changing old master binaries {}...'.format(new_secondary))
            self.change_instance_binaries(instance=new_secondary,
                                          connect_string=connect_string,
                                          run_authschemaupgrade=True)

            LOG.info('Switching Databases')
            driver.check_replication_and_switch(instance=new_secondary)

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0023)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        try:
            pass

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0023)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def change_instance_binaries(self, instance, connect_string, run_authschemaupgrade):
        script = test_bash_script_error()
        script += util.build_cp_mongodb_binary_file()
        script += util.build_stop_database_script(clean_data=False)
        script += util.build_change_release_alias_script()
        script += util.build_start_database_script(wait_time=30)
        script += util.build_change_limits_script()
        script += util.build_remove_reprecated_index_counter_metrics()

        if run_authschemaupgrade:
            script += util.build_authschemaupgrade_script()

        context_dict = {
            'SOURCE_PATH': '/mnt/software/db/mongodb',
            'TARGET_PATH': '/usr/local/',
            'MONGODB_RELEASE_FILE': 'mongodb-linux-x86_64-3.0.8.tgz',
            'MONGODB_RELEASE_FOLDER': 'mongodb-linux-x86_64-3.0.8',
            'CONNECT_STRING': connect_string,
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
