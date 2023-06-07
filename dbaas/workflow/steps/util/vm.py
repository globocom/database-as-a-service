# -*- coding: utf-8 -*-
import logging
from time import sleep
from dbaas_credentials.models import CredentialType
from util import get_credentials_for
from base import BaseInstanceStep

CHANGE_MASTER_ATTEMPS = 30
CHANGE_MASTER_SECONDS = 15

LOG = logging.getLogger(__name__)


class HostStatus(object):
    @staticmethod
    def is_up(host_obj, attempts=2, wait=5, interval=10):
        return host_obj.ssh.check(
            retries=attempts,
            wait=wait,
            interval=interval
        )


class VmStep(BaseInstanceStep):

    def __init__(self, instance):
        super(VmStep, self).__init__(instance)
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

    @property
    def is_valid(self):
        return not self.instance.temporary

    def __unicode__(self):
        return "Waiting for VM be ready..."

    def do(self):
        if not self.is_valid:
            return
        
        host_ready = self.host.ssh.check(wait=5, interval=10)
        if not host_ready:
            raise EnvironmentError('VM is not ready')


class WaitingBeReadyTemporaryInstance(WaitingBeReady):
    
    @property
    def is_valid(self):
        return self.instance.temporary
    
    def do(self):
        if self.is_valid:
            super(WaitingBeReadyTemporaryInstance, self).do()


class WaitingBeReadyRollback(WaitingBeReady):

    def __unicode__(self):
        return "Waiting for VM be ready if rollback..."

    def do(self):
        pass

    def undo(self):
        super(WaitingBeReadyRollback, self).do()


class UpdateOSDescription(VmStep):

    def __unicode__(self):
        return "Updating instance OS description..."

    def do(self):
        self.host.update_os_description()


class UpdateOSDescriptionTemporaryInstance(UpdateOSDescription):
    
    @property
    def is_valid(self):
        return self.instance.temporary
    
    def do(self):
        if self.is_valid:
            super(UpdateOSDescriptionTemporaryInstance, self).do()


class ChangeMaster(VmStep):

    def __unicode__(self):
        return "Changing master node..."

    @property
    def target_instance(self):
        return self.instance

    @property
    def is_slave(self):
        master = self.driver.get_master_instance()
        if isinstance(master, list):
            if self.target_instance not in master:
                return True
        elif self.target_instance != master:
            return True

        if not self.driver.check_instance_is_master(self.target_instance):
            return True

        return False

    @property
    def is_single_instance(self):
        return not self.infra.plan.is_ha

    @property
    def is_valid(self):
        if self.is_single_instance:
            return False
        if self.is_slave:
            return False
        return True

    def do(self):
        if not self.is_valid:
            return

        error = None
        for _ in range(CHANGE_MASTER_ATTEMPS):
            if self.is_slave:
                return
            try:
                self.driver.check_replication_and_switch(self.target_instance)
            except Exception as e:
                error = e
                sleep(CHANGE_MASTER_SECONDS)
            else:
                return

        raise error
    

class ChangeMasterTemporaryInstance(ChangeMaster):

    @property
    def is_valid(self):
        master_temporary = self.check_master_is_temporary()
        # so executa para  a VM tepmoraria, e se a  Master nao eh temporaria
        if not self.instance.temporary or master_temporary:
            return False

        return True

    def check_master_is_temporary(self, wait_seconds=0):
        LOG.info("Checking master is temporary instance")
        LOG.debug("Willl sleep for %s seconds before checking", wait_seconds)
        sleep(wait_seconds)

        master = self.driver.get_master_instance()
        LOG.info("Master instance is %s", master)
        LOG.info("Master is temporary? %s", master.temporary)

        if master is None or not master.temporary:
            return False

        return True

    def change_master(self):
        error = None

        for _ in range(CHANGE_MASTER_ATTEMPS):
            error = None
            try:
                LOG.info("Trying to change master. Attempt %s", _)
                self.driver.check_replication_and_switch_with_stepdown_time(self.target_instance, stepdown_time=300)
                master_is_temporary = self.check_master_is_temporary(wait_seconds=60)

                if not master_is_temporary:
                    raise Exception('Master is not the temporary instance')

                return
            except Exception as e:
                error = e
                sleep(CHANGE_MASTER_SECONDS)

        if error is not None:
            raise error

    def do(self):
        if not self.is_valid:
            return

        self.change_master()


class ChangeMasterNotTemporaryInstance(ChangeMasterTemporaryInstance):

    @property
    def is_valid(self):
        if not self.instance.temporary:
            return False
        return super(ChangeMasterTemporaryInstance, self).is_valid
    
    def change_master(self):
        error = None

        for _ in range(CHANGE_MASTER_ATTEMPS):
            try:
                self.driver.check_replication_and_switch(self.target_instance)
                if self.check_master_is_temporary(wait_seconds=60):
                    raise Exception('Master is the temporary instance')

                return
            except Exception as e:
                error = e
                sleep(CHANGE_MASTER_SECONDS)

        if error is not None:
            raise error


class ChangeMasterDatabaseMigrate(ChangeMaster):
    @property
    def target_instance(self):
        return self.instance.future_instance


class ChangeMasterRollback(ChangeMaster):
    def __unicode__(self):
        return "Changing master node if rollback..."

    def do(self):
        pass

    def undo(self):
        return super(ChangeMasterRollback, self).do()


class ChangeMasterMigrateRollback(ChangeMasterRollback):
    @property
    def target_instance(self):
        return self.instance.future_instance

    @property
    def is_slave(self):
        master = self.driver.get_master_instance2()
        if isinstance(master, list):
            if self.target_instance not in master:
                return True
        elif self.target_instance != master:
            return True

        if not self.driver.check_instance_is_master(self.target_instance):
            return True

        return False

class ChangeMasterMigrate(ChangeMaster):
    @property
    def is_valid(self):
        is_valid = super(ChangeMasterMigrate, self).is_valid
        return is_valid and self.instance == self.infra.instances.first()



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
        script = "hostname | grep 'localhost.localdomain' | wc -l"
        output = self.host.ssh.run_script(script)

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
            self.host.ssh.run_script(script)


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

        script = "(echo >/dev/tcp/{}/{}) &>/dev/null && exit 0 || exit 1"
        script = script.format(destiny.address, port)
        try:
            origin.ssh.run_script(script)
        except origin.ssh.ScriptFailedException as err:
            raise EnvironmentError(
                'Could not connect from {} to {}:{} - Error: {}'.format(
                    origin.address, destiny.address, port, err
                )
            )

    def do(self):
        self.check_access(self.host, self.master, self.driver.default_port)


class CheckAccessFromMaster(CheckAccessToMaster):

    def __unicode__(self):
        return "Checking access from master..."

    def do(self):
        self.check_access(self.master, self.host, self.instance.port)
