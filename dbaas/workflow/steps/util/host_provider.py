# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from requests import post, delete
from dbaas_credentials.models import CredentialType
from physical.models import Host, Instance
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
    def infra(self):
        return self.instance.databaseinfra

    @property
    def plan(self):
        return self.infra.plan

    @property
    def environment(self):
        return self.infra.environment

    @property
    def host(self):
        return self.instance.hostname

    @property
    def engine(self):
        return self.infra.engine.full_name_for_host_provider

    @property
    def credential(self):
        if not self._credential:
            self._credential = get_credentials_for(
                self.environment, CredentialType.HOST_PROVIDER
            )

        return self._credential

    @property
    def vm_credential(self):
        if not self._vm_credential:
            self._vm_credential = get_credentials_for(
                self.environment, CredentialType.VM,
            )

        return self._vm_credential

    @property
    def provider(self):
        return self.credential.project

    def post(self, url, **kw):
        auth = (self.credential.user, self.credential.password,)
        kw.update(**{'auth': auth} if self.credential.user else {})
        return post(url, **kw)

    def start(self):
        url = "{}/{}/{}/host/start".format(
            self.credential.endpoint, self.provider, self.environment
        )
        data = {
            "host_id": self.instance.hostname.identifier
        }

        response = self.post(url, json=data)
        if not response.ok:
            raise IndexError(response.content, response)

        return True

    def stop(self):
        url = "{}/{}/{}/host/stop".format(
            self.credential.endpoint, self.provider, self.environment
        )
        data = {
            "host_id": self.instance.hostname.identifier
        }

        response = self.post(url, json=data)
        if not response.ok:
            raise IndexError(response.content, response)

        return True

    def new_version(self, engine=None):
        url = "{}/{}/{}/host/reinstall".format(
            self.credential.endpoint, self.provider, self.environment
        )
        data = {"host_id": self.host.identifier}
        data.update(
            **{'engine': engine.full_name_for_host_provider} if engine else {}
        )

        response = self.post(url, json=data)
        if response.status_code != 200:
            raise IndexError(response.content, response)

        return True

    def new_offering(self, offering):
        url = "{}/{}/{}/host/resize".format(
            self.credential.endpoint, self.provider, self.environment
        )

        data = {
            "host_id": self.host.identifier,
            "cpus": offering.cpus,
            'memory': offering.memory_size_mb
        }

        response = self.post(url, json=data)
        if response.status_code != 200:
            raise IndexError(response.content, response)

        return True

    def create_host(self, infra, offering, name, team_name):
        url = "{}/{}/{}/host/new".format(
            self.credential.endpoint, self.provider, self.environment
        )
        data = {
            "engine": self.engine,
            "name": name,
            "cpu": offering.cpus,
            "memory": offering.memory_size_mb,
            "group": infra.name,
            "team_name": team_name
        }

        response = self.post(url, json=data, timeout=600)
        if response.status_code != 201:
            raise IndexError(response.content, response)

        content = response.json()

        host = Host()
        host.address = content["address"]
        host.hostname = host.address
        host.user = self.vm_credential.user
        host.password = self.vm_credential.password
        host.provider = self.provider
        host.identifier = content["id"]
        host.offering = offering
        host.save()

        return host

    def destroy_host(self, host):
        url = "{}/{}/{}/host/{}".format(
            self.credential.endpoint, self.provider, self.environment,
            self.instance.hostname.identifier
        )

        response = delete(url)
        if not response.ok:
            raise IndexError(response.content, response)


class HostProviderStep(BaseInstanceStep):

    def __init__(self, instance=None):
        super(HostProviderStep, self).__init__(instance)
        self.driver = self.instance and self.infra.get_driver()
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

    def __unicode__(self):
        return "Reinstalling template to VM..."

    def do(self):
        reinstall = self.provider.new_version()
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

        self.target_offering = self.resize.target_offer

#    def get_offering_id(self, offering):
#        host_provider_cli = HostProviderClient(self.infra.environment)
#        return host_provider_cli.get_offering_id(
#            offering.cpus, offering.memory
#        )
#
    def __unicode__(self):
        return "Resizing VM..."

    def do(self):
        success = self.provider.new_offering(self.target_offering)
        if not success:
            raise Exception("Could not change offering")

    def undo(self):
        self.target_offering = self.resize.source_offer
        # self.target_offering_id = self.get_offering_id(self.resize.source_offer)
        self.do()


class CreateVirtualMachine(HostProviderStep):

    def __unicode__(self):
        return "Creating virtualmachine..."

    def create_instance(self, host):
        self.instance.hostname = host
        self.instance.address = host.address
        self.instance.read_only = self.is_readonly_instance
        self.instance.save()

    def delete_instance(self):
        if self.instance.id:
            self.instance.delete()

    def update_databaseinfra_last_vm_created(self):
        last_vm_created = self.infra.last_vm_created
        last_vm_created += 1
        self.infra.last_vm_created = last_vm_created
        self.infra.save()

    def delete_instance(self):
        if self.instance.id:
            self.instance.delete()

    @property
    def is_readonly_instance(self):
        return bool(self.database)

    @property
    def is_readonly_instance(self):
        return bool(self.database)

    @property
    def vm_name(self):
        return self.instance.vm_name

    @property
    def stronger_offering(self):
        return self.plan.stronger_offering

    @property
    def weaker_offering(self):
        return self.plan.weaker_offering

    def do(self):
        if self.instance.is_database:
            offering = (self.infra.offering if self.is_readonly_instance
                        else self.stronger_offering)
        else:
            offering = self.weaker_offering

        try:
            pair = self.infra.instances.get(dns=self.instance.dns)
        except Instance.DoesNotExist:
            host = self.provider.create_host(
                self.infra, offering,
                self.vm_name,
                self.create.team.name
            )
            self.update_databaseinfra_last_vm_created()
        else:
            host = pair.hostname

        self.create_instance(host)

    def undo(self):
        try:
            host = self.instance.hostname
        except ObjectDoesNotExist:
            self.delete_instance()
            return

        try:
            self.provider.destroy_host(
                Host.objects.get(id=host.id)
            )
        except (Host.DoesNotExist, IndexError):
            pass
        self.delete_instance()
        if host.id:
            host.delete()
