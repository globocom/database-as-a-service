# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from time import sleep
from drivers.errors import ReplicationNotRunningError
from logical.models import Database
from util import build_context_script, exec_remote_command_host, check_ssh
from workflow.steps.mongodb.util import build_change_oplogsize_script
from workflow.steps.util.base import BaseInstanceStep
from workflow.steps.util import test_bash_script_error, monit_script
from drivers.errors import ReplicationNotRunningError
from workflow.steps.util.ssl import InfraSSLBaseName


LOG = logging.getLogger(__name__)

CHECK_SECONDS = 10
CHECK_ATTEMPTS = 30


class DatabaseStep(BaseInstanceStep):

    def __init__(self, instance):
        super(DatabaseStep, self).__init__(instance)
        if self.host_migrate:
            self.instance.address = self.host.address

    def __del__(self):
        if self.host_migrate:
            self.instance.address = self.instance.hostname.address

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass

    def run_script(self, script):
        output = {}
        return_code = exec_remote_command_host(
            host=self.host,
            command=script,
            output=output,
            retry=False,
            get_pty=self.driver.get_start_pty_default())
        return return_code, output

    def _execute_init_script(self, command):
        base_host = self.instance.hostname if self.host_migrate else self.host
        script = self.driver.initialization_script_path(base_host)
        script = script.format(option=command)
        script += ' > /dev/null'

        return self.run_script(script)

    def start_database(self):
        return self._execute_init_script('start')

    def stop_database(self):
        return self._execute_init_script('stop')

    def __is_instance_status(self, expected, attempts=None):
        if self.host_migrate and self.instance.hostname.future_host:
            self.instance.address = self.instance.hostname.future_host.address
        for _ in range(attempts or CHECK_ATTEMPTS):
            try:
                status = self.driver.check_status(instance=self.instance)
            except Exception as e:
                LOG.debug('{} is down - {}'.format(self.instance, e))
                status = False

            if status == expected:
                return True
            else:
                sleep(CHECK_SECONDS)
        return False

    def vm_is_up(self, attempts=2, wait=5, interval=10):
        return check_ssh(
            self.host,
            retries=attempts,
            wait=wait,
            interval=interval
        )

    def is_up(self, attempts=None):
        return self.__is_instance_status(True, attempts=attempts)

    def is_down(self, attempts=None):
        return self.__is_instance_status(False, attempts=attempts)

    def _execute_script(self, script_variables, script):
        final_script = build_context_script(
            script_variables, script
        )

        output = {}
        return_code = exec_remote_command_host(self.host, final_script, output)
        if return_code != 0:
            raise EnvironmentError(
                'Could not execute replica script {}: {}'.format(
                    return_code, output
                )
            )

    @property
    def is_valid(self):
        return self.host

    def is_os_process_running(self, process_name):
        script = "ps -ef | grep {} | grep -v grep | wc -l".format(
            process_name
        )

        for _ in range(CHECK_ATTEMPTS):
            output = {}
            return_code = exec_remote_command_host(self.host, script, output)
            if return_code != 0:
                raise Exception(str(output))
            processes = int(output['stdout'][0])
            if processes == 0:
                return False
            LOG.info("{} is running".format(process_name))
            sleep(CHECK_SECONDS)

        return True

    @property
    def root_certificate_file(self):
        return InfraSSLBaseName(self.instance).master_ssl_ca


class Stop(DatabaseStep):

    def __unicode__(self):
        return "Stopping database..."

    @property
    def undo_klass(self):
        return Start

    def do(self):
        if not self.is_valid:
            return

        return_code, output = self.stop_database()
        if return_code != 0 and not self.is_down:
            raise EnvironmentError(
                'Could not stop database {}: {}'.format(return_code, output)
            )

        process_name = self.driver.get_database_process_name()
        if self.is_os_process_running(process_name):
            raise EnvironmentError(
                '{} is running on server'.format(process_name)
            )

    def undo(self):
        self.undo_klass(self.instance).do()


class StopIfRunning(Stop):

    @property
    def is_valid(self):
        is_valid = super(StopIfRunning, self).is_valid
        return is_valid and self.is_up(attempts=3)


class StopWithoutUndo(Stop):
    def undo(self):
        pass


class StopIfRunningAndVMUp(StopIfRunning):

    @property
    def is_valid(self):
        if self.vm_is_up():
            return super(StopIfRunningAndVMUp, self).is_valid
        return False


