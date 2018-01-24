# -*- coding: utf-8 -*-
import logging
from workflow.steps.util.database import DatabaseStep
from util import exec_remote_command_host

LOG = logging.getLogger(__name__)


class MySQLDatabaseStep(DatabaseStep):

    def do(self):
        raise NotImplementedError

    def execute_script(self, script):
        output = {}
        return_code = exec_remote_command_host(
            self.host, script, output
        )
        if return_code != 0:
            raise Exception(str(output))


class UpgradeMySQL(MySQLDatabaseStep):

    def __unicode__(self):
        return "Executing mysql_upgrade command..."

    def do(self):
        script = "mysql_upgrade -h{} -P{} -u{} -p{}".format(
            self.instance.address, self.instance.port,
            self.infra.user, self.infra.password,
        )
        self.execute_script(script)


class SetFilePermission(MySQLDatabaseStep):

    def __unicode__(self):
        return "Setting data permission..."

    def do(self):
        script = """chown mysql:mysql /data
        chown -R mysql:mysql /data/*
        """
        self.execute_script(script)


class SkipSlaveStart(MySQLDatabaseStep):

    def __unicode__(self):
        return "Skip slave start..."

    def do(self):

        if not self.infra.plan.is_ha:
            return

        script = "sed -e 's/^#skip_slave_start/skip_slave_start/' -i /etc/my.cnf"
        self.execute_script(script)

class DoNotSkipSlaveStart(MySQLDatabaseStep):

    def __unicode__(self):
        return "Do not skip slave start..."

    def do(self):

        if not self.infra.plan.is_ha:
            return

        script = "sed -e 's/^skip_slave_start/#skip_slave_start/' -i /etc/my.cnf"
        self.execute_script(script)
