# -*- coding: utf-8 -*-
from logging import getLogger
from requests import post, delete, get
from time import sleep
from urlparse import urljoin

from django.core.exceptions import ObjectDoesNotExist

from dbaas_credentials.models import CredentialType
from physical.models import Host, Instance, Ip, DatabaseInfra
from maintenance.models import HostMigrate
from util import get_credentials_for
from base import BaseInstanceStep
from vm import WaitingBeReady as WaitingVMBeReady
from workflow.steps.util.vm import HostStatus

LOG = getLogger(__name__)

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


class HostProviderCreateIPException(HostProviderException):
    pass


class HostProviderDestroyIPException(HostProviderException):
    pass


class HostProviderDestroyVMException(HostProviderException):
    pass


class HostProviderListZoneException(HostProviderException):
    pass


class HostProviderInfoException(HostProviderException):
    pass


class HostProviderCreateServiceAccountException(HostProviderException):
    pass


class HostProviderSetRoleServiceAccountException(HostProviderException):
    pass


class HostProviderDestroyServiceAccountException(HostProviderException):
    pass


class HostProviderUpdateLabelsException(HostProviderException):
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

    @property
    def infra_service_account(self):
        infra = DatabaseInfra.objects.get(id=self.infra.id)
        return infra.service_account

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

    def new_version(self, engine=None, host_identifier=None,
                    team_name=None, database_name=None,
                    infra_name=None, service_account=None):
        url = "{}/{}/{}/host/reinstall".format(
            self.credential.endpoint, self.provider, self.environment
        )
        data = {
            "host_id": host_identifier,
            "team_name": team_name,
            "database_name": database_name,
            "group": infra_name,
            "service_account": service_account
        }
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
                    database_name='', host_obj=None, port=None,
                    volume_name=None, init_user=None, init_password=None,
                    static_ip=None):
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
            "database_name": database_name,
            "static_ip_id": static_ip and static_ip.identifier,
            "service_account": self.infra_service_account
        }
        if zone:
            data['zone'] = zone
        if port:
            data['port'] = port
        if volume_name:
            data['volume_name'] = volume_name
        if init_user:
            data['init_user'] = init_user
        if init_password:
            data['init_password'] = init_password

        response = self._request(post, url, json=data, timeout=900)
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
        host.private_key = self.vm_credential.private_key
        host.provider = self.provider
        host.identifier = content["id"]
        host.offering = offering
        host.save()
        return host

    def create_static_ip(self, infra):
        url = "{}/{}/{}/ip/".format(
            self.credential.endpoint, self.provider, self.environment
        )
        data = {
            "engine": self.engine,
            "name": "{}-static-ip".format(self.instance.dns.split(".")[0]),
            "group": infra.name,
        }

        response = self._request(post, url, json=data, timeout=600)
        if not response.ok:
            raise HostProviderCreateIPException(response.content, response)

        content = response.json()
        if content:
            ip = Ip()
            ip.identifier = content['identifier']
            ip.address = content['address']
            ip.instance = self.instance
            ip.save()
            return ip

    def create_static_ip_region(self, infra, zone):
        url = "{}/{}/{}/ip/".format(
            self.credential.endpoint, self.provider, self.environment
        )

        data = {
            "engine": self.engine,
            "name": "{}-static-ip".format(self.get_new_ip(self.instance.dns.split(".")[0], zone)),
            "group": infra.name,
        }

        response = self._request(post, url, json=data, timeout=600)
        if not response.ok:
            raise HostProviderCreateIPException(response.content, response)

        content = response.json()
        if content:
            ip = Ip()
            ip.identifier = content['identifier']
            ip.address = content['address']
            ip.instance = self.instance
            ip.save()
            return ip

    def get_new_ip(self, dns, zone):
        dns = str(dns).split('-')
        dns[1] = str(dns[1]) + (str(zone).replace('-', ''))
        return '-'.join(dns)

    def destroy_static_ip(self, static_ip):
        url = "{}/{}/{}/ip/{}".format(
            self.credential.endpoint, self.provider, self.environment,
            static_ip.identifier
        )

        response = self._request(delete, url, timeout=600)
        if not response.ok:
            raise HostProviderDestroyIPException(response.content, response)

    def prepare(self):
        url = "{}/{}/{}/prepare".format(
            self.credential.endpoint, self.provider, self.environment
        )
        data = {
            "engine": self.engine,
            "name": self.instance.vm_name,
            "group": self.infra.name,
            "ports": [self.instance.port],
        }
        response = self._request(post, url, json=data)
        if response.status_code != 201:
            raise HostProviderException(response.content, response)

    def configure(self, configuration):
        url = "{}/{}/{}/host/configure".format(
            self.credential.endpoint, self.provider, self.environment
        )
        data = {
            "host": self.host.hostname,
            "group": self.infra.name,
            "engine": self.engine,
            "configuration": configuration
        }
        response = self._request(post, url, json=data)
        if response.status_code != 200:
            raise HostProviderChangeOfferingException(
                response.content,
                response
            )
        return True

    def remove_configuration(self):
        url = "{}/{}/{}/host/configure/{}".format(
            self.credential.endpoint, self.provider, self.environment,
            self.host.hostname
        )
        response = self._request(delete, url, timeout=600)
        if not response.ok:
            raise HostProviderDestroyVMException(response.content, response)

    def destroy_host(self, host):
        url = "{}/{}/{}/host/{}".format(
            self.credential.endpoint, self.provider, self.environment,
            host.identifier
        )
        response = self._request(delete, url, timeout=600)
        if not response.ok:
            raise HostProviderDestroyVMException(response.content, response)

    def clean(self):
        url = "{}/{}/{}/clean/{}".format(
            self.credential.endpoint, self.provider, self.environment,
            self.host.hostname,
        )
        response = self._request(delete, url)
        if not response.ok:
            raise HostProviderException(response.content, response)

    def list_zones(self):
        url = "{}/{}/{}/zones".format(
            self.credential.endpoint, self.provider, self.environment
        )
        response = self._request(get, url)
        if not response.ok:
            raise HostProviderListZoneException(response.content, response)
        data = response.json()
        return data['zones']

    def host_info(self, host, refresh=False):
        url = "{}/{}/{}/host/{}/".format(
            self.credential.endpoint, self.provider, self.environment,
            host.identifier
        )
        if refresh:
            url = urljoin(url, "refresh/")
        response = self._request(get, url)
        if not response.ok:
            raise HostProviderInfoException(response.content, response)
        return response.json()

    def status_host(self, host):
        url = "{}/{}/{}/status/{}".format(
            self.credential.endpoint,
            self.provider,
            self.environment,
            host.identifier
        )
        response = self._request(get, url)
        if not response.ok:
            raise HostProviderException(response.content, response)
        return response.json()

    def create_service_account(self, name):

        url = "{}/{}/{}/sa/".format(
            self.credential.endpoint, self.provider, self.environment
        )
        data = {
            "name": name
        }

        response = self._request(post, url, json=data, timeout=600)
        if not response.ok:
            raise HostProviderCreateServiceAccountException(
                response.content, response
            )

        content = response.json()
        if content:
            return content['service_account']
        return None

    def set_roles_service_account(self, sa):
        url = "{}/{}/{}/sa-set-role/{}".format(
            self.credential.endpoint, self.provider,
            self.environment, sa
        )

        response = self._request(post, url, timeout=600)
        if not response.ok:
            raise HostProviderSetRoleServiceAccountException(
                response.content, response
            )

        return True

    def destroy_service_account(self, service_account):
        url = "{}/{}/{}/sa/{}".format(
            self.credential.endpoint, self.provider, self.environment,
            service_account
        )
        response = self._request(delete, url, timeout=600)
        if not response.ok:
            raise HostProviderDestroyServiceAccountException(
                response.content, response
            )

    def update_team_labels(self, host, team_name):
        url = "{}/{}/{}/host/update_labels".format(
            self.credential.endpoint, self.provider, self.environment
        )
        data = {
            "host_id": host.identifier,
            "team_name": team_name
        }

        response = self._request(post, url, json=data, timeout=600)
        if not response.ok:
            raise HostProviderUpdateLabelsException(
                response.content, response
            )

        return True


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
        raise Exception(
            "U must use the new method. run_script of HostSSH class"
        )
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


