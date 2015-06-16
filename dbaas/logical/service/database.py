# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django_services import service
from ..models import Database
from drivers import factory_for


class DatabaseService(service.CRUDService):
    model_class = Database

    def get_engine(self, database):
        return factory_for(database.databaseinfra)

    def create(self, database):
        super(DatabaseService, self).create(database)

    def update(self, database):
        super(DatabaseService, self).update(database)

    def delete(self, database):
        super(DatabaseService, self).delete(database)
