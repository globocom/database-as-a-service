# -*- coding: utf-8 -*-
import logging
from util import full_stack
from dbaas_nfsaas.provider import NfsaasProvider
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0022
from dbaas_nfsaas.models import HostAttr

LOG = logging.getLogger(__name__)


class CreateVolume(BaseStep):

    def __unicode__(self):
        return "Requesting NFS volume..."

    def do(self, workflow_dict):
        try:
            environment = workflow_dict['environment']
            plan = workflow_dict['plan']

            host = workflow_dict['host']
            LOG.info("Creating nfsaas volume...")

            volume = NfsaasProvider(
            ).create_disk(environment=environment,
                          plan=plan,
                          host=host)

            if not volume:
                return False

            volume = HostAttr.objects.get(host=host,
                                          nfsaas_path=volume['path'])

            workflow_dict['volume'] = volume

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0022)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        try:
            environment = workflow_dict['environment']

            if 'volume' in workflow_dict:
                volume = workflow_dict['volume']
                LOG.info("Destroying nfsaas volume...")

                provider = NfsaasProvider()
                provider.revoke_access(environment=environment,
                                       host=volume.host,
                                       export_id=volume.nfsaas_export_id)

                provider.drop_export(environment=environment,
                                     export_id=volume.nfsaas_export_id)

                volume.delete()

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0022)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
