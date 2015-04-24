# -*- coding: utf-8 -*-
from django_services import service
from ..models import DatabaseRegionMigration


class DatabaseRegionMigrationService(service.CRUDService):
    model_class = DatabaseRegionMigration
