# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from requests import post
from dbaas_credentials.models import CredentialType
from physical.models import Host
from util import check_ssh, get_credentials_for
from base import BaseInstanceStep


CHANGE_MASTER_ATTEMPS = 4
CHANGE_MASTER_SECONDS = 15


class Provider(object):

    def __init__(self, instance):
        self.instance = instance
        self._credential = None
        self._vm_credential = None

    @property
    def environment(self):
        return self.instance.databaseinfra.environment

    @property
    def engine(self):
        return str(self.instance.databaseinfra.engine).replace(".", "_")

    @property
    def credential(self):
        # TODO Remove hard coded "Cloudstack"
        if not self._credential:
            self._credential = get_credentials_for(
                self.environment, CredentialType.HOST_PROVIDER,
                project="cloudstack"
            )

        return self._credential

    @property
    def vm_credential(self):
        # TODO Lembrar de colocar o project pra quando tiver um provider
        # diferente
        if not self._vm_credential:
            self._vm_credential = get_credentials_for(
                self.environment, CredentialType.VM,
            )

        return self._vm_credential

    @property
    def provider(self):
        return self.credential.project

    def start(self):
        pass

    def stop(self):
        pass

    def new_version(self, engine):
        pass

    def new_offering(self, offering):
        pass

    def create_host(self, infra, offering, name):
        url = "{}/{}/{}/host/new".format(
            self.credential.endpoint, self.provider, self.environment
        )
        data = {
            "engine": self.engine,
            "name": name,
            "cpu": offering.cpus,
            "memory": offering.memory_size_mb,
            "group": infra.name
        }

        response = post(url, json=data)
        if response.status_code != 201:
            raise IndexError(response.content, response)

        content = response.json()

        host = Host()
        host.address = content["ip"]
        host.hostname = host.address
        host.user = self.credential.user
        host.password = self.credential.password
        host.provider = self.provider
        host.identifier = content["id"]
        host.save()

        return host

    def destroy_host(self, host):
        pass


class HostProviderStep(BaseInstanceStep):

    def __init__(self, instance):
        super(HostProviderStep, self).__init__(instance)
        self.driver = self.infra.get_driver()
        self.credentials = None
        self._provider = None

    @property
    def provider(self):
        if not self._provider:
            self._provider = Provider(self.instance)
        return self._provider

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass


class Stop(HostProviderStep):

    def __unicode__(self):
        return "Stopping VM..."

    def do(self):
        stopped = self.provider.stop()
        if not stopped:
            raise EnvironmentError("Could not stop VM")

    def undo(self):
        Start(self.instance).do()
        WaitingBeReady(self.instance).do()


class Start(HostProviderStep):

    def __unicode__(self):
        return "Starting VM..."

    def do(self):
        started = self.provider.start()
        if not started:
            raise EnvironmentError("Could not start VM")

    def undo(self):
        Stop(self.instance).do()


class InstallNewTemplate(HostProviderStep):

    def __init__(self, instance):
        super(InstallNewTemplate, self).__init__(instance)
        self.future_engine = self.plan.engine_equivalent_plan.engine

    def __unicode__(self):
        return "Installing new template to VM..."

    def do(self):
        reinstall = self.provider.new_version(self.future_engine)
        if not reinstall:
            raise EnvironmentError('Could not reinstall VM')


class ReinstallTemplate(HostProviderStep):

    def __init__(self, instance):
        super(ReinstallTemplate, self).__init__(instance)
        self.future_engine = self.plan.engine

    def __unicode__(self):
        return "Reinstalling template to VM..."

    def do(self):
        reinstall = self.provider.new_version(self.future_engine)
        if not reinstall:
            raise EnvironmentError('Could not reinstall VM')


class WaitingBeReady(HostProviderStep):

    def __unicode__(self):
        return "Waiting for VM be ready..."

    def do(self):
        host_ready = check_ssh(self.host, wait=5, interval=10)
        if not host_ready:
            raise EnvironmentError('VM is not ready')


class ChangeOffering(HostProviderStep):

    def __init__(self, instance):
        super(ChangeOffering, self).__init__(instance)

        target_offer = self.resize.target_offer
        self.target_offering_id = target_offer.offering.serviceofferingid

    def __unicode__(self):
        return "Resizing VM..."

    def do(self):
        success = self.provider.new_offering(offering)
        if not success:
            raise Exception("Could not change offering")

    def undo(self):
        offer = self.resize.source_offer
        self.target_offering_id = offer.offering.serviceofferingid
        self.do()


class CreateVirtualMachine(HostProviderStep):

    def __unicode__(self):
        return "Creating virtualmachine..."

    def create_instance(self, host):
        self.instance.hostname = host
        self.instance.address = host.address
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

    @property
    def vm_name(self):
        return self.instance.vm_name

    def do(self):
        host = self.provider.create_host(self.infra, self.vm_name, offering)

        self.create_instance(host)
        self.update_databaseinfra_last_vm_created()

    def undo(self):
        try:
            host = self.instance.hostname
        except ObjectDoesNotExist:
            return

        self.provider.destroy_host(host)
        self.instance.delete()
        host.delete()
