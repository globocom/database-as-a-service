# -*- coding: utf-8 -*-
from __future__ import absolute_import
from mock import patch

from django.test import TestCase
from django.core import mail

from account.tests.factory import TeamFactory
from logical.tests.factory import DatabaseFactory
from system.models import Configuration
from notification.tasks import database_notification_for_team
from dbaas.tests.helpers import InstanceHelper


class BaseTestCase(object):

    engine_name = ''
    port = None
    replication_topology_class_path = None
    instance_helper = InstanceHelper
    instance_quantity = 1
    instance_type = 1

    def setUp(self):
        self.team = TeamFactory()
        self.threshold_database_notification = Configuration(
            name='threshold_database_notification', value=70,
            description='Threshold infra notification'
        )
        self.threshold_database_notification.save()
        self.new_user_notify_email = Configuration(
            name='new_user_notify_email', value='me@email.com',
            description='New user notify e-mail'
        )
        self.new_user_notify_email.save()

        self.database_big = DatabaseFactory(
            databaseinfra__engine__engine_type__name=self.engine_name,
        )
        self.database_big.team = self.team
        self.database_big.save()

        self.infra_big = self.database_big.databaseinfra
        self.infra_big.plan.replication_topology.class_path = self.replication_topology_class_path
        self.infra_big.plan.replication_topology.save()
        self.infra_big.save()

        self.database_small = DatabaseFactory(
            databaseinfra__engine__engine_type__name=self.engine_name
        )
        self.database_small.team = self.team
        self.database_small.save()

        self.infra_small = self.database_small.databaseinfra
        self.infra_small.plan.replication_topology.class_path = self.replication_topology_class_path
        self.infra_small.plan.replication_topology.save()
        self.infra_small.save()

        self.instance_helper.create_instances_by_quant(
            qt=self.instance_quantity, infra=self.infra_big,
            total_size_in_bytes=10000, used_size_in_bytes=9900,
            port=self.port, instance_type=self.instance_type
        )
        self.instance_helper.create_instances_by_quant(
            qt=self.instance_quantity, infra=self.infra_small,
            total_size_in_bytes=10000, used_size_in_bytes=1900,
            port=self.port, instance_type=self.instance_type
        )

    def test_team_can_receive_notification(self, check_master_mock):
        database_notification_for_team(team=self.team)
        self.assertEqual(len(mail.outbox), 2)

    def test_team_do_not_want_receive_notification(self, check_master_mock):
        self.database_big.subscribe_to_email_events = False
        self.database_big.save()

        database_notification_for_team(team=self.team)
        self.assertEqual(len(mail.outbox), 0)


@patch('drivers.mysqldb.MySQL.check_instance_is_master',
        side_effect=InstanceHelper.check_instance_is_master)
class MySQLSingleTestCase(BaseTestCase, TestCase):

    engine_name = 'mysql'
    port = 3306
    replication_topology_class_path = 'drivers.replication_topologies.mysql.MySQLSingle'


@patch('drivers.mysqldb.MySQLFOXHA.check_instance_is_master',
        side_effect=InstanceHelper.check_instance_is_master)
class MySQLFoxHATestCase(BaseTestCase, TestCase):

    engine_name = 'mysql'
    port = 3306
    replication_topology_class_path = 'drivers.replication_topologies.mysql.MySQLFoxHA'
    instance_quantity = 2


@patch('drivers.mongodb.MongoDB.check_instance_is_master',
        side_effect=InstanceHelper.check_instance_is_master)
class MongoDBSingleTestCase(BaseTestCase, TestCase):

    engine_name = 'mongodb'
    port = 27017
    replication_topology_class_path = 'drivers.replication_topologies.mongodb.MongoDBSingle'
    instance_type = 2


@patch('drivers.mongodb.MongoDBReplicaSet.check_instance_is_master',
        side_effect=InstanceHelper.check_instance_is_master)
class MongoDBReplicasetTestCase(BaseTestCase, TestCase):

    engine_name = 'mongodb'
    port = 27017
    replication_topology_class_path = 'drivers.replication_topologies.mongodb.MongoDBReplicaset'
    instance_type = 2
    instance_quantity = 2


@patch('drivers.redis.Redis.check_instance_is_master',
        side_effect=InstanceHelper.check_instance_is_master)
class RedisSingleTestCase(BaseTestCase, TestCase):

    engine_name = 'redis'
    port = 6379
    replication_topology_class_path = 'drivers.replication_topologies.redis.RedisSingle'
    instance_type = 4


@patch('drivers.redis.RedisSentinel.check_instance_is_master',
        side_effect=InstanceHelper.check_instance_is_master)
class RedisSentinelTestCase(BaseTestCase, TestCase):

    engine_name = 'redis'
    port = 6379
    replication_topology_class_path = 'drivers.replication_topologies.redis.RedisSentinel'
    instance_type = 4
    instance_quantity = 2


@patch('drivers.redis.RedisCluster.check_instance_is_master',
        side_effect=InstanceHelper.check_instance_is_master)
class RedisClusterTestCase(BaseTestCase, TestCase):

    engine_name = 'redis'
    port = 6379
    replication_topology_class_path = 'drivers.replication_topologies.redis.RedisCluster'
    instance_type = 4
    instance_quantity = 6
