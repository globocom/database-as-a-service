# -*- coding: utf-8 -*-
from time import sleep
from django.core.exceptions import ObjectDoesNotExist
from dbaas_cloudstack.models import HostAttr, PlanAttr
from dbaas_cloudstack.provider import CloudStackProvider
from dbaas_credentials.models import CredentialType
from dbaas_cloudstack.models import LastUsedBundleDatabaseInfra, \
    LastUsedBundle, DatabaseInfraOffering
from physical.models import Environment, Instance
from util import exec_remote_command_host, check_ssh, get_credentials_for
from base import BaseInstanceStep, BaseInstanceStepMigration

CHANGE_MASTER_ATTEMPS = 30
CHANGE_MASTER_SECONDS = 15


class VmStep(BaseInstanceStep):

    @property
    def host_cs(self):
        if not self.host:
            return

        try:
            return HostAttr.objects.get(host=self.host)
        except ObjectDoesNotExist:
            return

    def __init__(self, instance):
        super(VmStep, self).__init__(instance)
        self.driver = self.infra.get_driver()
        self.credentials = None
        self.provider = None

    @property
    def cs_provider(self):
        if not self.provider:
            self.provider = CloudStackProvider(credentials=self.cs_credentials)
        return self.provider

    @property
    def cs_credentials(self):
        if not self.credentials:
            self.credentials = get_credentials_for(
                self.environment, CredentialType.CLOUDSTACK
            )
        return self.credentials

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass


class Stop(VmStep):

    def __unicode__(self):
        return "Stopping VM..."

    def do(self):
        stopped = self.cs_provider.stop_virtual_machine(self.host_cs.vm_id)
        if not stopped:
            raise EnvironmentError("Could not stop VM")

    def undo(self):
        Start(self.instance).do()
        WaitingBeReady(self.instance).do()


class Start(VmStep):

    def __unicode__(self):
        return "Starting VM..."

    def do(self):
        started = self.cs_provider.start_virtual_machine(self.host_cs.vm_id)
        if not started:
            raise EnvironmentError("Could not start VM")

    def undo(self):
        Stop(self.instance).do()


class InstallNewTemplate(VmStep):

    def __init__(self, instance):
        super(InstallNewTemplate, self).__init__(instance)

        target_plan = self.plan.engine_equivalent_plan
        cs_plan = PlanAttr.objects.get(plan=target_plan)
        self.bundle = cs_plan.bundles.first()

    def __unicode__(self):
        return "Installing new template to VM..."

    def do(self):
        reinstall = self.cs_provider.reinstall_new_template(
            self.host_cs.vm_id, self.bundle.templateid
        )
        if not reinstall:
            raise EnvironmentError('Could not reinstall VM')


class ReinstallTemplate(VmStep):

    def __init__(self, instance):
        super(ReinstallTemplate, self).__init__(instance)

        cs_plan = PlanAttr.objects.get(plan=self.plan)
        self.bundle = cs_plan.bundles.first()

    def __unicode__(self):
        return "Reinstalling template to VM..."

    def do(self):
        reinstall = self.cs_provider.reinstall_new_template(
            self.host_cs.vm_id, self.bundle.templateid
        )
        if not reinstall:
            raise EnvironmentError('Could not reinstall VM')


class WaitingBeReady(VmStep):

    def __unicode__(self):
        return "Waiting for VM be ready..."

    def do(self):
        host_ready = check_ssh(self.host, wait=5, interval=10)
        if not host_ready:
            raise EnvironmentError('VM is not ready')


class MigrationWaitingBeReady(WaitingBeReady, BaseInstanceStepMigration):
    pass


class UpdateOSDescription(VmStep):

    def __unicode__(self):
        return "Updating instance OS description..."

    def do(self):
        self.host.update_os_description()


class ChangeOffering(VmStep):

    def __init__(self, instance):
        super(ChangeOffering, self).__init__(instance)

        target_offer = self.resize.target_offer
        self.target_offering_id = target_offer.offering.serviceofferingid

    def __unicode__(self):
        return "Resizing VM..."

    def do(self):
        cloudstack_offering_id = self.cs_provider.get_vm_offering_id(
            vm_id=self.host_cs.vm_id,
            project_id=self.cs_credentials.project
        )

        if cloudstack_offering_id == self.target_offering_id:
            return

        success = self.cs_provider.change_service_for_vm(
            self.host_cs.vm_id, self.target_offering_id
        )
        if not success:
            raise Exception("Could not change offering")

    def undo(self):
        offer = self.resize.source_offer
        self.target_offering_id = offer.offering.serviceofferingid
        self.do()


