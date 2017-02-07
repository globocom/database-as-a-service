# -*- coding: utf-8 -*-
from base import BaseTopology, STOP_RESIZE_START


class BaseMongoDB(BaseTopology):
    def deploy_first_steps(self):
        return (
            'workflow.steps.util.deploy.build_databaseinfra.BuildDatabaseInfra',
            'workflow.steps.mongodb.deploy.create_virtualmachines.CreateVirtualMachine',
            'workflow.steps.util.deploy.create_dns.CreateDns',
            'workflow.steps.util.deploy.create_nfs.CreateNfs',
            'workflow.steps.mongodb.deploy.init_database.InitDatabaseMongoDB',
            'workflow.steps.util.deploy.config_backup_log.ConfigBackupLog',
            'workflow.steps.util.deploy.check_database_connection.CheckDatabaseConnection',
            'workflow.steps.util.deploy.check_dns.CheckDns',
            'workflow.steps.util.deploy.start_monit.StartMonit',
        )

    def deploy_last_steps(self):
        return (
            'workflow.steps.util.deploy.build_database.BuildDatabase',
            'workflow.steps.util.deploy.create_log.CreateLog',
            'workflow.steps.util.deploy.check_database_binds.CheckDatabaseBinds',
        )

    def get_clone_steps(self):
        return self.deploy_first_steps() + self.deploy_last_steps() + (
            'workflow.steps.util.clone.clone_database.CloneDatabase',
            'workflow.steps.util.resize.check_database_status.CheckDatabaseStatus',
        ) + self.monitoring_steps()

    def get_resize_steps(self):
        return (
            ('workflow.steps.util.resize.stop_database.StopDatabase',) +
            STOP_RESIZE_START +
            ('workflow.steps.util.resize.start_database.StartDatabase',
             'workflow.steps.util.resize.start_agents.StartAgents',
             'workflow.steps.util.resize.check_database_status.CheckDatabaseStatus',
             )
        )


class MongoDBSingle(BaseMongoDB):

    def get_upgrade_steps_extra(self):
        return (
            'workflow.steps.mongodb.upgrade.vm.ChangeBinaryTo32',
            'workflow.steps.util.upgrade.database.Start',
            'workflow.steps.util.upgrade.database.CheckIsUp',
            'workflow.steps.util.upgrade.database.Stop',
            'workflow.steps.util.upgrade.database.CheckIsDown',
            'workflow.steps.mongodb.upgrade.vm.ChangeBinaryTo34',
        ) + super(MongoDBSingle, self).get_upgrade_steps_extra()


class MongoDBReplicaset(BaseMongoDB):

    def get_upgrade_steps_extra(self):
        return (
            'workflow.steps.mongodb.upgrade.vm.ChangeBinaryTo32',
        ) + super(MongoDBReplicaset, self).get_upgrade_steps_extra()

    def get_upgrade_steps_final(self):
        return [
            (
                'workflow.steps.util.upgrade.vm.ChangeMaster',
                'workflow.steps.util.upgrade.database.Stop',
                'workflow.steps.util.upgrade.database.CheckIsDown',
                'workflow.steps.mongo.upgrade.vm.ChangeBinaryTo34',
                'workflow.steps.util.upgrade.database.Start',
                'workflow.steps.util.upgrade.database.CheckIsUp',
            ),
        ] + super(MongoDBReplicaset, self).get_upgrade_steps_final()