class Start(DatabaseStep):

    def __unicode__(self):
        return "Starting database..."

    @property
    def undo_klass(self):
        return StopIfRunning

    def do(self):
        if not self.is_valid:
            return

        return_code, output = self.start_database()
        if return_code != 0 and not self.is_up():
            raise EnvironmentError(
                'Could not start database {}: {}'.format(return_code, output)
            )

    def undo(self):
        self.undo_klass(self.instance).do()


class StartRsyslog(DatabaseStep):

    def __unicode__(self):
        return "Starting rsyslog..."

    def _exec_command(self, action):
        script = "/etc/init.d/rsyslog {} > /dev/null".format(action)
        return_code, output = self.run_script(script)
        if return_code != 0:
            raise EnvironmentError(
                'Could not {} rsyslog {}: {}'.format(action, return_code, output)
            )

    def _start(self):
        return self._exec_command('start')

    def _stop(self):
        return self._exec_command('stop')

    def do(self):
        return self._start()

    def undo(self):
        return self._stop()


class StopRsyslog(StartRsyslog):

    def __unicode__(self):
        return "Stopping rsyslog..."

    def do(self):
        self._stop()

    def undo(self):
        self._start()


class OnlyInSentinel(DatabaseStep):

    @property
    def is_valid(self):
        base = super(OnlyInSentinel, self).is_valid
        if not base:
            return False

        if self.host.database_instance():
            return self.instance.is_database

        return True


class StartSentinel(Start, OnlyInSentinel):

    @property
    def undo_klass(self):
        return StopSentinel


class StopSentinel(Stop, OnlyInSentinel):

    @property
    def undo_klass(self):
        return StartSentinel


class StartSlave(DatabaseStep):

    def __unicode__(self):
        return "Starting slave..."

    def do(self):
        if not self.infra.plan.is_ha:
            return

        CheckIsUp(self.instance)
        self.driver.start_slave(instance=self.instance)

    def undo(self):
        StopSlave(self.instance).do()


class StopSlave(DatabaseStep):

    def __unicode__(self):
        return "Stopping slave..."

    def do(self):
        if not self.infra.plan.is_ha:
            return

        CheckIsUp(self.instance)
        self.driver.stop_slave(instance=self.instance)

    def undo(self):
        StartSlave(self.instance).do()


class StopSlaveIfRunning(StopSlave):

    @property
    def is_valid(self):
        return self.is_up(attempts=3)

    def do(self):
        if not self.is_valid:
            return
        super(StopSlaveIfRunning, self).do()


class WaitForReplication(DatabaseStep):

    def __unicode__(self):
        return "Waiting for replication ok..."

    def check_replication_ok(self, instance):
        attempts = 0
        while not self.driver.is_replication_ok(instance):
            if attempts == CHECK_ATTEMPTS:
                return False

            attempts += 1
            LOG.info("Replication is not ok for {} (Attempt {}/{})".format(
                instance, attempts, CHECK_ATTEMPTS
            ))
            sleep(CHECK_SECONDS)

        return True

    def do(self):
        if not self.infra.plan.is_ha:
            return

        not_running = []
        sleep(CHECK_SECONDS)
        for instance in self.driver.get_database_instances():
            try:
                if not self.check_replication_ok(instance):
                    not_running.append(instance)
            except ReplicationNotRunningError:
                not_running.append(instance)

        for instance in not_running:
            self.driver.stop_slave(instance)
            sleep(CHECK_SECONDS)
            self.driver.start_slave(instance)
            sleep(CHECK_SECONDS)
            if not self.check_replication_ok(instance):
                raise ReplicationNotRunningError


class CheckIsUp(DatabaseStep):

    def __unicode__(self):
        return "Checking database is up..."

    def do(self):
        if not self.instance.is_database:
            return

        if not self.is_up():
            raise EnvironmentError('Database is down, should be up')


class CheckIfSwitchMaster(DatabaseStep):
    def __unicode__(self):
        return "Checking if master was switched..."

    def do(self):
        if not self.infra.plan.is_ha:
            return

        master = None
        for _ in range(CHECK_ATTEMPTS):
            master = self.driver.get_master_instance()
            if isinstance(master, list):
                if self.instance not in master:
                    return
            elif master and (master != self.instance):
                return
            sleep(CHECK_SECONDS)

        if master:
            raise EnvironmentError('The instance is still master.')
        else:
            raise EnvironmentError('There is no master for this infra.')