class ChangeMaster(VmStep):

    def __unicode__(self):
        return "Changing master node..."

    def do(self):
        if not self.infra.plan.is_ha:
            return

        master = self.driver.get_master_instance()
        if type(master) == list and self.instance not in master:
            return

        if self.instance != master:
            return

        if not self.driver.check_instance_is_master(self.instance):
            return

        error = None
        for _ in range(CHANGE_MASTER_ATTEMPS):
            try:
                self.driver.check_replication_and_switch(self.instance)
            except Exception as e:
                error = e
                sleep(CHANGE_MASTER_SECONDS)
            else:
                return

        raise error


class InstanceIsSlave(ChangeMaster):

    def __unicode__(self):
        return "Checking master..."

    def do(self):
        pass

    def undo(self):
        super(InstanceIsSlave, self).do()


class CreateVirtualMachine(VmStep):

    def __init__(self, instance):
        super(CreateVirtualMachine, self).__init__(instance)
        self._vm_credential = None

    def __unicode__(self):
        return "Creating virtualmachine..."

    @property
    def vm_credentials(self):
        if not self._vm_credential:
            self._vm_credential = get_credentials_for(
                self.environment, CredentialType.VM
            )
        return self._vm_credential

    def create_host(self, address):
        from physical.models import Host

        host = Host()
        host.address = address
        host.hostname = host.address
        host.user = self.vm_credentials.user
        host.password = self.vm_credentials.password
        host.offering = self.cs_offering
        host.save()
        return host

    def create_host_attr(self, host, vm_id, bundle):
        from dbaas_cloudstack.models import HostAttr
        host_attr = HostAttr()
        host_attr.vm_id = vm_id
        host_attr.host = host
        host_attr.vm_user = self.vm_credentials.user
        host_attr.vm_password = self.vm_credentials.password
        host_attr.bundle = bundle
        host_attr.save()

    def create_instance(self, host):
        self.instance.hostname = host
        self.instance.address = host.address

        if not self.instance.port:
            self.instance.port = self.driver.get_default_database_port()

        if not self.instance.instance_type:
            self.instance.instance_type = self.driver.get_default_instance_type()

        self.instance.read_only = self.read_only_instance
        self.instance.save()

    def update_databaseinfra_last_vm_created(self):
        last_vm_created = self.infra.last_vm_created
        last_vm_created += 1
        self.infra.last_vm_created = last_vm_created
        self.infra.save()

    def get_next_plan_bundle(self):
        bundles = PlanAttr.objects.get(plan=self.plan).bundles_actives
        return LastUsedBundle.get_next_infra_bundle(self.plan, bundles)

    def get_next_bundle(self):
        return LastUsedBundleDatabaseInfra.get_next_infra_bundle(self.infra)

    def set_last_bundle(self, bundle):
        LastUsedBundleDatabaseInfra.set_last_infra_bundle(self.infra, bundle)

    @property
    def vm_name(self):
        return self.instance.vm_name

    @property
    def cs_offering(self):
        return self.infra.cs_dbinfra_offering.get().offering

    def register_infra_offering(self):
        try:
            DatabaseInfraOffering.objects.get(databaseinfra=self.infra)
        except DatabaseInfraOffering.DoesNotExist:
            DatabaseInfraOffering(
                offering=self.cs_offering,
                databaseinfra=self.infra
            ).save()

    def deploy_vm(self, bundle):
        error, vm = self.cs_provider.deploy_virtual_machine(
            offering=self.cs_offering.serviceofferingid,
            bundle=bundle,
            project_id=self.cs_credentials.project,
            vmname=self.vm_name,
            affinity_group_id=self.cs_credentials.get_parameter_by_name(
                'affinity_group_id'
            ),
        )

        if error:
            raise Exception(error)

        address = vm['virtualmachine'][0]['nic'][0]['ipaddress']
        vm_id = vm['virtualmachine'][0]['id']

        return address, vm_id

    def do(self):
        host = self.host
        if not host:
            self.plan.validate_min_environment_bundles(self.environment)
            if self.infra.instances.count() == 0:
                bundle = self.get_next_plan_bundle()
            else:
                bundle = self.get_next_bundle()
            address, vm_id = self.deploy_vm(bundle=bundle)
            host = self.create_host(address=address)
            self.create_host_attr(host=host, vm_id=vm_id, bundle=bundle)
            self.set_last_bundle(bundle)

        self.create_instance(host=host)
        self.update_databaseinfra_last_vm_created()
        self.register_infra_offering()

    def undo(self):
        if self.host_cs:
            self.cs_provider.destroy_virtual_machine(
                project_id=self.cs_credentials.project,
                environment=self.environment,
                vm_id=self.host_cs.vm_id)

            self.host_cs.delete()

        if self.host:
            self.host.delete()

        if self.instance.id:
            self.instance.delete()

    @property
    def read_only_instance(self):
        return False


