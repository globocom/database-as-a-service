# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import service
from ..models import Database
from base.engine.factory import EngineFactory


class DatabaseService(service.CRUDService):
    model_class = Database

    def get_engine(self, database):
        return EngineFactory.factory(database.instance)

    def create(self, database):
        super(DatabaseService, self).create(database)

        engine = self.get_engine(database)
        engine.create_database(database)

    def update(self, database):
        super(DatabaseService, self).update(database)
        # FIXME?? How can I change the name? or Instance?

    def delete(self, database):
        super(DatabaseService, self).delete(database)

        engine = self.get_engine(database)
        engine.remove_database(database)
