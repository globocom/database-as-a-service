# -*- coding: utf-8 -*-
import logging
from util import full_stack, get_credentials_for, exec_remote_command_host
from dbaas_foreman import get_foreman_provider
from dbaas_credentials.models import CredentialType
from ...util.base import BaseStep
from ....exceptions.error_codes import DBAAS_0007

LOG = logging.getLogger(__name__)


class ConfigVMsForeman(BaseStep):

    def __unicode__(self):
        return "Configuring VMs on Foreman..."

    def do(self, workflow_dict):
        try:

            databaseinfra = workflow_dict['databaseinfra']
            environment = workflow_dict['environment']
            credentials = get_credentials_for(environment=environment,
                                              credential_type=CredentialType.FOREMAN)
            forman_provider = get_foreman_provider(databaseinfra=databaseinfra,
                                                   credentials=credentials)

            vip = workflow_dict['vip']

            for host in workflow_dict['hosts']:
                LOG.info('Get fqdn for host {}'.format(host))
                script = 'hostname'
                output = {}
                return_code = exec_remote_command_host(host, script, output)
                LOG.info(output)
                if return_code != 0:
                    raise Exception(str(output))
                fqdn = output['stdout'][0].strip()

                if fqdn == "localhost.localdomain":
                    errormsg = "The fqdn {} is not valid.".format(fqdn)
                    LOG.error(errormsg)
                    raise Exception(errormsg)

                LOG.info("Call foreman for fqdn={}, vip={}, dsrc={}".format(fqdn, vip.vip_ip, vip.dscp))
                forman_provider.setup_database_dscp(fqdn=fqdn,
                                                    vip_ip=vip.vip_ip,
                                                    dsrc=vip.dscp,
                                                    port=3306)

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0007)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        try:
            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0007)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
