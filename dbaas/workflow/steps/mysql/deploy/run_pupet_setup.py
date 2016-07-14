# -*- coding: utf-8 -*-
import logging
from dbaas_cloudstack.models import HostAttr as CsHostAttr
from util import exec_remote_command
from util import full_stack
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0013

LOG = logging.getLogger(__name__)


class RunPuppetSetup(BaseStep):

    def __unicode__(self):
        return "Running puppet-setup..."

    def do(self, workflow_dict):
        try:

            script = "puppet-setup"
            for host in workflow_dict['hosts']:

                LOG.info("Getting vm credentials...")
                host_csattr = CsHostAttr.objects.get(host=host)

                LOG.info("Run puppet-setup on host {}".format(host))
                output = {}
                return_code = exec_remote_command(server=host.address,
                                                  username=host_csattr.vm_user,
                                                  password=host_csattr.vm_password,
                                                  command=script,
                                                  output=output)
                #if return_code != 0:
                #    raise Exception(str(output))

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0013)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        try:

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0013)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
