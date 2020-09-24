# -*- coding: utf-8 -*-
from time import sleep
from requests import post, delete, get

from django.core.exceptions import ObjectDoesNotExist

from dbaas_credentials.models import CredentialType
from physical.models import Host, Instance
from util import get_credentials_for, exec_remote_command_host
from base import BaseInstanceStep
from vm import WaitingBeReady
from workflow.steps.util.vm import HostStatus

CHANGE_MASTER_ATTEMPS = 4
CHANGE_MASTER_SECONDS = 15


class HostProviderException(Exception):
    pass


class HostProviderStartVMException(HostProviderException):
    pass


class HostProviderStopVMException(HostProviderException):
    pass


class HostProviderNewVersionException(HostProviderException):
    pass


class HostProviderChangeOfferingException(HostProviderException):
    pass


class HostProviderCreateVMException(HostProviderException):
    pass


class HostProviderDestroyVMException(HostProviderException):
    pass


class HostProviderListZoneException(HostProviderException):
    pass


class HostProviderInfoException(HostProviderException):
    pass


class Provider(BaseInstanceStep):

    def __init__(self, instance, environment):
        self.instance = instance
        self._credential = None
        self._vm_credential = None
        self._environment = environment

    @property
    def infra(self):
        return self.instance.databaseinfra

    @property
    def plan(self):
        return self.infra.plan

    @property
    def environment(self):
        return self._environment

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

    def _request(self, action, url, **kw):
        auth = (self.credential.user, self.credential.password,)
        kw.update(**{'auth': auth} if self.credential.user else {})
        kw['headers'] = self.headers
        return action(url, **kw)

    def start(self):
        url = "{}/{}/{}/host/start".format(
            self.credential.endpoint, self.provider, self.environment
        )
        data = {
            "host_id": self.instance.hostname.identifier
        }
        response = self._request(post, url, json=data)
        if not response.ok:
            raise HostProviderStartVMException(response.content, response)
        return True

    def stop(self):
        url = "{}/{}/{}/host/stop".format(
            self.credential.endpoint, self.provider, self.environment
        )
        data = {
            "host_id": self.instance.hostname.identifier
        }
        response = self._request(post, url, json=data)
        if not response.ok:
            raise HostProviderStopVMException(response.content, response)
        return True

    def new_version(self, engine=None):
        url = "{}/{}/{}/host/reinstall".format(
            self.credential.endpoint, self.provider, self.environment
        )
        data = {"host_id": self.host.identifier}
        data.update(
            **{'engine': engine.full_name_for_host_provider} if engine else {}
        )
        response = self._request(post, url, json=data)
        if response.status_code != 200:
            raise HostProviderNewVersionException(response.content, response)
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
        response = self._request(post, url, json=data)
        if response.status_code != 200:
            raise HostProviderChangeOfferingException(
                response.content,
                response
            )
        return True

    def create_host(self, infra, offering, name, team_name, zone=None,
                    database_name='', host_obj=None, **kw):
        url = "{}/{}/{}/host/new".format(
            self.credential.endpoint, self.provider, self.environment
        )
        data = {
            "engine": self.engine,
            "name": name,
            "cpu": offering.cpus,
            "memory": offering.memory_size_mb,
            "group": infra.name,
            "team_name": team_name,
            "database_name": database_name
        }
        data.update(kw)
        if zone:
            data['zone'] = zone

        response = self._request(post, url, json=data, timeout=600)
        if response.status_code != 201:
            raise HostProviderCreateVMException(response.content, response)

        content = response.json()
        if host_obj is None:
            host = Host()
            host.hostname = content["address"]
        else:
            host = host_obj
        host.address = content["address"]
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
            host.identifier
        )
        response = self._request(delete, url, timeout=600)
        if not response.ok:
            raise HostProviderDestroyVMException(response.content, response)

    def list_zones(self):
        url = "{}/{}/{}/zones".format(
            self.credential.endpoint, self.provider, self.environment
        )
        response = self._request(get, url)
        if not response.ok:
            raise HostProviderListZoneException(response.content, response)
        data = response.json()
        return data['zones']

    def host_info(self, host):
        url = "{}/{}/{}/host/{}".format(
            self.credential.endpoint, self.provider, self.environment,
            host.identifier
        )
        response = self._request(get, url)
        if not response.ok:
            raise HostProviderInfoException(response.content, response)
        return response.json()


class HostProviderStep(BaseInstanceStep):

    def __init__(self, instance=None):
        super(HostProviderStep, self).__init__(instance)
        self.credentials = None
        self._provider = None

    @property
    def provider(self):
        if not self._provider:
            self._provider = Provider(self.instance, self.environment)
        return self._provider

    def execute_script(self, script):
        output = {}
        return_code = exec_remote_command_host(self.host, script, output)
        if return_code != 0:
            error = 'Could not execute script {}: {}'.format(
                return_code, output)
            raise EnvironmentError(error)
        return output

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


class StopIfRunning(Stop):
    def do(self):
        if HostStatus.is_up(self.host):
            super(StopIfRunning, self).do()


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


