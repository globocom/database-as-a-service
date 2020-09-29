# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from mock import patch, MagicMock

from physical.tests.factory import InstanceFactory
from model_mommy import mommy
from physical.models import EngineType


class UsedAndTotalValidator(object):

    @staticmethod
    def assertEqual(a, b):
        assert a == b, "{} NOT EQUAL {}".format(a, b)

    @classmethod
    def instances_sizes(cls, instances=None, expected_used_size=40,
                        expected_total_size=90):
        for instance in instances:
            cls.assertEqual(instance.used_size_in_bytes, expected_used_size)
            cls.assertEqual(instance.total_size_in_bytes, expected_total_size)


class InstanceHelper(object):

    model = InstanceFactory.FACTORY_FOR
    quantity_of_masters = 1

    @classmethod
    def kill_instances(cls, instances):
        for instance in instances:
            instance.status = cls.model.DEAD
            instance.save()

    @staticmethod
    def change_instances_type(instances, instance_type):
        for instance in instances:
            instance.instance_type = instance_type
            instance.save()

    @staticmethod
    def check_instance_is_master(instance, default_timeout=False):
        """
            Method for mock the real check_instance_is_master.
        """

        quantity_of_masters = instance.databaseinfra.instances.count() / 2

        return instance.id in (instance.databaseinfra.instances.values_list(
                               'id', flat=True)[quantity_of_masters:])

    @staticmethod
    def create_instances_by_quant(infra, port=3306, qt=1,
                                  total_size_in_bytes=50,
                                  used_size_in_bytes=25, instance_type=1,
                                  base_address='127', hostname=None):
        """
            Helper create instances by quantity
        """
        def _create(n):
            extra_params = dict(**{'hostname': hostname} if hostname else {})
            return InstanceFactory(
                databaseinfra=infra,
                address='{0}.7{1}.{2}.{2}'.format(
                    base_address, infra.id, n
                ),
                port=port,
                instance_type=instance_type,
                total_size_in_bytes=total_size_in_bytes,
                used_size_in_bytes=used_size_in_bytes,
                **extra_params
            )

        return map(_create, range(1, qt + 1))


class DatabaseHelper(object):
    @staticmethod
    @patch('logical.models.Database.automatic_create_first_credential',
           MagicMock())
    def create(**kwargs):
        if 'databaseinfra' not in kwargs:
            kwargs['databaseinfra'] = InfraHelper.create()

        driver = kwargs['databaseinfra'].get_driver()
        module_path = "{}.{}.create_database".format(
            driver.__class__.__module__,
            driver.__class__.__name__
        )
        with patch(module_path, MagicMock()):
            return mommy.make(
                'Database', **kwargs
            )


class PlanHelper(object):
    engine_map = {
        'mysql_single': {
            'class_path': 'drivers.replication_topologies.mysql.MySQLSingle',
            'name': 'MySQL Single 5.7.25'
        }
    }
    @classmethod
    def create(cls, engine_name='mysql_single', *kwargs):
        """
            Engine must be: `NAME`_`TOPOLOGY_TYPE`
            Ex. mysql_single.The name of engine will be mysql and mysql_single
            will be used to get topology class_path and name. See `engine_map`
            class variable
        """
        if 'engine' not in kwargs:
            if engine_name not in cls.engine_map:
                raise Exception(
                    "Engine not mapped. Mapped engines are: {}".format(
                        ', '.join(cls.engine_map.keys())
                    )
                )
            engine_conf = cls.engine_map[engine_name]
            try:
                engine_type_name = engine_name.split('_')[0]
                engine_type = EngineType.objects.get(name=engine_type_name)
            except EngineType.DoesNotExist:
                engine_type = mommy.make('EngineType', name=engine_type_name)
            engine = mommy.make(
                'Engine', engine_type=engine_type
            )
            replication_topology = mommy.make(
                'ReplicationTopology',
                name=engine_conf['name'],
                class_path=engine_conf['class_path']
            )
        else:
            engine = kwargs.get('engine')
            replication_topology = mommy.make(
                'ReplicationTopology'
            )

        plan = mommy.make(
            'Plan', engine=engine,
            replication_topology=replication_topology
        )
        return engine_type, engine, replication_topology, plan


class InfraHelper(object):
    @staticmethod
    def create(engine_name='mysql_single', **kwargs):
        if 'plan' not in kwargs:
            _, _, _, kwargs['plan'] = PlanHelper.create(engine_name)
        return mommy.make_recipe('physical.databaseinfra', **kwargs)