class UpdateTeamLabelsVmInstances(HostProviderStep):
    def __unicode__(self):
        return "Updating Team Labels in all VM Instances..."

    def do(self):
        updated = self.provider.update_team_labels(self.host, self.team_name)
        if not updated:
            raise EnvironmentError("Error in update Team Labels")


class Stop(HostProviderStep):

    def __unicode__(self):
        return "Stopping VM..."

    def do(self):
        stopped = self.provider.stop()
        if not stopped:
            raise EnvironmentError("Could not stop VM")

    def undo(self):
        Start(self.instance).do()
        WaitingVMBeReady(self.instance).do()


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
        reinstall = self.provider.new_version(
            self.future_engine, self.host.identifier,
            self.team_name, self.database.name,
            self.infra.name, self.infra.service_account)
        if not reinstall:
            raise EnvironmentError('Could not reinstall VM')


class InstallMigrateEngineTemplate(HostProviderStep):

    def __init__(self, instance):
        super(InstallMigrateEngineTemplate, self).__init__(instance)
        self.future_engine = self.plan.migrate_engine_equivalent_plan.engine

    def __unicode__(self):
        return "Installing new engine template to VM..."

    def do(self):
        reinstall = self.provider.new_version(
            self.future_engine, self.host.identifier,
            self.team_name, self.database.name,
            self.infra.name, self.infra.service_account)
        if not reinstall:
            raise EnvironmentError('Could not reinstall VM')


