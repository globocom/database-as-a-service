# -*- coding: utf-8 -*-
from workflow.steps.util.database import DatabaseStep
from workflow.steps.util import test_bash_script_error
from workflow.steps.mongodb.util import build_add_replica_set_member_script
from workflow.steps.mongodb.util import build_remove_read_only_replica_set_member_script
from workflow.steps.mongodb.util import build_change_priority_script


class MongoDBDatabaseStep(DatabaseStep):
    @property
    def ssl_conn_string(self):
        if self.infra.ssl_mode == self.infra.REQUIRETLS:
            return '--tls --tlsCAFile {}'.format(
                self.root_certificate_file)
        else:
            return ''


class DatabaseReplicaSet(MongoDBDatabaseStep):

    def __init__(self, instance):
        super(DatabaseReplicaSet, self).__init__(instance)

        self._host_address = None

    @property
    def host_address(self):
        if self._host_address:
            return self._host_address
        return self.host and self.host.address

    @host_address.setter
    def host_address(self, host_address):
        self._host_address = host_address

    @property
    def script_variables(self):
        variables = {
            'CONNECT_ADMIN_URI': self.driver.get_admin_connection(),
            'HOSTADDRESS': self.host_address,
            'PORT': self.instance.port,
            'REPLICA_ID': self.driver.get_max_replica_id() + 1,
            'SSL_CONN_STRING': self.ssl_conn_string,
        }
        return variables


class AddInstanceToReplicaSet(DatabaseReplicaSet):

    def __unicode__(self):
        return "Adding instance to Replica Set..."

    @property
    def base_script(self):
        return build_add_replica_set_member_script(
            self.infra.engine.version, self.instance.read_only,
            not self.instance.is_database
        )

    def do(self):
        script = test_bash_script_error()
        script += self.base_script
        self._execute_script(self.script_variables, script)

    def undo(self):
        if self.host_address:
            remove = RemoveInstanceFromReplicaSet(self.instance)
            remove.host_address = self.host_address
            remove.do()


class RemoveInstanceFromReplicaSet(DatabaseReplicaSet):

    def __unicode__(self):
        return "Removing instance from Replica Set..."

    def __init__(self, instance):
        super(DatabaseReplicaSet, self).__init__(instance)

        self._host_address = None

    @property
    def host_address(self):
        if self._host_address:
            return self._host_address
        return self.instance.hostname.address

    @host_address.setter
    def host_address(self, host_address):
        self._host_address = host_address

    def do(self):
        script = test_bash_script_error()
        script += build_remove_read_only_replica_set_member_script()
        self._execute_script(self.script_variables, script)

    def undo(self):
        add = AddInstanceToReplicaSet(self.instance)
        add.host_address = self.host_address
        add.do()


class SetNotEligible(DatabaseReplicaSet):

    def __unicode__(self):
        return "Set instance not eligible to be master..."

    def __init__(self, instance):
        super(SetNotEligible, self).__init__(instance)
        self.priority = 0

    @property
    def script_variables(self):
        if self.infra.ssl_mode == self.infra.REQUIRETLS:
            ssl_connect = '--tls --tlsCAFile {}'.format(
                self.root_certificate_file)
        else:
            ssl_connect = ''
        variables = {
            'CONNECT_ADMIN_URI': self.driver.get_admin_connection(),
            'HOST_ADDRESS': "{}:{}".format(self.instance.address, self.instance.port),
            'PRIORITY': self.priority,
            'SSL_CONN_STRING': ssl_connect,
        }
        return variables

    def do(self):
        script = test_bash_script_error()
        script += build_change_priority_script(len(self.infra.instances.all()))
        self._execute_script(self.script_variables, script)

    def undo(self):
        self.priority = 1
        self.do()

class RecreateMongoLogRotateScript(MongoDBDatabaseStep):
    def __unicode__(self):
        return "Recreating MongoDB log rotate script..."

    def do(self):
        from notification.scripts.script_mongo_log_rotate import (
            script_mongodb_rotate)
        script = script_mongodb_rotate % (
            self.ssl_conn_string, self.ssl_conn_string, self.ssl_conn_string)
        self._execute_script({}, script)

