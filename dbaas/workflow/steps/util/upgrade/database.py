# -*- coding: utf-8 -*-
from time import sleep
from util import full_stack
from workflow.exceptions.error_codes import DBAAS_0004
from workflow.steps.util.restore_snapshot import use_database_initialization_script
from workflow.steps.util.base import BaseInstanceStep


CHECK_SECONDS = 10
CHECK_ATTEMPTS = 12


class DatabaseStep(BaseInstanceStep):

    def __init__(self, instance):
        super(DatabaseStep, self).__init__(instance)

        self.infra = self.instance.databaseinfra
        self.driver = self.infra.get_driver()

    def do(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError

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
            status = self.driver.check_status(instance=self.instance)
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


class Stop(DatabaseStep):

    def __unicode__(self):
        return "Stopping database..."

    def do(self):
        return_code, output = self.stop_database()
        if return_code != 0:
            return False, DBAAS_0004, '{}: {}'.format(return_code, output)

        return True, None, None

    def undo(self):
        return True, None, None


class Start(DatabaseStep):

    def __unicode__(self):
        return "Starting database..."

    def do(self):
        return_code, output = self.start_database()
        if return_code != 0:
            return False, DBAAS_0004, '{}: {}'.format(return_code, output)

        return True, None, None

    def undo(self):
        return True, None, None


class CheckIsUp(DatabaseStep):

    def __unicode__(self):
        return "Checking database is up..."

    def do(self):
        if self.is_up:
            return True, None, None
        return False, DBAAS_0004, 'Database is down'

    def undo(self):
        return True, None, None


class CheckIsDown(DatabaseStep):

    def __unicode__(self):
        return "Checking database is down..."

    def do(self):
        if self.is_down:
            return True, None, None
        return False, DBAAS_0004, 'Database is up'

    def undo(self):
        return True, None, None
