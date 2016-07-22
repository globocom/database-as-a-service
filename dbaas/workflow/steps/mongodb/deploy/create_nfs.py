# -*- coding: utf-8 -*-
import logging
from util import full_stack, get_credentials_for
from dbaas_nfsaas.dbaas_api import DatabaseAsAServiceApi
from dbaas_nfsaas.faas_provider import Provider
from dbaas_nfsaas.models import HostAttr
from dbaas_credentials.models import CredentialType
from ...util.base import BaseStep
from ....exceptions.error_codes import DBAAS_0009

LOG = logging.getLogger(__name__)


class CreateNfs(BaseStep):

    def __unicode__(self):
        return "Requesting NFS export..."

    def _get_faas_provider(self, workflow_dict):
        faas_credentials = get_credentials_for(
            environment=workflow_dict['environment'],
            credential_type=CredentialType.FAAS
        )
        dbaas_api = DatabaseAsAServiceApi(credentials=faas_credentials)
        return Provider(dbaas_api, HostAttr)

    def do(self, workflow_dict):
        try:
            workflow_dict['disks'] = []

            for instance in workflow_dict['instances']:
                host = instance.hostname

                if instance.is_arbiter:
                    LOG.info("Do not create NFS disk for Arbiter...")
                    continue

                LOG.info("Creating nfsaas disk...")
                provider = self._get_faas_provider(workflow_dict)
                disk = provider.create_export(
                    host=host,
                    size_kb=workflow_dict['plan'].disk_offering.size_kb
                )
                workflow_dict['disks'].append(disk)

                LOG.info(
                    "Creating nfsaas access to disk: {}".format(
                        disk.nfsaas_path_host
                    )
                )

                provider.create_access(
                    export_path=disk.nfsaas_path_host, address=host.address
                )

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0009)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        try:
            provider = self._get_faas_provider(workflow_dict)
            for host in workflow_dict['hosts']:
                LOG.info("Destroying NFS export...")
                for disk in HostAttr.objects.filter(host=host):
                    if not provider.delete_export(disk.nfsaas_path_host):
                        return False

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0009)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
