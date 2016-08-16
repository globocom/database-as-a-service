# -*- coding: utf-8 -*-
import logging
from util import full_stack
from util import exec_remote_command
from util import build_context_script
from dbaas_cloudstack.models import HostAttr as CS_HostAttr
from dbaas_nfsaas.models import HostAttr as NF_HostAttr
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020
from workflow.steps.util import test_bash_script_error
from workflow.steps.mysql.util import build_permission_script
from workflow.steps.mysql.util import build_mount_snapshot_volume_script
from workflow.steps.mysql.util import build_remove_deprecated_files_script
from workflow.steps.mysql.util import build_start_database_script
from workflow.steps.mysql.util import build_flipper_script
from util import get_credentials_for
from dbaas_credentials.models import CredentialType

LOG = logging.getLogger(__name__)


class RetoreBackupOnTargets(BaseStep):

    def __unicode__(self):
        return "Restoring backup on target hosts..."

    def do(self, workflow_dict):
        try:

            flipper_crdentials = get_credentials_for(workflow_dict['source_environment'],
                                                     CredentialType.FLIPPER)

            flipper_vip = flipper_crdentials.get_parameter_by_name('vip')

            for host in workflow_dict['target_hosts']:
                cs_host_attr = CS_HostAttr.objects.get(host=host)
                source_host = workflow_dict['source_hosts'][0]
                nf_host_attr = NF_HostAttr.objects.get(host=source_host)

                script = test_bash_script_error()
                script += build_mount_snapshot_volume_script()
                script += build_remove_deprecated_files_script()
                script += build_permission_script()
                script += build_start_database_script()
                script += build_flipper_script()

                context_dict = {
                    'EXPORT_PATH': nf_host_attr.nfsaas_path,
                    'SNAPSHOPT_NAME': workflow_dict['snapshot_name'],
                    'VIP_FLIPPER': flipper_vip,
                    'IPWRITE': workflow_dict['target_secondary_ips'][0].ip,
                    'HOST01': workflow_dict['target_hosts'][0],
                    'HOST02': workflow_dict['target_hosts'][1]

                }

                script = build_context_script(context_dict, script)

                output = {}
                LOG.info(script)
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
