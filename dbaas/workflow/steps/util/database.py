# -*- coding: utf-8 -*-
from time import sleep
from dbaas_cloudstack.models import HostAttr
from workflow.steps.util.restore_snapshot import use_database_initialization_script
from util import build_context_script, exec_remote_command
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


class CheckIsDown(DatabaseStep):

    def __unicode__(self):
        return "Checking database is down..."

    def do(self):
        if not self.is_down:
            raise EnvironmentError('Database is up, should be down')
