# -*- coding: utf-8 -*-
import logging
from util import full_stack
from util import exec_remote_command
from util import build_context_script
from dbaas_cloudstack.models import HostAttr as CS_HostAttr
from ...util.base import BaseStep
from ....exceptions.error_codes import DBAAS_0019

LOG = logging.getLogger(__name__)


class SwitchPrimary(BaseStep):

    def __unicode__(self):
        return "Switching primary instance..."

    def do(self, workflow_dict):
        try:

            initial_script = '#!/bin/bash\n\ndie_if_error()\n{\n    local err=$?\n    if [ "$err" != "0" ]; then\n        echo "$*"\n        exit $err\n    fi\n}'
            databaseinfra = workflow_dict['databaseinfra']

            connect_string = ""
            for source_instance in workflow_dict['source_instances']:
                if source_instance.instance_type != source_instance.MONGODB_ARBITER:
                    if connect_string:
                        connect_string += ','
                    connect_string += source_instance.address + \
                        ":" + str(source_instance.port)

            connect_string = databaseinfra.get_driver().get_replica_name() + \
                "/" + connect_string
            connect_string = " --host {} admin -u{} -p{}".format(
                connect_string, databaseinfra.user, databaseinfra.password)

            context_dict = {
                'CONNECT_STRING': connect_string,
            }

            script = initial_script
            script += '\necho ""; echo $(date "+%Y-%m-%d %T") "- Change priority of members"'
            script += '\n/usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS'
            script += '\nstatus = rs.status()'
            script += '\nvar_secundary_member = 0'
            script += '\nif (status["members"][1].stateStr == "SECONDARY") {var_secundary_member = 1}'
            script += '\ncfg = rs.conf()'
            script += '\ncfg.members[var_secundary_member].priority = 0'
            script += '\ncfg.members[3].priority = 1'
            script += '\ncfg.members[4].priority = 1'
            script += '\nrs.reconfig(cfg)'
            script += '\nexit'
            script += '\nEOF_DBAAS'
            script += '\ndie_if_error "Error changing priority of members"'

            script += '\nsleep 30'
            script += '\necho ""; echo $(date "+%Y-%m-%d %T") "- Switch primary"'
            script += '\n/usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS'
            script += '\nrs.stepDown()'
            script += '\nexit'
            script += '\nEOF_DBAAS'
            script += '\ndie_if_error "Error switching primary"'

            script += '\nsleep 30'
            script += '\necho ""; echo $(date "+%Y-%m-%d %T") "- Change priority of members"'
            script += '\n/usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS'
            script += '\ncfg = rs.conf()'
            script += '\ncfg.members[0].priority = 0'
            script += '\ncfg.members[1].priority = 0'
            script += '\nrs.reconfig(cfg)'
            script += '\nexit'
            script += '\nEOF_DBAAS'
            script += '\ndie_if_error "Error changing priority of members"'

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

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0019)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:

            initial_script = '#!/bin/bash\n\ndie_if_error()\n{\n    local err=$?\n    if [ "$err" != "0" ]; then\n        echo "$*"\n        exit $err\n    fi\n}'
            databaseinfra = workflow_dict['databaseinfra']

            connect_string = ""
            for source_instance in workflow_dict['source_instances']:
                if source_instance.instance_type != source_instance.MONGODB_ARBITER:
                    if connect_string:
                        connect_string += ','
                    connect_string += source_instance.address + \
                        ":" + str(source_instance.port)

            connect_string = databaseinfra.get_driver().get_replica_name() + \
                "/" + connect_string
            connect_string = " --host {} admin -u{} -p{}".format(
                connect_string, databaseinfra.user, databaseinfra.password)
            LOG.debug(connect_string)

            context_dict = {
                'CONNECT_STRING': connect_string,
            }

            script = initial_script
            script += '\necho ""; echo $(date "+%Y-%m-%d %T") "- Change priority of members"'
            script += '\n/usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS'
            script += '\nstatus = rs.status()'
            script += '\nvar_secundary_member = 3'
            script += '\nif (status["members"][4].stateStr == "SECONDARY") {var_secundary_member = 4}'
            script += '\ncfg = rs.conf()'
            script += '\ncfg.members[var_secundary_member].priority = 0'
            script += '\ncfg.members[0].priority = 1'
            script += '\ncfg.members[1].priority = 1'
            script += '\nrs.reconfig(cfg)'
            script += '\nexit'
            script += '\nEOF_DBAAS'
            script += '\ndie_if_error "Error changing priority of members"'

            script += '\nsleep 30'
            script += '\necho ""; echo $(date "+%Y-%m-%d %T") "- Switch primary"'
            script += '\n/usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS'
            script += '\nrs.stepDown()'
            script += '\nexit'
            script += '\nEOF_DBAAS'
            script += '\ndie_if_error "Error switching primary"'

            script += '\nsleep 30'
            script += '\necho ""; echo $(date "+%Y-%m-%d %T") "- Change priority of members"'
            script += '\n/usr/local/mongodb/bin/mongo {{CONNECT_STRING}} <<EOF_DBAAS'
            script += '\ncfg = rs.conf()'
            script += '\ncfg.members[3].priority = 0'
            script += '\ncfg.members[4].priority = 0'
            script += '\nrs.reconfig(cfg)'
            script += '\nexit'
            script += '\nEOF_DBAAS'
            script += '\ndie_if_error "Error changing priority of members"'
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

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0019)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
