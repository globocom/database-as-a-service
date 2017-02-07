# -*- coding: utf-8 -*-
from time import sleep
from django.db import transaction
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
        if self.instance not in self.driver.get_database_instances():
            return True

        for _ in range(CHECK_ATTEMPTS):
            try:
                status = self.driver.check_status(instance=self.instance)
            except:
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


class Stop(DatabaseStep):

    def __unicode__(self):
        return "Stopping database..."

    def do(self):
        return_code, output = self.stop_database()
        if return_code != 0:
            raise EnvironmentError(
                'Could not stop database {}: {}'.format(return_code, output)
            )


class Start(DatabaseStep):

    def __unicode__(self):
        return "Starting database..."

    def do(self):
        return_code, output = self.start_database()
        if return_code != 0:
            raise EnvironmentError(
                'Could not start database {}: {}'.format(return_code, output)
            )


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
