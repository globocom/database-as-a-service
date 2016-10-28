# -*- coding: utf-8 -*-
from django_services import service
from ..models import DatabaseFlipperFoxMigration


class DatabaseFlipperFoxMigrationService(service.CRUDService):
    model_class = DatabaseFlipperFoxMigration
