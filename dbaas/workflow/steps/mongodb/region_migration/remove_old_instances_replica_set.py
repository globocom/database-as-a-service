# -*- coding: utf-8 -*-
import logging
from util import full_stack
from util import exec_remote_command
from util import build_context_script
from dbaas_cloudstack.models import HostAttr as CS_HostAttr
from ...util.base import BaseStep
from ....exceptions.error_codes import DBAAS_0019

LOG = logging.getLogger(__name__)


class RemoveInstancesReplicaSet(BaseStep):

    def __unicode__(self):
        return "Removing instances from Replica Set..."

    def do(self, workflow_dict):
        try:

            initial_script = '#!/bin/bash\n\ndie_if_error()\n{\n    local err=$?\n    if [ "$err" != "0" ]; then\n        echo "$*"\n        exit $err\n    fi\n}'
            databaseinfra = workflow_dict['databaseinfra']

            connect_string = ""
            for source_instance in workflow_dict['source_instances']:
                target_instance = source_instance.future_instance
                if target_instance.instance_type != target_instance.MONGODB_ARBITER:
                    if connect_string:
                        connect_string += ','
                    connect_string += target_instance.address + \
                        ":" + str(target_instance.port)

            connect_string = databaseinfra.get_driver().get_replica_name() + \
                "/" + connect_string
            connect_string = " --host {} admin -u{} -p{}".format(
                connect_string, databaseinfra.user, databaseinfra.password)
            LOG.debug(connect_string)

            context_dict = {
                'CONNECT_STRING': connect_string,
                'SECUNDARY_ONE': "{}:{}".format(workflow_dict['source_instances'][0].address, workflow_dict['source_instances'][0].port),
                'SECUNDARY_TWO': "{}:{}".format(workflow_dict['source_instances'][1].address, workflow_dict['source_instances'][1].port),
                'ARBITER': "{}:{}".format(workflow_dict['source_instances'][2].address, workflow_dict['source_instances'][2].port),
            }

            script = initial_script
            script += '\necho ""; echo $(date "+%Y-%m-%d %T") "- Removing new database members"'
            script += '\n/usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS'
            script += '\nrs.remove("{{ARBITER}}")'
            script += '\nexit'
            script += '\nEOF_DBAAS'
            script += '\ndie_if_error "Error removing new replica set members"'

            script += '\nsleep 30'
            script += '\necho ""; echo $(date "+%Y-%m-%d %T") "- Removing new database members"'
            script += '\n/usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS'
            script += '\nrs.remove("{{SECUNDARY_TWO}}")'
            script += '\nexit'
            script += '\nEOF_DBAAS'
            script += '\ndie_if_error "Error removing new replica set members"'

            script += '\nsleep 30'
            script += '\necho ""; echo $(date "+%Y-%m-%d %T") "- Removing new database members"'
            script += '\n/usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS'
            script += '\nrs.remove("{{SECUNDARY_ONE}}")'
            script += '\nexit'
            script += '\nEOF_DBAAS'
            script += '\ndie_if_error "Error removing new replica set members"'

            script = build_context_script(context_dict, script)
            output = {}

            host = workflow_dict['source_instances'][0].hostname
            cs_host_attr = CS_HostAttr.objects.get(host=host)
            return_code = exec_remote_command(server=host.address,
                                              username=cs_host_attr.vm_user,
                                              password=cs_host_attr.vm_password,
                                              command=script,
                                              output=output)
            LOG.info(output)
            if return_code != 0:
                raise Exception(str(output))

            for source_instance in workflow_dict['source_instances']:
                source_instance.delete()
                LOG.info("Source instance deleted")

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0019)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0019)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
