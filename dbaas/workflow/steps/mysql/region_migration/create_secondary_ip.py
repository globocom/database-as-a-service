# -*- coding: utf-8 -*-
import logging
from dbaas_credentials.models import CredentialType
from util import get_credentials_for
from util import full_stack
from dbaas_cloudstack.models import HostAttr
from dbaas_cloudstack.models import DatabaseInfraAttr
from dbaas_cloudstack.provider import CloudStackProvider
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0010

LOG = logging.getLogger(__name__)


class CreateSecondaryIp(BaseStep):

    def __unicode__(self):
        return "Allocating secondary ips..."

    def do(self, workflow_dict):
        try:
            if 'target_hosts' not in workflow_dict:
                return False

            if len(workflow_dict['target_hosts']) == 1:
                return True

            cs_credentials = get_credentials_for(
                environment=workflow_dict['target_environment'],
                credential_type=CredentialType.CLOUDSTACK)

            LOG.info("Get credential fot network api...")
            networkapi_credentials = get_credentials_for(
                environment=workflow_dict['target_environment'],
                credential_type=CredentialType.NETWORKAPI)

            cs_provider = CloudStackProvider(credentials=cs_credentials,
                                             networkapi_credentials=networkapi_credentials)
            if not cs_provider:
                raise Exception("Could not create CloudStackProvider object")
                return False

            workflow_dict['target_secondary_ips'] = []

            networkapi_equipment_id = workflow_dict[
                'source_secondary_ips'][0].networkapi_equipment_id

            if not networkapi_equipment_id:
                raise Exception("Could not register networkapi equipment")
                return False

            for index, host in enumerate(workflow_dict['target_hosts']):
                LOG.info("Creating Secondary ips...")
                host_attr = HostAttr.objects.get(host=host)

                reserved_ip = cs_provider.reserve_ip(
                    project_id=cs_credentials.project,
                    vm_id=host_attr.vm_id)
                if not reserved_ip:
                    return False

                databaseinfraattr = DatabaseInfraAttr()
                databaseinfraattr.ip = reserved_ip['secondary_ip']
                if index == 0:
                    databaseinfraattr.is_write = True
                    ip_desc = 'Write IP'
                else:
                    databaseinfraattr.is_write = False
                    ip_desc = 'Read IP'

                networkapi_ip_id = cs_provider.register_networkapi_ip(equipment_id=networkapi_equipment_id,
                                                                      ip=reserved_ip[
                                                                          'secondary_ip'],
                                                                      ip_desc=ip_desc)

                databaseinfraattr.cs_ip_id = reserved_ip['cs_ip_id']
                databaseinfraattr.networkapi_equipment_id = networkapi_equipment_id
                databaseinfraattr.networkapi_ip_id = networkapi_ip_id
                databaseinfraattr.databaseinfra = workflow_dict[
                    'databaseinfra']
                databaseinfraattr.save()

                old_ip = workflow_dict['source_secondary_ips'][index]
                old_ip.equivalent_dbinfraattr = databaseinfraattr
                old_ip.save()

                workflow_dict['target_secondary_ips'].append(databaseinfraattr)

            return True
        except Exception:
            traceback = full_stack()
            workflow_dict['exceptions']['error_codes'].append(DBAAS_0010)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            if 'databaseinfra' not in workflow_dict:
                LOG.info(
                    "We could not find a databaseinfra inside the workflow_dict")
                return False

            source_secondary_ip_ids = [
                secondary_ip.id for secondary_ip in workflow_dict['source_secondary_ips']]

            databaseinfraattr = DatabaseInfraAttr.objects.filter(
                databaseinfra=workflow_dict['databaseinfra'],
                equivalent_dbinfraattr=None).exclude(id__in=source_secondary_ip_ids)

            LOG.info("databaseinfraattr: {}".format(databaseinfraattr))
            LOG.info("old infra ip: {}".format(
                workflow_dict['source_secondary_ips']))

            cs_credentials = get_credentials_for(
                environment=workflow_dict['target_environment'],
                credential_type=CredentialType.CLOUDSTACK)

            networkapi_credentials = get_credentials_for(
                environment=workflow_dict['target_environment'],
                credential_type=CredentialType.NETWORKAPI)

            cs_provider = CloudStackProvider(credentials=cs_credentials,
                                             networkapi_credentials=networkapi_credentials)

            for infra_attr in databaseinfraattr:
                networkapi_equipment_id = infra_attr.networkapi_equipment_id
                networkapi_ip_id = infra_attr.networkapi_ip_id
                if networkapi_ip_id:
                    LOG.info("Removing network api IP for %s" %
                             networkapi_ip_id)
                    if not cs_provider.remove_networkapi_ip(equipment_id=networkapi_equipment_id,
                                                            ip_id=networkapi_ip_id):
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