class ReinstallTemplate(HostProviderStep):

    def __unicode__(self):
        return "Reinstalling template to VM..."

    def do(self):
        reinstall = self.provider.new_version(
            self.engine, self.host.identifier,
            self.team_name, self.database.name,
            self.infra.name, self.infra.service_account)
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

    def associate_static_ip_with_instance(self):
        static_ip = self.instance.static_ip
        if static_ip:
            static_ip.instance = self.instance
            static_ip.save()

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
        if self.host_migrate:
            plan = self.plan.get_equivalent_plan_for_env(
                self.environment
            )
        else:
            plan = self.plan
        return plan.weaker_offering

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
                database_name=(self.database.name if self.database
                               else task_manager.name),
                static_ip=self.instance.static_ip
            )
            self.update_databaseinfra_last_vm_created()
        else:
            host = pair.hostname

        self.create_instance(host)
        self.associate_static_ip_with_instance()

    def undo(self):
        try:
            host = self.instance.hostname
        except ObjectDoesNotExist:
            self.delete_instance()
            return

        try:
            self.provider.destroy_host(self.host)
        except HostProviderDestroyVMException as e:
            content, response = e
            if response.status_code == 404:
                LOG.warning('Host {} not found in host-provider'.format(self.host))
            else:
                raise e

        self.delete_instance()
        if host.id:
            host.delete()


class AllocateIP(HostProviderStep):

    def __unicode__(self):
        return "Allocating new ip..."

    def do(self):
        if self.instance.static_ip is None:
            self.provider.create_static_ip(self.infra)

    def undo(self):
        if self.instance.static_ip:
            self.provider.destroy_static_ip(self.instance.static_ip)
            self.instance.static_ip.delete()

class AllocateIPRegionMigrate(HostProviderStep):

    @property
    def zone(self):
        return self.host_migrate.zone

    def __unicode__(self):
        return "Allocating new ip region..."

    def do(self):
        if self.instance.static_ip is None:
            self.provider.create_static_ip_region(self.infra, self.zone)
        self.provider.create_static_ip_region(self.infra, self.zone)

    def undo(self):
        if self.instance.static_ip:
            self.provider.destroy_static_ip(self.instance.static_ip)
            self.instance.static_ip.delete()


class DeallocateIP(HostProviderStep):

    def __unicode__(self):
        return "Deallocating new ip..."

    def do(self):
        AllocateIP(self.instance).undo()

    def undo(self):
        AllocateIP(self.instance).do()