class CheckIfSwitchMasterRollback(CheckIfSwitchMaster):
    def __unicode__(self):
        return "Checking if master was switched if rollback..."

    def do(self):
        pass

    def undo(self):
        return super(CheckIfSwitchMasterRollback, self).do()


class CheckIfSwitchMasterMigrate(CheckIfSwitchMaster):
    @property
    def is_valid(self):
        return self.instance == self.infra.instances.first()

    def do(self):
        if not self.is_valid:
            return
        return super(CheckIfSwitchMasterMigrate, self).do()


class CheckIsUpForResizeLog(CheckIsUp):
    def do(self):
        self.instance.old_port = self.instance.port
        self.instance.port = 27018
        super(CheckIsUpForResizeLog, self).do()
        self.instance.port = self.instance.old_port


class StartForResizeLog(Start):
    def do(self):
        self.instance.old_port = self.instance.port
        self.instance.port = 27018
        LOG.info('Will start database')
        super(StartForResizeLog, self).do()
        self.instance.port = self.instance.old_port


class CheckIsDown(DatabaseStep):

    def __unicode__(self):
        return "Checking database is down..."

    def do(self):
        if not self.instance.is_database:
            return

        if not self.is_down:
            raise EnvironmentError('Database is up, should be down')

        process_name = self.driver.get_database_process_name()
        if self.is_os_process_running(process_name):
            raise EnvironmentError(
                '{} is running on server'.format(process_name)
            )


class CheckIsDownIfVMUp(CheckIsDown):
    def __unicode__(self):
        original_unicode = super(StopIfRunning, self).__unicode__()
        if not self.is_valid:
            return '{}{}'.format(original_unicode, self.skip_msg)
        return original_unicode

    @property
    def is_valid(self):
        return self.vm_is_up()

    def do(self):
        if not self.is_valid:
            return
        super(CheckIsDownIfVMUp, self).do()


class DatabaseChangedParameters(DatabaseStep):

    def __init__(self, instance):
        super(DatabaseChangedParameters, self).__init__(instance)
        from physical.models import DatabaseInfraParameter

        self.reseted_parameters = DatabaseInfraParameter\
            .get_databaseinfra_reseted_parameters(databaseinfra=self.finfra)

        self.changed_parameters = DatabaseInfraParameter\
            .get_databaseinfra_changed_parameters(databaseinfra=self.finfra)


class ChangeDynamicParameters(DatabaseStep):

    def __unicode__(self):
        return "Changing dynamic database parameters..."

    def do(self):
        from physical.models import DatabaseInfraParameter

        changed_parameters = DatabaseInfraParameter\
            .get_databaseinfra_changed_parameters(self.infra)
        for changed_parameter in changed_parameters:
            self.driver.set_configuration(
                instance=self.instance,
                name=changed_parameter.parameter.name,
                value=changed_parameter.value
            )


class SetParameterStatus(DatabaseStep):

    def __unicode__(self):
        return "Setting database parameter status on databaseinfra..."

    def do(self):
        from physical.models import DatabaseInfraParameter

        reseted_parameters = DatabaseInfraParameter\
            .get_databaseinfra_reseted_parameters(self.infra)
        for reseted_parameter in reseted_parameters:
            reseted_parameter.delete()

        changed_parameters = DatabaseInfraParameter\
            .get_databaseinfra_changed_not_reseted_parameters(self.infra)
        for changed_parameter in changed_parameters:
            changed_parameter.applied_on_database = True
            changed_parameter.current_value = changed_parameter.value
            changed_parameter.save()


class ResizeOpLogSize(DatabaseStep):

    def __unicode__(self):
        return "Changing oplog Size..."

    def do(self):
        from physical.models import DatabaseInfraParameter
        self.instance.old_port = self.instance.port
        self.instance.port = 27018
        oplogsize = DatabaseInfraParameter.objects.get(
            databaseinfra=self.infra,
            parameter__name='oplogSize')
        script = build_change_oplogsize_script(
            instance=self.instance, oplogsize=oplogsize.value)
        output = {}
        return_code = exec_remote_command_host(self.host, script, output)
        if return_code != 0:
            raise Exception(str(output))
        self.instance.port = self.instance.old_port


