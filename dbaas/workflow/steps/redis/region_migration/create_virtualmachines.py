# -*- coding: utf-8 -*-
import logging
from util import get_credentials_for
from util import full_stack
from dbaas_cloudstack.provider import CloudStackProvider
from dbaas_credentials.models import CredentialType
from dbaas_cloudstack.models import PlanAttr
from dbaas_cloudstack.models import HostAttr
from dbaas_cloudstack.models import LastUsedBundle
from physical.models import Host
from physical.models import Instance
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0020

LOG = logging.getLogger(__name__)


class CreateVirtualMachine(BaseStep):

    def __unicode__(self):
        return "Creating virtualmachines..."

    def do(self, workflow_dict):
        try:

            cs_credentials = get_credentials_for(
                environment=workflow_dict['target_environment'],
                credential_type=CredentialType.CLOUDSTACK)

            vm_credentials = get_credentials_for(
                environment=workflow_dict['target_environment'],
                credential_type=CredentialType.VM)

            cs_provider = CloudStackProvider(credentials=cs_credentials)

            target_offering = workflow_dict['target_offering']

            cs_plan_attrs = PlanAttr.objects.get(
                plan=workflow_dict['target_plan'])
            bundles = list(cs_plan_attrs.bundle.all())

            workflow_dict['target_hosts'] = []
            workflow_dict['target_instances'] = []
            source_instances = []

            for index, source_host in enumerate(workflow_dict['source_hosts']):

                sentinel_source_instance = Instance.objects.filter(
                    hostname=source_host, instance_type=Instance.REDIS_SENTINEL)[0]
                if index < 2:
                    redis_source_instance = Instance.objects.filter(
                        hostname=source_host, instance_type=Instance.REDIS)[0]

                vm_name = source_host.hostname.split('.')[0]

                if len(bundles) == 1:
                    bundle = bundles[0]
                else:
                    bundle = LastUsedBundle.get_next_bundle(
                        plan=workflow_dict['target_plan'], bundle=bundles)

                if index == 2:
                    offering = cs_plan_attrs.get_weaker_offering()
                else:
                    offering = target_offering

                vm = cs_provider.deploy_virtual_machine(offering=offering.serviceofferingid,
                                                        bundle=bundle,
                                                        project_id=cs_credentials.project,
                                                        vmname=vm_name,
                                                        affinity_group_id=cs_credentials.get_parameter_by_name(
                                                            'affinity_group_id'),
                                                        )

                if not vm:
                    raise Exception(
                        "CloudStack could not create the virtualmachine")

                host = Host()
                host.address = vm['virtualmachine'][0]['nic'][0]['ipaddress']
                host.hostname = host.address
                host.save()
                workflow_dict['target_hosts'].append(host)

                source_host.future_host = host
                source_host.save()

                host_attr = HostAttr()
                host_attr.vm_id = vm['virtualmachine'][0]['id']
                host_attr.vm_user = vm_credentials.user
                host_attr.vm_password = vm_credentials.password
                host_attr.host = host
                host_attr.save()
                LOG.info("Host attrs custom attributes created!")

                if index < 2:

                    redis_instance = Instance()
                    redis_instance.address = host.address
                    redis_instance.dns = host.address
                    redis_instance.port = redis_source_instance.port

                    redis_instance.is_active = redis_source_instance.is_active
                    redis_instance.is_arbiter = redis_source_instance.is_arbiter
                    redis_instance.instance_type = redis_source_instance.instance_type
                    redis_instance.hostname = host

                    redis_instance.databaseinfra = workflow_dict[
                        'databaseinfra']
                    redis_instance.save()
                    LOG.info("Instance created!")

                    redis_source_instance.future_instance = redis_instance
                    redis_source_instance.save()

                    source_instances.append(redis_source_instance)

                    workflow_dict['target_instances'].append(redis_instance)

                sentinel_instance = Instance()
                sentinel_instance.address = host.address
                sentinel_instance.dns = host.address
                sentinel_instance.port = sentinel_source_instance.port

                sentinel_instance.is_active = sentinel_source_instance.is_active
                sentinel_instance.is_arbiter = sentinel_source_instance.is_arbiter
                sentinel_instance.instance_type = sentinel_source_instance.instance_type
                sentinel_instance.hostname = host

                sentinel_instance.databaseinfra = workflow_dict[
                    'databaseinfra']
                sentinel_instance.save()
                LOG.info("Instance created!")

                sentinel_source_instance.future_instance = sentinel_instance
                sentinel_source_instance.save()

                source_instances.append(sentinel_source_instance)

                workflow_dict['target_instances'].append(sentinel_instance)

            workflow_dict['source_instances'] = source_instances

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:
            cs_credentials = get_credentials_for(
                environment=workflow_dict['target_environment'],
                credential_type=CredentialType.CLOUDSTACK)

            cs_provider = CloudStackProvider(credentials=cs_credentials)

            for source_instance in workflow_dict['source_instances']:
                source_instance.future_instance = None
                source_instance.save()
                LOG.info("Source instance updated")

            for target_instance in workflow_dict['target_instances']:
                target_instance.delete()
                LOG.info("Target instance deleted")

            for source_host in workflow_dict['source_hosts']:
                source_host.future_host = None
                source_host.save()
                LOG.info("Source host updated")

            for target_host in workflow_dict['target_hosts']:
                host_attr = HostAttr.objects.get(host=target_host)
                LOG.info("Destroying virtualmachine %s" % host_attr.vm_id)

                cs_provider.destroy_virtual_machine(
                    project_id=cs_credentials.project,
                    environment=workflow_dict['target_environment'],
                    vm_id=host_attr.vm_id)

                host_attr.delete()
                LOG.info("HostAttr deleted!")

                target_host.delete()
                LOG.info("Target host deleted")

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0020)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