class CreateVirtualMachineRegionMigrate(CreateVirtualMachine):

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
    def static_ip(self):
        return Ip.objects.get(identifier="{}-static-ip".format(self.provider.get_new_ip(self.instance.dns.split(".")[0], self.zone)))

    @property
    def vm_name(self):
        new_name = str(self.host.hostname).split('.')[0].split('-')
        new_name[1] = str(new_name[1]) + str(self.zone).replace('-', '')
        return '-'.join(new_name)

    def do(self):
        if self.host.future_host:
            return

        if self.attempt and self.attempt > 1:
            sleep(240)

        host = self.provider.create_host(
            self.infra, self.offering, self.vm_name,
            self.team, self.zone,
            database_name=self.database.name,
            static_ip=self.static_ip
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
            self.infra, self.offering, self.vm_name,
            self.team, self.zone,
            database_name=self.database.name,
            static_ip=self.instance.static_ip
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
        origin_host = self.instance.hostname

        if not origin_host.future_host:
            return

        self.provider.destroy_host(origin_host)

        for instance in origin_host.instances.all():
            if instance.future_instance:
                instance.delete()
            else:
                instance.hostname = self.host
                instance.address = self.host.address
                instance.save()

        for host_migrate in HostMigrate.objects.filter(host=origin_host):
            host_migrate.host = host_migrate.host.future_host
            host_migrate.save()

        origin_host.delete()

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
        # output = self.execute_script(script)
        output = self.host.ssh.run_script(script)
        disk_size_kb = float(output['stdout'][0])
        disk_size_gb = (disk_size_kb / 1024.0) / 1024.0

        return disk_size_gb

    def __unicode__(self):
        return "Updating Host root volume size..."

    def do(self):
        root_size_gb = self.get_root_volume_size()
        self.host.root_size_gb = round(root_size_gb, 2)
        self.host.save()


class WaitingBeReady(HostProviderStep):

    RETRIES = 30

    def __unicode__(self):
        return "Waiting for host be ready..."

    def do(self):
        sleep(60)
        for attempt in range(self.RETRIES):
            status = self.provider.status_host(self.host)
            if status["host_status"] == "READY":
                self.host.version = status["version_id"]
                self.host.save()
                return
            if attempt == self.RETRIES - 1:
                raise EnvironmentError(
                    'Host {} is not ready'.format(
                        self.host
                    )
                )
            sleep(10)

    def undo(self):
        self.do()


class WaitingNewDeploy(WaitingBeReady):

    def execute(self):
        for attempt in range(self.RETRIES):
            status = self.provider.status_host(self.host)
            if (status["host_status"] == "READY" and
                    self.host.version != status["version_id"]):
                self.host.version = status["version_id"]
                self.host.save()
                return
            if attempt == self.RETRIES - 1:
                raise EnvironmentError(
                    'Host {} is not ready'.format(self.host)
                )
            sleep(10)


class WaitingNewDeployDo(WaitingNewDeploy):

    def do(self):
        self.execute()

    def undo(self):
        pass


class WaitingNewDeployUndo(WaitingNewDeploy):

    def do(self):
        pass

    def undo(self):
        self.execute()


class DestroyVirtualMachineMigrateKeepObject(DestroyVirtualMachineMigrate):

    def __unicode__(self):
        return "Destroy VM from previous zone..."

    @property
    def host_migrating(self):
        return self.host_migrate.host

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
    def vm_name(self):
        return self.host_migrating.hostname.split('.')[0]

    def do(self):
        self.provider.destroy_host(self.host)

    def undo(self):
        self.provider.create_host(
            self.infra, self.host_migrating.offering, self.vm_name,
            self.team, self.host_migrate.zone_origin,
            database_name=self.database.name,
            static_ip=self.instance.static_ip,
            host_obj=self.host
        )
        self.host.save()


class RecreateVirtualMachineMigrate(CreateVirtualMachineMigrate):

    def __unicode__(self):
        return "Recreating virtual machine in new zone..."

    def do(self):
        self.provider.create_host(
            self.infra, self.offering, self.vm_name,
            self.team, self.zone,
            database_name=self.database.name,
            static_ip=self.instance.static_ip,
            host_obj=self.host
        )
        self.host.save()

    def undo(self):
        self.provider.destroy_host(self.host_migrate.host)


class CreateServiceAccount(HostProviderStep):

    def __unicode__(self):
        return "Creating Service Account..."

    @property
    def infra_service_account(self):
        infra = DatabaseInfra.objects.get(id=self.infra.id)
        return infra.service_account

    def do(self):
        if not self.infra_service_account:
            name = self.infra.name
            service_account = self.provider.create_service_account(name)
            self.infra.service_account = service_account
            self.infra.save()

    def undo(self):
        if self.infra_service_account:
            self.provider.destroy_service_account(self.infra_service_account)
            self.infra.service_account = None
            self.infra.save()


class SetServiceAccountRoles(CreateServiceAccount):

    def __unicode__(self):
        return "Set roles in service account..."

    def do(self):
        if self.infra_service_account:
            return self.provider.set_roles_service_account(
                self.infra_service_account
            )

    def undo(self):
        pass


class DestroyIPMigrate(AllocateIP):

    def __unicode__(self):
        return "Destroy IP migrate host..."

    @property
    def environment(self):
        return self.infra.environment

    def do(self):
        if self.instance.static_ip_by_address:
            self.provider.destroy_static_ip(self.instance.static_ip_by_address)
            self.instance.static_ip_by_address.delete()

    def undo(self):
        raise NotImplementedError


class DestroyServiceAccountMigrate(CreateServiceAccount):

    def __unicode__(self):
        return "Detroy SA migrate host..."

    @property
    def environment(self):
        return self.infra.environment

    def do(self):
        pass
        #super(DestroyServiceAccountMigrate, self).undo()

    def undo(self):
        raise NotImplementedError
