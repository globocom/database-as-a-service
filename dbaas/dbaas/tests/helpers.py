# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from physical.tests.factory import InstanceFactory


class UsedAndTotalValidator(object):

    @staticmethod
    def assertEqual(a, b):
        assert a == b, "{} NOT EQUAL {}".format(a, b)

    @classmethod
    def instances_sizes(cls, instances=None, expected_used_size=40, expected_total_size=90):
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
    def check_instance_is_master(instance):
        """
            Method for mock the real check_instance_is_master.
        """

        quantity_of_masters = instance.databaseinfra.instances.count() / 2

        return instance.id in (instance.databaseinfra.instances.values_list(
                               'id', flat=True)[quantity_of_masters:])

    @staticmethod
    def create_instances_by_quant(infra, port=3306, qt=1, total_size_in_bytes=50,
                                  used_size_in_bytes=25, instance_type=1,
                                  base_address='127', hostname=None):
        """
            Helper create instances by quantity
        """
        def _create(n):
            extra_params = dict(**{'hostname': hostname} if hostname else {})
            return InstanceFactory(
                databaseinfra=infra,
                address='{0}.7{1}.{2}.{2}'.format(base_address, infra.id, n), port=port,
                instance_type=instance_type,
                total_size_in_bytes=total_size_in_bytes,
                used_size_in_bytes=used_size_in_bytes,
                **extra_params
            )

        return map(_create, range(1, qt + 1))
