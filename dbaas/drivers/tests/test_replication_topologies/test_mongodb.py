# -*- coding: utf-8 -*-
from drivers.replication_topologies.base import STOP_RESIZE_START
from drivers.replication_topologies.mongodb import MongoDBReplicaset
from drivers.replication_topologies.mongodb import MongoDBSingle
from drivers.tests.test_replication_topologies import AbstractReplicationTopologySettingsTestCase


class AbstractBaseMondodbTestCase(AbstractReplicationTopologySettingsTestCase):

    def _get_deploy_first_settings(self):
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

    def _get_deploy_last_settings(self):
        return (
            'workflow.steps.util.deploy.build_database.BuildDatabase',
            'workflow.steps.util.deploy.create_log.CreateLog',
            'workflow.steps.util.deploy.check_database_binds.CheckDatabaseBinds',
        )

    def _get_clone_settings(self):
        return self._get_deploy_first_settings() + self._get_deploy_last_settings() + (
            'workflow.steps.util.clone.clone_database.CloneDatabase',
            'workflow.steps.util.resize.check_database_status.CheckDatabaseStatus',
        ) + self._get_monitoring_settings()

    def _get_resize_settings(self):
        return (
            ('workflow.steps.util.resize.stop_database.StopDatabase',) +
            STOP_RESIZE_START +
            ('workflow.steps.util.resize.start_database.StartDatabase',
             'workflow.steps.util.resize.start_agents.StartAgents',
             'workflow.steps.util.resize.check_database_status.CheckDatabaseStatus',
             )
        )


class TestMongoDBSingle(AbstractBaseMondodbTestCase):

    def _get_replication_topology_driver(self):
        return MongoDBSingle()

    def _get_upgrade_steps_extra(self):
        return (
                   'workflow.steps.mongodb.upgrade.vm.ChangeBinaryTo32',
                   'workflow.steps.util.upgrade.database.Start',
                   'workflow.steps.util.upgrade.database.CheckIsUp',
                   'workflow.steps.util.upgrade.database.Stop',
                   'workflow.steps.util.upgrade.database.CheckIsDown',
                   'workflow.steps.mongodb.upgrade.vm.ChangeBinaryTo34',
               ) + super(TestMongoDBSingle, self)._get_upgrade_steps_extra()


class TestMongoDBReplicaset(AbstractBaseMondodbTestCase):

    def _get_replication_topology_driver(self):
        return MongoDBReplicaset()
