# -*- coding: utf-8 -*-
from workflow.steps.util.base import BaseInstanceStep
from dbaas_aclapi.tasks import replicate_acl_for


class ACLStep(BaseInstanceStep):

    def __init__(self, instance):
        super(ACLStep, self).__init__(instance)
        self.databaseinfra = self.instance.databaseinfra
        self.database = self.databaseinfra.databases.first()

    def do(self):
        raise NotImplementedError

    def undo(self):
        pass


class ReplicateAcls(ACLStep):

    def __unicode__(self):
        return "Replicating acls ..."

    def do(self):
        replicate_acl_for(
            database=self.database,
            old_ip=source_instance.address,
            new_ip=self.instance.address)
