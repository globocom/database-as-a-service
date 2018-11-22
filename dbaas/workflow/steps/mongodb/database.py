# -*- coding: utf-8 -*-
from workflow.steps.util.database import DatabaseStep
from workflow.steps.util import test_bash_script_error
from workflow.steps.mongodb.util import build_add_replica_set_member_script
from workflow.steps.mongodb.util import build_remove_read_only_replica_set_member_script
from workflow.steps.mongodb.util import build_change_priority_script


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
            self.infra.engine.version, self.instance.read_only,
            not self.instance.is_database
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


class SetNotEligible(DatabaseReplicaSet):

    def __unicode__(self):
        return "Set instance not eligible to be master..."

    def __init__(self, instance):
        super(SetNotEligible, self).__init__(instance)
        self.priority = 0

    @property
    def index(self):
        all_instances = list(self.infra.instances.all())
        return all_instances.index(self.instance)

    @property
    def script_variables(self):
        variables = {
            'CONNECT_ADMIN_URI': self.driver.get_admin_connection(),
            'INDEX': self.index,
            'PRIORITY': self.priority
        }
        return variables

    def do(self):
        script = test_bash_script_error()
        script += build_change_priority_script()
        self._execute_script(self.script_variables, script)

    def undo(self):
        self.priority = 1
        self.do()
