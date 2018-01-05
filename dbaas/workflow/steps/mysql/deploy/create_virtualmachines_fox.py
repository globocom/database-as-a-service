# -*- coding: utf-8 -*-
import logging
from django.core.exceptions import ObjectDoesNotExist
from dbaas_cloudstack.provider import CloudStackProvider
from dbaas_credentials.models import CredentialType
from dbaas_cloudstack.models import (PlanAttr, HostAttr,
                                      LastUsedBundle, LastUsedBundleDatabaseInfra,
                                      DatabaseInfraOffering)

from util import full_stack
from util import get_credentials_for
from physical.models import Host
from physical.models import Instance
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0011


LOG = logging.getLogger(__name__)


class CreateVirtualMachine(BaseStep):

    def __unicode__(self):
        return "Creating virtualmachines..."

    def do(self, workflow_dict):
        try:
            if 'environment' not in workflow_dict or 'plan' not in workflow_dict:
                return False

            cs_credentials = get_credentials_for(
                environment=workflow_dict['environment'],
                credential_type=CredentialType.CLOUDSTACK)

            vm_credentials = get_credentials_for(
                environment=workflow_dict['environment'],
                credential_type=CredentialType.VM)

            cs_provider = CloudStackProvider(credentials=cs_credentials)

            cs_plan_attrs = PlanAttr.objects.get(plan=workflow_dict['plan'])

            workflow_dict['hosts'] = []
            workflow_dict['instances'] = []
            workflow_dict['databaseinfraattr'] = []
            workflow_dict['vms_id'] = []

            workflow_dict['plan'].validate_min_environment_bundles(
                workflow_dict['environment']
            )
            bundles = list(cs_plan_attrs.bundles_actives)

            for index, vm_name in enumerate(workflow_dict['names']['vms']):
                offering = cs_plan_attrs.get_stronger_offering()

                if len(bundles) == 1:
                    bundle = bundles[0]
                else:
                    if index == 0:
                        bundle = LastUsedBundle.get_next_infra_bundle(
                            plan=workflow_dict['plan'], bundles=bundles)
                    else:
                        bundle = LastUsedBundle.get_next_bundle(
                            current_bundle=bundle, bundles=bundles)

                try:
                    DatabaseInfraOffering.objects.get(
                        databaseinfra=workflow_dict['databaseinfra'])
                except ObjectDoesNotExist:
                    LOG.info("Creating databaseInfra Offering...")
                    dbinfra_offering = DatabaseInfraOffering()
                    dbinfra_offering.offering = offering
                    dbinfra_offering.databaseinfra = workflow_dict[
                        'databaseinfra']
                    dbinfra_offering.save()

                LOG.debug(
                    "Deploying new vm on cs with bundle %s and offering %s" % (bundle, offering))

                error, vm = cs_provider.deploy_virtual_machine(
                    offering=offering.serviceofferingid,
                    bundle=bundle,
                    project_id=cs_credentials.project,
                    vmname=vm_name,
                    affinity_group_id=cs_credentials.get_parameter_by_name(
                        'affinity_group_id'),
                )

                if error:
                    raise Exception(error)

                LOG.debug("New virtualmachine: %s" % vm)

                workflow_dict['vms_id'].append(vm['virtualmachine'][0]['id'])

                host = Host()
                host.address = vm['virtualmachine'][0]['nic'][0]['ipaddress']
                host.hostname = host.address
                host.cloud_portal_host = True
                host.save()
                LOG.info("Host created!")

                workflow_dict['hosts'].append(host)

                host_attr = HostAttr()
                host_attr.vm_id = vm['virtualmachine'][0]['id']
                host_attr.vm_user = vm_credentials.user
                host_attr.vm_password = vm_credentials.password
                host_attr.host = host
                host_attr.bundle = bundle
                host_attr.save()
                LOG.info("Host attrs custom attributes created!")

                instance = Instance()
                instance.address = host.address
                instance.port = 3306
                instance.hostname = host
                instance.databaseinfra = workflow_dict['databaseinfra']
                instance.instance_type = Instance.MYSQL
                instance.offering = offering
                instance.save()
                LOG.info("Instance created!")

                workflow_dict['instances'].append(instance)

                databaseinfra = workflow_dict['databaseinfra']
                databaseinfra.last_vm_created += 1
                databaseinfra.save()
                workflow_dict['databaseinfra'] = databaseinfra

                LastUsedBundleDatabaseInfra.set_last_infra_bundle(
                    databaseinfra=databaseinfra, bundle=host_attr.bundle)

                if workflow_dict['qt'] == 1:

                    LOG.info("Updating databaseinfra endpoint...")
                    databaseinfra = workflow_dict['databaseinfra']
                    databaseinfra.endpoint = instance.address + \
                        ":%i" % (instance.port)
                    databaseinfra.save()
                    workflow_dict['databaseinfra'] = databaseinfra

                    return True

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0011)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        LOG.info("Running undo...")
        try:

            cs_credentials = get_credentials_for(
                environment=workflow_dict['environment'],
                credential_type=CredentialType.CLOUDSTACK)

            cs_provider = CloudStackProvider(credentials=cs_credentials)

            instances = workflow_dict['databaseinfra'].instances.all()

            if not instances:

                for vm_id in workflow_dict['vms_id']:
                    cs_provider.destroy_virtual_machine(
                        project_id=cs_credentials.project,
                        environment=workflow_dict['environment'],
                        vm_id=vm_id)

                for host in workflow_dict['hosts']:
                    host_attr = HostAttr.objects.filter(host=host)

                    host.delete()
                    LOG.info("Host deleted!")

                    if host_attr:
                        host_attr[0].delete()
                        LOG.info("HostAttr deleted!")

            for instance in instances:
                host = instance.hostname

                host_attr = HostAttr.objects.get(host=host)

                LOG.info("Destroying virtualmachine %s" % host_attr.vm_id)

                cs_provider.destroy_virtual_machine(
                    project_id=cs_credentials.project,
                    environment=workflow_dict['environment'],
                    vm_id=host_attr.vm_id)

                host_attr.delete()
                LOG.info("HostAttr deleted!")

                instance.delete()
                LOG.info("Instance deleted")

                host.delete()
                LOG.info("Host deleted!")

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0011)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