class ResizeOpLogSize40(DatabaseStep):

    def __unicode__(self):
        return "Changing oplog Size..."

    def do(self):
        from physical.models import DatabaseInfraParameter
        oplogsize = DatabaseInfraParameter.objects.get(
            databaseinfra=self.infra,
            parameter__name='oplogSize')
        client = self.driver.get_client(self.instance)
        client.admin.command(
            {'replSetResizeOplog': 1, 'size': int(oplogsize.value)})


class ValidateOplogSizeValue(DatabaseStep):

    def __unicode__(self):
        return "Validating oplog Size value..."

    def do(self):
        from physical.models import DatabaseInfraParameter
        oplog = DatabaseInfraParameter.objects.get(
            databaseinfra=self.infra,
            parameter__name='oplogSize')
        oplogsize = oplog.value
        error = 'BadValue oplogSize {}. Must be integer.'.format(oplogsize)
        try:
            oplogsize = int(oplogsize)
        except ValueError:
            raise EnvironmentError(error)

        if oplogsize < 990:
            error = 'BadValue oplogSize {}. Must be greater than 990.'.format(
                oplogsize)
            raise EnvironmentError(error)


class SetSlave(DatabaseStep):

    def __unicode__(self):
        return "Setting slaves..."

    @property
    def is_valid(self):
        return self.instance.is_database

    @property
    def master(self):
        if self.host_migrate:
            return self.infra.get_driver().get_master_instance(self.instance)
        return self.infra.get_driver().get_master_instance()

    def do(self):
        if not self.is_valid:
            return

        master = self.master
        if master == self.instance:
            return

        client = self.infra.get_driver().get_client(self.instance)
        client.slaveof(master.address, master.port)


class SetSlaveRestore(SetSlave):

    @property
    def master(self):
        return self.restore.master_for(self.instance)


class SetSlaveNewInfra(SetSlave):

    @property
    def is_valid(self):
        base = super(SetSlaveNewInfra, self).is_valid
        if not base:
            return False

        return self.instance != self.infra.instances.first()


class SetSlavesMigration(SetSlave):

    def do(self):
        if not self.instance.is_sentinel:
            return

        instances = list(self.infra.instances.all())
        master = instances.pop(0)
        for instance in instances:
            if not instance.is_database:
                continue

            client = self.infra.get_driver().get_client(instance)
            client.slaveof(master.address, master.port)

class StartMonit(DatabaseStep):
    def __unicode__(self):
        return "Starting monit..."

    def do(self):
        LOG.info("Start monit on host {}".format(self.host))
        script = test_bash_script_error()
        action = 'start'
        script += monit_script(action)

        LOG.info(script)
        output = {}
        return_code = exec_remote_command_host(self.host, script, output)
        LOG.info(output)
        if return_code != 0:
            LOG.error("Error starting monit")
            LOG.error(str(output))

    def undo(self):
        pass


class Create(DatabaseStep):

    def __unicode__(self):
        return "Creating database..."

    def do(self):
        creating = self.create
        if creating.database:
            return

        database = Database.provision(creating.name, self.infra)
        database.team = creating.team
        database.description = creating.description
        database.subscribe_to_email_events = creating.subscribe_to_email_events
        database.is_protected = creating.is_protected

        if creating.project:
            database.project = creating.project

        database.save()

        creating.database = database
        creating.save()

        database.pin_task(self.create.task)

    def undo(self):
        maintenance_task = self.create or self.destroy
        if not maintenance_task.database:
            return

        database = self.database
        if not database.is_in_quarantine:
            LOG.info("Putting Database in quarentine...")
            database.is_in_quarantine = True
            database.quarantine_dt = datetime.now().date()
            database.subscribe_to_email_events = False
            database.is_protected = False
            database.save()

        database.delete()
        LOG.info("Database destroyed....")


class Clone(DatabaseStep):

    def __unicode__(self):
        return "Cloning database..."

    def do(self):
        if self.step_manager.database:
            return

        origin_database = self.step_manager.origin_database
        database = Database.provision(self.step_manager.name, self.infra)
        database.team = origin_database.team
        database.description = origin_database.description
        database.subscribe_to_email_events = (
            origin_database.subscribe_to_email_events
        )
        database.is_protected = origin_database.is_protected

        if origin_database.project:
            database.project = origin_database.project

        database.save()

        self.step_manager.database = database
        self.step_manager.save()

        database.pin_task(self.step_manager.task)

    def undo(self):
        if not self.step_manager.database:
            return

        database = self.database
        if not database.is_in_quarantine:
            LOG.info("Putting Database in quarentine...")
            database.is_in_quarantine = True
            database.quarantine_dt = datetime.now().date()
            database.subscribe_to_email_events = False
            database.is_protected = False
            database.save()

        database.delete()
        LOG.info("Database destroyed....")


