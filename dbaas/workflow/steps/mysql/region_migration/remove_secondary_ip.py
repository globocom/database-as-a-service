# -*- coding: utf-8 -*-
import logging
from dbaas_credentials.models import CredentialType
from util import get_credentials_for
from util import full_stack
from dbaas_cloudstack.models import DatabaseInfraAttr
from dbaas_cloudstack.provider import CloudStackProvider
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0010

LOG = logging.getLogger(__name__)


class RemoveSecondaryIp(BaseStep):
    def __unicode__(self):
        return "Removing secondary ips..."

    def do(self, workflow_dict):
        try:
            databaseinfraattr = DatabaseInfraAttr.objects.filter(
                databaseinfra=workflow_dict['databaseinfra'])

            cs_credentials = get_credentials_for(
                environment=workflow_dict['source_environment'],
                credential_type=CredentialType.CLOUDSTACK)

            networkapi_credentials = get_credentials_for(
                environment=workflow_dict['source_environment'],
                credential_type=CredentialType.NETWORKAPI)

            cs_provider = CloudStackProvider(credentials=cs_credentials,
                                             networkapi_credentials=networkapi_credentials)

            for infra_attr in databaseinfraattr:

                networkapi_equipment_id = infra_attr.networkapi_equipment_id
                networkapi_ip_id = infra_attr.networkapi_ip_id
                if networkapi_ip_id:
                    LOG.info("Removing network api IP for %s" % networkapi_ip_id)
                    ip_removed = cs_provider.remove_networkapi_ip(equipment_id=networkapi_equipment_id,
                                                                  ip_id=networkapi_ip_id)
                    if not ip_removed:
                        return False

                LOG.info("Removing secondary_ip for %s" % infra_attr.cs_ip_id)
                if not cs_provider.remove_secondary_ips(infra_attr.cs_ip_id):
                    return False

                LOG.info("Secondary ip deleted!")

                infra_attr.delete()
                LOG.info("Databaseinfraattr deleted!")

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0010)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0010)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
