# -*- coding: utf-8 -*-
from workflow.steps.util.database import DatabaseStep
from workflow.steps.util import test_bash_script_error
from workflow.steps.mongodb.util import build_add_replica_set_member_script
from workflow.steps.mongodb.util import build_remove_read_only_replica_set_member_script


class DatabaseReplicaSet(DatabaseStep):

    def __init__(self, instance):
        super(DatabaseReplicaSet, self).__init__(instance)
        self.host_address = self.host.address

    @property
    def script_variables(self):
        variables = {
            'CONNECT_ADMIN_URI': self.driver.get_admin_connection(),
            'HOSTADDRESS': self.host_address,
            'PORT': self.instance.port,
            'REPLICA_ID': self.driver.get_max_replica_id() + 1
        }
        return variables


class AddInstanceToReplicaSet(DatabaseReplicaSet):

    def __unicode__(self):
        return "Adding instance to Replica Set..."

    @property
    def base_script(self):
        return build_add_replica_set_member_script(
            self.infra.engine.version, self.instance.read_only
        )

    def do(self):
        script = test_bash_script_error()
        script += self.base_script
        self._execute_script(self.script_variables, script)

    def undo(self):
        remove = RemoveInstanceFromReplicaSet(self.instance)
        remove.host_address = self.host_address
        remove.do()


class RemoveInstanceFromReplicaSet(DatabaseReplicaSet):

    def __unicode__(self):
        return "Removing instance from Replica Set..."

    def __init__(self, instance):
        super(DatabaseReplicaSet, self).__init__(instance)
        self.host_address = self.instance.hostname.address

    def do(self):
        script = test_bash_script_error()
        script += build_remove_read_only_replica_set_member_script()
        self._execute_script(self.script_variables, script)

    def undo(self):
        add = AddInstanceToReplicaSet(self.instance)
        add.host_address = self.host_address
        add.do()
