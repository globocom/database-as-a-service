from mock import patch
from unittest import TestCase
from api.task import TaskSerializer
from logical.models import Database, DatabaseHistory
from logical.tests.factory import DatabaseFactory, DatabaseHistoryFactory


class GetDatabaseTestCase(TestCase):
    def setUp(self):
        self.serializer = TaskSerializer()
        self.fake_task = type('FakeTask', (object,), {})
        self.fake_task.object_class = Database._meta.db_table
        self.fake_task.object_id = 999

    def test_object_class_return_none(self):
        self.fake_task.object_class = 'other_class'
        self.assertFalse(self.serializer.get_database(self.fake_task))

    @patch.object(Database, 'objects')
    def test_object_make_dict_from_model(self, objects_mock):
        fake_database = DatabaseFactory.build(
            name='test_fake_database',
        )
        fake_database.environment.name = '__test__ fake env'
        fake_database.databaseinfra.engine.version = 'v1.2.3'
        fake_database.databaseinfra.engine.engine_type.name = '__test__ fake engine'
        objects_mock.select_related().get.return_value = fake_database

        database_info = self.serializer.get_database(self.fake_task)

        self.assertEqual(database_info.get('name'), 'test_fake_database')
        self.assertEqual(database_info.get('environment'), '__test__ fake env')
        self.assertEqual(database_info.get('engine'), '__test__ fake engine v1.2.3')

    @patch.object(Database, 'objects')
    @patch.object(DatabaseHistory, 'objects')
    def test_model_not_found(self, history_obj_mock, database_obj_mock):
        database_obj_mock.select_related().get.side_effect = Database.DoesNotExist
        history_obj_mock.get.side_effect = DatabaseHistory.DoesNotExist

        database_info = self.serializer.get_database(self.fake_task)

        self.assertFalse(database_info)

    @patch.object(Database, 'objects')
    @patch.object(DatabaseHistory, 'objects')
    def test_make_dict_from_history(self, history_obj_mock, database_obj_mock):
        database_obj_mock.select_related().get.side_effect = Database.DoesNotExist
        fake_history = DatabaseHistoryFactory.build(
            name='test_fake_database',
            environment='__test__ fake env',
            engine='__test__ fake engine v1.2.3'
        )
        history_obj_mock.get.return_value = fake_history

        database_info = self.serializer.get_database(self.fake_task)

        self.assertEqual(database_info.get('name'), 'test_fake_database')
        self.assertEqual(database_info.get('environment'), '__test__ fake env')
        self.assertEqual(database_info.get('engine'), '__test__ fake engine v1.2.3')
