from django.test import TestCase
import logging
import re
from ..util import factory_arguments_for_task
from logical.tests.factory import DatabaseFactory
from physical.tests.factory import OfferingFactory
from account.tests.factory import UserFactory
from .factory import DatabaseBindFactory


class ArgumentsTestCase(TestCase):

    def setUp(self):
        database = DatabaseFactory()

        self.keys = (
            'notification.tasks.create_database',
            'notification.tasks.resize_database',
            'notification.tasks.database_disk_resize',
            'backup.tasks.restore_snapshot',
            'notification.tasks.destroy_database',
            'notification.tasks.clone_database',
            'dbaas_services.analyzing.tasks.analyze.analyze_databases',
            'notification.tasks.upgrade_mongodb_24_to_30',
            'dbaas_aclapi.tasks.unbind_address_on_database',
            'dbaas_aclapi.tasks.bind_address_on_database',
            'arguments.test_not_existent.there_is_no_class_for_this_task',
        )

        self.args = {
            'name': database.name,
            'database': database,
            'environment': database.environment,
            'project': database.project,
            'plan': database.databaseinfra.plan,
            'offering': OfferingFactory(),
            'disk_offering': database.databaseinfra.disk_offering,
            'user': UserFactory(),
            'origin_database': database,
            'clone_name': 'clone_{}'.format(database.name),
            'database_bind': DatabaseBindFactory(),
        }

        # Pattern:      Name of the argument: value of argument
        self.pattern = "[A-Z0-9][A-Za-z0-9_\- ]*[:][\s][A-Za-z0-9_\- ]+"

    def test_arguments_factory(self):
        for key in self.keys:
            args_list = factory_arguments_for_task(key, self.args)
            for arg in args_list:
                self.assertIsNotNone(
                    re.match(self.pattern, arg),
                    msg="Testing argument {} for task {}.".format(arg, key)
                )
