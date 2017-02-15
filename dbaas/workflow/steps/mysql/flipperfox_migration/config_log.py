# -*- coding: utf-8 -*-
import logging
from util import full_stack
from util import exec_remote_command
from dbaas_cloudstack.models import HostAttr as CS_HostAttr
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020

LOG = logging.getLogger(__name__)


class ConfigLog(BaseStep):

    def __unicode__(self):
        return "Configuring rsyslog..."

    def do(self, workflow_dict):
        try:
            for source_host in workflow_dict['source_hosts']:
                future_host = source_host.future_host
                cs_host_attr = CS_HostAttr.objects.get(host=future_host)

                LOG.info("Configuring rsyslog {}".format(future_host))

                script = self.rsyslog_create_config(workflow_dict['database'])
                LOG.info(script)

                output = {}
                return_code = exec_remote_command(
                    server=future_host.address,
                    username=cs_host_attr.vm_user,
                    password=cs_host_attr.vm_password,
                    command=script,
                    output=output
                )
                LOG.info(output)
                if return_code != 0:
                    error_msg = "Error configuring rsyslog: {}".format(str(output))
                    LOG.error(error_msg)
                    raise EnvironmentError(error_msg)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            for source_host in workflow_dict['source_hosts']:
                future_host = source_host.future_host
                cs_host_attr = CS_HostAttr.objects.get(host=future_host)

                LOG.info("Removing rsyslog config in {}".format(future_host))

                script = self.rsyslog_remove_config()
                LOG.info(script)

                output = {}
                return_code = exec_remote_command(
                    server=future_host.address,
                    username=cs_host_attr.vm_user,
                    password=cs_host_attr.vm_password,
                    command=script,
                    output=output
                )
                LOG.info(output)
                if return_code != 0:
                    error_msg = "Error removing configuring rsyslog: {}".format(str(output))
                    LOG.error(error_msg)
                    raise EnvironmentError(error_msg)

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def rsyslog_create_config(self, database):
        return \
            ' echo "\$EscapeControlCharactersOnReceive off" >> /etc/rsyslog.d/dbaaslog.conf &&' \
            ' sed -i "\$a \$template db-log, \\\"<%PRI%>%TIMESTAMP% %HOSTNAME% %syslogtag%%msg%   tags: INFRA,DBAAS,MYSQL,{}\\\"" /etc/rsyslog.d/dbaaslog.conf &&' \
            ' sed -i "\$a*.*                    @logging.udp.globoi.com:5140; db-log" /etc/rsyslog.d/dbaaslog.conf &&' \
            ' /etc/init.d/rsyslog restart'.format(database.name)

    def rsyslog_remove_config(self):
        return 'rm -f /etc/rsyslog.d/dbaaslog.conf'
