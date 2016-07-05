# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.test import TestCase
from django.contrib.admin.sites import AdminSite

from ..models import Plan, EngineType, Engine, ReplicationTopology
from ..admin.plan import PlanAdmin


class PlanTestCase(TestCase):

    def setUp(self):
        self.mysql_type = EngineType(name='MySQL')
        self.mysql_type.save()

        self.mysql_5_6 = Engine(
            engine_type=self.mysql_type, version='5.6'
        )
        self.mysql_5_6.save()

        self.mysql_5_7 = Engine(
            engine_type=self.mysql_type, version='5.7'
        )
        self.mysql_5_7.save()

        self.redis_type = EngineType(name='Redis')
        self.redis_type.save()

        self.redis_3_3 = Engine(
            engine_type=self.redis_type, version='3.3'
        )
        self.redis_3_3.save()

        self.foxha_topology = ReplicationTopology(name='FoxHA')
        self.foxha_topology.save()
        self.foxha_topology.engine.add(self.mysql_5_6)
        self.foxha_topology.engine.add(self.mysql_5_7)
        self.foxha_topology.save()

        self.flipper_topology = ReplicationTopology(name='Flipper')
        self.flipper_topology.save()
        self.flipper_topology.engine.add(self.mysql_5_6)
        self.flipper_topology.save()

        self.cluster_topology = ReplicationTopology(name='Cluster')
        self.cluster_topology.save()
        self.cluster_topology.engine.add(self.redis_3_3)
        self.cluster_topology.save()

    def tearDown(self):
        pass

    def test_context_replication_topologies(self):
        context = PlanAdmin(Plan, AdminSite())._add_replication_topologies_engines(None)
        self.assertIn('replication_topologies_engines', context)
        topologies = context['replication_topologies_engines']

        mysql_5_6 = topologies[str(self.mysql_5_6)]
        self.assertEqual(2, len(mysql_5_6))
        self.assertIn(self.foxha_topology, mysql_5_6)
        self.assertIn(self.flipper_topology, mysql_5_6)

        mysql_5_7 = topologies[str(self.mysql_5_7)]
        self.assertEqual(1, len(mysql_5_7))
        self.assertIn(self.foxha_topology, mysql_5_7)

        redis_3_3 = topologies[str(self.redis_3_3)]
        self.assertEqual(1, len(redis_3_3))
        self.assertIn(self.cluster_topology, redis_3_3)
