# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from physical.tests import factory as factory_physical


class InstanceHelper(object):

    @staticmethod
    def check_instance_is_master(instance):
        """
            Method for mock the real check_instance_is_master.
            This method return master if the last digit minus 1 of address
            is divisible by 2

            Ex. Address = '127.0.0.1' the last char is 1. Now subtract 1 and we
                have 0. Now check if 0 is divisible by 2. This case return True

            Ex. Address = '127.0.0.2' the last char is 2. Now subtract 1 and we
                have 1. Now check if 1 is divisible by 2. This case return False

            Ex. Address = '127.0.0.3' the last char is 3. Now subtract 1 and we
                have 2. Now check if 2 is divisible by 2. This case return True
        """

        n = int(instance.address.split('.')[-1]) - 1

        return n % 2 == 0

    @staticmethod
    def create_instances_by_quant(infra, port=3306, qt=1, total_size_in_bytes=50,
                                  used_size_in_bytes=25, instance_type=1):
        """
            Helper create instances by quantity
        """
        def _create(n):
            return factory_physical.InstanceFactory(
                databaseinfra=infra,
                address='127.7{0}.{1}.{1}'.format(infra.id, n), port=port,
                instance_type=instance_type,
                total_size_in_bytes=total_size_in_bytes,
                used_size_in_bytes=used_size_in_bytes
            )

        return map(_create, range(1, qt + 1))