class CheckIfInstanceIsMasterRestore(DatabaseStep):
    def __unicode__(self):
        return "Checking if restored instance is master..."

    def do(self):

        if not self.infra.plan.is_ha:
            return

        if not self.restore.is_master(self.instance):
            return

        for _ in range(CHECK_ATTEMPTS):
            master = self.driver.get_master_instance()
            if master and master == self.instance:
                return
            sleep(CHECK_SECONDS)

        raise EnvironmentError('The instance is not master.')


class CreateExtraDNS(DatabaseStep):
    def __unicode__(self):
        return "Creating extra DNS..."

    def do(self):
        pass

    def undo(self):
        from extra_dns.models import ExtraDns
        ExtraDns.objects.filter(database=self.database).delete()


class checkAndFixMySQLReplication(DatabaseStep):
    def __unicode__(self):
        return "Check and fix replication if necessary..."

    def __init__(self, instance):
        super(checkAndFixMySQLReplication, self).__init__(instance)
        self.instances = self.infra.instances.all()

    @property
    def is_valid(self):
        return 'mysql' in self.engine.name.lower() and self.plan.is_ha

    def get_master_instance(self):
        master_instance = self.driver.get_master_instance()
        if not master_instance:
            sleep(CHECK_SECONDS)
        master_instance = self.driver.get_master_instance()
        if not master_instance:
            raise EnvironmentError(
                "There is no master instance. Check FoxHA and database" \
                " read-write instances."
            )
        return master_instance

    def check_replication_is_running(self, instance):
        try:
            self.driver.get_replication_info(instance)
        except ReplicationNotRunningError:
            self.driver.stop_slave(instance)
            sleep(1)
            self.driver.start_slave(instance)
            sleep(1)
            self.driver.get_replication_info(instance)

    def check_replication_delay(self, instance):
        for _ in range(CHECK_ATTEMPTS):
            if self.driver.is_replication_ok(instance):
                return
            sleep(CHECK_SECONDS)
        raise EnvironmentError("Maximum number of attempts check replication")

    def check_heartbeat(self):
        master_instance = self.get_master_instance()
        hb_ok = self.driver.is_heartbeat_replication_ok(master_instance)
        if not hb_ok:
            host = master_instance.hostname
            self.driver.stop_agents(host)
            sleep(1)
            self.driver.start_agents(host)
            sleep(1)
            hb_ok = self.driver.is_heartbeat_replication_ok(master_instance)
            if not hb_ok:
                raise EnvironmentError("Check heartbeat delay.")

    def do(self):
        if not self.is_valid:
            return

        for instance in self.instances:
            self.check_replication_is_running(instance)
        for instance in self.instances:
            self.check_replication_delay(instance)
        self.check_heartbeat()


class checkAndFixMySQLReplicationIfRunning(checkAndFixMySQLReplication):
    def __unicode__(self):
        return "Check and fix replication if necessary if is running..."

    @property
    def is_valid(self):
        valid = super(checkAndFixMySQLReplicationIfRunning, self).is_valid
        return valid and self.is_up(attempts=3)


class checkAndFixMySQLReplicationRollback(checkAndFixMySQLReplication):
    def __unicode__(self):
        return "Check and fix replication if necessary on rollback..."

    def do(self):
        pass

    def undo(self):
        return super(checkAndFixReplicationRollback, self).do()


class StopNonDatabaseInstance(Stop):
    @property
    def is_valid(self):
        return not self.instance.is_database


class StartNonDatabaseInstance(Start):
    @property
    def is_valid(self):
        return not self.instance.is_database

class StartNonDatabaseInstanceRollback(Start):
    @property
    def is_valid(self):
        return not self.instance.is_database

    @property
    def host(self):
        return self.instance.hostname

    def do(self):
        pass

    def undo(self):
        return super(StartNonDatabaseInstanceRollback, self).do()


class StopNonDatabaseInstanceRollback(Stop):
    @property
    def is_valid(self):
        return not self.instance.is_database

    @property
    def host(self):
        return self.instance.hostname

    def do(self):
        pass

    def undo(self):
        return super(StopNonDatabaseInstanceRollback, self).do()