class CreateVirtualMachineNewInfra(CreateVirtualMachine):

    @property
    def cs_offering(self):
        plan_attr = PlanAttr.objects.get(plan=self.plan)
        if self.instance.is_database:
            return plan_attr.get_stronger_offering()
        return plan_attr.get_weaker_offering()

    def do(self):
        try:
            pair = self.infra.instances.get(dns=self.instance.dns)
        except Instance.DoesNotExist:
            super(CreateVirtualMachineNewInfra, self).do()
        else:
            self.create_instance(host=pair.hostname)

class CreateVirtualMachineHorizontalElasticity(CreateVirtualMachine):

    @property
    def read_only_instance(self):
        return True


class MigrationCreateNewVM(CreateVirtualMachine):

    @property
    def environment(self):
        environment = super(MigrationCreateNewVM, self).environment
        return environment.migrate_environment

    @property
    def vm_name(self):
        return self.host.hostname.split('.')[0]

    @property
    def cs_offering(self):
        if not self.instance.is_database:
            return PlanAttr.objects.get(plan=self.plan.migrate_plan).get_weaker_offering()

        base = super(MigrationCreateNewVM, self).cs_offering
        return base.equivalent_offering

    def get_next_bundle(self):
        migrate_plan = self.plan.migrate_plan
        bundles = PlanAttr.objects.get(plan=migrate_plan).bundles_actives
        return LastUsedBundle.get_next_infra_bundle(migrate_plan, bundles)

    def do(self):
        if self.host.future_host:
            return

        bundle = self.get_next_bundle()
        address, vm_id = self.deploy_vm(bundle=bundle)
        host = self.create_host(address=address)
        self.create_host_attr(host=host, vm_id=vm_id, bundle=bundle)

        self.host.future_host = host
        self.host.save()

    def undo(self):
        raise NotImplementedError


class ChangeInstanceHost(VmStep):

    def __unicode__(self):
        return "Remove old infra instance..."

    def do(self):
        host = self.host
        new_host = host.future_host
        new_host.future_host = host
        new_host.save()

        for instance in host.instances.all():
            future_instance = instance.future_instance
            future_instance.address = 'None-{}'.format(future_instance.id)
            future_instance.future_instance = instance
            future_instance.save()

            instance.address = new_host.address
            instance.hostname = new_host
            instance.save()

            if self.instance.id == instance.id:
                self.instance.address = instance.address
                self.instance.hostname = instance.hostname

            future_instance.address = host.address
            future_instance.hostname = host
            future_instance.save()


class RemoveHost(VmStep):

    def __unicode__(self):
        return "Destroying virtual machine..."

    def do(self):
        from dbaas_cloudstack.models import HostAttr

        host = self.host.future_host
        host_attr = HostAttr.objects.get(host=host)

        if not self.cs_provider.destroy_virtual_machine(
            project_id=self.cs_credentials.project,
            environment=self.environment,
            vm_id=host_attr.vm_id
        ):
            raise Exception("Could not remove Host - {} {} {}".format(
                self.environment, host_attr.vm_id, self.cs_credentials.project
            ))

        host_attr.delete()
        host.delete()


class RemoveHostMigration(RemoveHost):

    @property
    def environment(self):
        base_env = super(RemoveHostMigration, self).environment
        if not base_env.migrate_environment:
            base_env = Environment.objects.get(migrate_environment=base_env)
        return base_env


class CheckHostName(VmStep):

    def __unicode__(self):
        return "Checking VM hostname..."

    @property
    def is_hostname_valid(self):
        output = {}
        script = "hostname | grep 'localhost.localdomain' | wc -l"
        return_code = exec_remote_command_host(self.host, script, output)
        if return_code != 0:
            raise EnvironmentError(str(output))

        return int(output['stdout'][0]) < 1

    def do(self):
        if not self.is_hostname_valid:
            raise EnvironmentError('Hostname invalid')


class CheckHostNameAndReboot(CheckHostName):

    def __unicode__(self):
        return "Checking VM hostname..."

    def do(self):
        if not self.is_hostname_valid:
            script = '/sbin/reboot -f > /dev/null 2>&1 &'
            exec_remote_command_host(self.host, script)
