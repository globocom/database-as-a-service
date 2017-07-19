# -*- coding: utf-8 -*-
from time import sleep
from dbaas_cloudstack.models import HostAttr
from workflow.steps.util.restore_snapshot import use_database_initialization_script
from util import build_context_script, exec_remote_command
from util import exec_remote_command_host
from workflow.steps.mongodb.util import build_change_oplogsize_script
from workflow.steps.util.base import BaseInstanceStep
import logging

LOG = logging.getLogger(__name__)

CHECK_SECONDS = 10
CHECK_ATTEMPTS = 12


class DatabaseStep(BaseInstanceStep):

    def __init__(self, instance):
        super(DatabaseStep, self).__init__(instance)

        self.infra = self.instance.databaseinfra
        self.driver = self.infra.get_driver()
        self.host = self.instance.hostname
        self.host_cs = HostAttr.objects.get(host=self.host)

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass

    def _execute_init_script(self, command):
        return use_database_initialization_script(
            self.infra, self.instance.hostname, command
        )

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
        return_code = exec_remote_command(
            self.host.address, self.host_cs.vm_user, self.host_cs.vm_password,
            final_script, output
        )

        if return_code != 0:
            raise EnvironmentError(
                'Could not execute replica script {}: {}'.format(
                    return_code, output
                )
            )


class Stop(DatabaseStep):

    def __unicode__(self):
        return "Stopping database..."

    def do(self):
        return_code, output = self.stop_database()
        if return_code != 0 and not self.is_down:
            raise EnvironmentError(
                'Could not stop database {}: {}'.format(return_code, output)
            )


class Start(DatabaseStep):

    def __unicode__(self):
        return "Starting database..."

    def do(self):
        return_code, output = self.start_database()
        if return_code != 0 and not self.is_up:
            raise EnvironmentError(
                'Could not start database {}: {}'.format(return_code, output)
            )

    def undo(self):
        return_code, output = self.stop_database()
        if return_code != 0 and not self.is_down:
            raise EnvironmentError(
                'Could not stop database {}: {}'.format(return_code, output)
            )


class StartSlave(DatabaseStep):

    def __unicode__(self):
        return "Starting slave..."

    def do(self):
        CheckIsUp(self.instance)
        self.driver.start_slave(instance=self.instance)


class CheckIsUp(DatabaseStep):

    def __unicode__(self):
        return "Checking database is up..."

    def do(self):
        if not self.is_up:
            raise EnvironmentError('Database is down, should be up')


class CheckIfSwitchMaster(DatabaseStep):
    def __unicode__(self):
        return "Checking if master was switched..."

    def do(self):
        for _ in range(CHECK_ATTEMPTS):
            master = self.driver.get_master_instance()
            if master and master != self.instance:
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

    def __is_os_process_running(self):
        script = "ps -ef | grep {} | grep -v grep | wc -l".format(
            self.process_name
        )

        for _ in range(CHECK_ATTEMPTS):
            output = {}
            return_code = exec_remote_command_host(
                self.host, script, output
            )
            if return_code != 0:
                raise Exception(str(output))
            processes = int(output['stdout'][0])
            if processes == 0:
                return False
            LOG.info("{} is runnig".format(self.process_name))
            sleep(CHECK_SECONDS)

        return True

    def do(self):
        if not self.is_down:
            raise EnvironmentError('Database is up, should be down')

        self.process_name = self.driver.get_database_process_name()
        if self.__is_os_process_running():
            raise EnvironmentError(
                '{} is running on server'.format(self.process_name)
            )


class DatabaseChangedParameters(DatabaseStep):

    def __init__(self, instance):
        super(DatabaseChangedParameters, self).__init__(instance)
        from physical.models import DatabaseInfraParameter

        self.reseted_parameters = DatabaseInfraParameter.get_databaseinfra_reseted_parameters(
            databaseinfra=self.finfra,
        )

        self.changed_parameters = DatabaseInfraParameter.get_databaseinfra_changed_parameters(
            databaseinfra=self.finfra,
        )


class ChangeDynamicParameters(DatabaseStep):

    def __unicode__(self):
        return "Changing dynamic database parameters..."

    def do(self):
        from physical.models import DatabaseInfraParameter
        changed_parameters = DatabaseInfraParameter.get_databaseinfra_changed_parameters(
            self.infra
        )
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

        reseted_parameters = DatabaseInfraParameter.get_databaseinfra_reseted_parameters(
            self.infra
        )
        for reseted_parameter in reseted_parameters:
            reseted_parameter.delete()

        changed_parameters = DatabaseInfraParameter.get_databaseinfra_changed_not_reseted_parameters(
            self.infra
        )
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
        return_code = exec_remote_command_host(
            self.host, script, output
        )
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
