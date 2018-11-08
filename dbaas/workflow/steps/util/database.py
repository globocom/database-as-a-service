# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from time import sleep
from drivers.errors import ReplicationNotRunningError
from logical.models import Database
from util import build_context_script, exec_remote_command_host
from workflow.steps.mongodb.util import build_change_oplogsize_script
from workflow.steps.util.base import BaseInstanceStep
from workflow.steps.util import test_bash_script_error, monit_script

LOG = logging.getLogger(__name__)

CHECK_SECONDS = 10
CHECK_ATTEMPTS = 30


class DatabaseStep(BaseInstanceStep):

    def __init__(self, instance):
        super(DatabaseStep, self).__init__(instance)
        self.driver = self.infra.get_driver()
        if self.host_migrate:
            self.instance.address = self.host.address

    def __del__(self):
        if self.host_migrate:
            self.instance.address = self.instance.hostname.address

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass

    def _execute_init_script(self, command):
        base_host = self.instance.hostname if self.host_migrate else self.host
        script = self.driver.initialization_script_path(base_host)
        script = script.format(option=command)
        script += ' > /dev/null'

        output = {}
        return_code = exec_remote_command_host(self.host, script, output)
        return return_code, output

    def start_database(self):
        return self._execute_init_script('start')

    def stop_database(self):
        return self._execute_init_script('stop')

    def __is_instance_status(self, expected):
        for _ in range(CHECK_ATTEMPTS):
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

    @property
    def is_up(self):
        return self.__is_instance_status(True)

    @property
    def is_down(self):
        return self.__is_instance_status(False)

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


class Start(DatabaseStep):

    def __unicode__(self):
        return "Starting database..."

    @property
    def undo_klass(self):
        return Stop

    def do(self):
        if not self.is_valid:
            return

        return_code, output = self.start_database()
        if return_code != 0 and not self.is_up:
            raise EnvironmentError(
                'Could not start database {}: {}'.format(return_code, output)
            )

    def undo(self):
        self.undo_klass(self.instance).do()


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
            if not self.check_replication_ok(instance):
                raise ReplicationNotRunningError


class CheckIsUp(DatabaseStep):

    def __unicode__(self):
        return "Checking database is up..."

    def do(self):
        if not self.instance.is_database:
            return

        if not self.is_up:
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


class ValidateOplogSizeValue(DatabaseStep):

    def __unicode__(self):
        return "Validating oplog Size value..."

    def do(self):
        from physical.models import DatabaseInfraParameter
        oplog = DatabaseInfraParameter.objects.get(
            databaseinfra=self.infra,
            parameter__name='oplogSize')
        oplogsize = oplog.value
        error = 'BadValue oplogSize {}. Must be integer and greater than 0.'.format(oplogsize)
        try:
            oplogsize = int(oplogsize)
        except ValueError:
            raise EnvironmentError(error)

        if oplogsize <= 0:
            raise EnvironmentError(error)


class SetSlave(DatabaseStep):

    def __unicode__(self):
        return "Setting slaves..."

    @property
    def is_valid(self):
        return self.instance.is_database

    @property
    def master(self):
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

        database.pin_task(self.creating.task)

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
