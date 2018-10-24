# -*- coding: utf-8 -*-
from time import sleep
from dbaas_credentials.models import CredentialType
from util import exec_remote_command_host, check_ssh, get_credentials_for
from base import BaseInstanceStep

CHANGE_MASTER_ATTEMPS = 30
CHANGE_MASTER_SECONDS = 15


class VmStep(BaseInstanceStep):

    def __init__(self, instance):
        super(VmStep, self).__init__(instance)
        self.driver = self.infra.get_driver()
        self.credentials = None
        self.provider = None

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


class WaitingBeReady(VmStep):

    def __unicode__(self):
        return "Waiting for VM be ready..."

    def do(self):
        host_ready = check_ssh(self.host, wait=5, interval=10)
        if not host_ready:
            raise EnvironmentError('VM is not ready')


class UpdateOSDescription(VmStep):

    def __unicode__(self):
        return "Updating instance OS description..."

    def do(self):
        self.host.update_os_description()


class ChangeMaster(VmStep):

    def __unicode__(self):
        return "Changing master node..."

    def do(self):
        if not self.infra.plan.is_ha:
            return

        master = self.driver.get_master_instance()
        if isinstance(master, list):
            if self.instance not in master:
                return
        elif self.instance != master:
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


class CheckAccessToMaster(VmStep):

    def __unicode__(self):
        return "Checking access to master..."

    @property
    def master(self):
        return self.driver.get_master_for(self.instance).hostname

    @staticmethod
    def check_access(origin, destiny, port):
        if origin == destiny:
            return

        output = {}
        script = "(echo >/dev/tcp/{}/{}) &>/dev/null && exit 0 || exit 1"
        script = script.format(destiny.address, port)
        return_code = exec_remote_command_host(origin, script, output)
        if return_code != 0:
            raise EnvironmentError(
                'Could not connect from {} to {}:{} - Error: {}'.format(
                    origin.address, destiny.address, port, str(output)
                )
            )

    def do(self):
        self.check_access(self.host, self.master, self.driver.default_port)


class CheckAccessFromMaster(CheckAccessToMaster):

    def __unicode__(self):
        return "Checking access from master..."

    def do(self):
        self.check_access(self.master, self.host, self.driver.default_port)