class InstallMigrateEngineTemplate(HostProviderStep):

    def __init__(self, instance):
        super(InstallMigrateEngineTemplate, self).__init__(instance)
        self.future_engine = self.plan.migrate_engine_equivalent_plan.engine

    def __unicode__(self):
        return "Installing new engine template to VM..."

    def do(self):
        reinstall = self.provider.new_version(self.future_engine)
        if not reinstall:
            raise EnvironmentError('Could not reinstall VM')


class ReinstallTemplate(HostProviderStep):

    def __unicode__(self):
        return "Reinstalling template to VM..."

    def do(self):
        reinstall = self.provider.new_version(self.engine)
        if not reinstall:
            raise EnvironmentError('Could not reinstall VM')


class ChangeOffering(HostProviderStep):

    def __init__(self, instance):
        super(ChangeOffering, self).__init__(instance)
        self.target_offering = self.resize.target_offer

    def __unicode__(self):
        return "Resizing VM..."

    def do(self):
        success = self.provider.new_offering(self.target_offering)
        if not success:
            raise Exception("Could not change offering")

    def undo(self):
        self.target_offering = self.resize.source_offer
        self.do()


class CreateVirtualMachine(HostProviderStep):

    def __unicode__(self):
        return "Creating virtual machine..."

    def create_instance(self, host):
        self.instance.hostname = host
        self.instance.address = host.address
        self.instance.read_only = self.has_database
        self.instance.save()

    def delete_instance(self):
        if self.instance.id:
            self.instance.delete()

    def update_databaseinfra_last_vm_created(self):
        last_vm_created = self.infra.last_vm_created
        last_vm_created += 1
        self.infra.last_vm_created = last_vm_created
        self.infra.save()

    @property
    def vm_name(self):
        return self.instance.vm_name

    @property
    def stronger_offering(self):
        return self.plan.stronger_offering

    @property
    def weaker_offering(self):
        return self.plan.weaker_offering

    @property
    def database_offering(self):
        if self.host_migrate and self.host_migrate.database_migrate:
            return self.host_migrate.database_migrate.offering
        if self.has_database:
            return self.infra.offering
        return self.stronger_offering

    @property
    def offering(self):
        if self.instance.is_database:
            return self.database_offering
        return self.weaker_offering

    @property
    def team(self):
        if self.has_database:
            return self.database.team.name
        elif self.create:
            return self.create.team.name
        elif (self.step_manager
              and hasattr(self.step_manager, 'origin_database')):
            return self.step_manager.origin_database.team.name

    @property
    def zone(self):
        return None

    def do(self):
        task_manager = self.create or self.destroy
        if hasattr(self, 'step_manager') and task_manager is None:
            task_manager = self.step_manager
        try:
            pair = self.infra.instances.get(dns=self.instance.dns)
        except Instance.DoesNotExist:
            host = self.provider.create_host(
                self.infra, self.offering, self.vm_name, self.team, self.zone,
                database_name=self.database.name if self.database else task_manager.name
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
            self.provider.destroy_host(self.host)
        except (Host.DoesNotExist, IndexError):
            pass
        self.delete_instance()
        if host.id:
            host.delete()


class CreateVirtualMachineMigrate(CreateVirtualMachine):

    @property
    def environment(self):
        return self.host_migrate.environment

    @property
    def zone(self):
        return self.host_migrate.zone

    @property
    def host(self):
        return self.instance.hostname

    @property
    def vm_name(self):
        return self.host.hostname.split('.')[0]

    def do(self):
        if self.host.future_host:
            return

        if self.attempt and self.attempt > 1:
            sleep(240)

        host = self.provider.create_host(
            self.infra, self.offering, self.vm_name, self.team, self.zone
        )
        self.host.future_host = host
        self.host.save()

    def undo(self):
        try:
            host = self.instance.hostname.future_host
        except ObjectDoesNotExist:
            return

        if not host:
            return

        try:
            self.provider.destroy_host(self.host.future_host)
        except (Host.DoesNotExist, IndexError):
            pass

        if host.id:
            host.delete()


class DestroyVirtualMachineMigrate(HostProviderStep):

    def __unicode__(self):
        return "Destroying virtual machine..."

    @property
    def environment(self):
        return self.infra.environment

    def do(self):
        host = self.instance.hostname
        if not host.future_host:
            return

        self.provider.destroy_host(host)
        for instance in host.instances.all():
            instance.hostname = self.host
            instance.address = self.host.address
            instance.save()

        migrate = self.host_migrate
        migrate.host = host.future_host
        migrate.save()
        host.delete()

    def undo(self):
        raise NotImplementedError


class UpdateHostRootVolumeSize(HostProviderStep):

    def get_root_volume_size(self):
        """This methods executes a script in the host that returns disk size in
        KB. This size is then converted to GB.
        """
        script = """echo $(($(free | grep Swap | awk '{print $2}')\
        + $(df -l --total | tail -n1 | awk '{print $2}')))
        """
        output = self.execute_script(script)
        disk_size_kb = float(output['stdout'][0])
        disk_size_gb = (disk_size_kb / 1024.0) / 1024.0

        return disk_size_gb

    def __unicode__(self):
        return "Updating Host root volume size..."

    def do(self):
        root_size_gb = self.get_root_volume_size()
        self.host.root_size_gb = round(root_size_gb, 2)
        self.host.save()
