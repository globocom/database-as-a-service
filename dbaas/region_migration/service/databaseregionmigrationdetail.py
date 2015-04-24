# -*- coding: utf-8 -*-
from django_services import service
from ..models import DatabaseRegionMigrationDetail


class DatabaseRegionMigrationDetailService(service.CRUDService):
    model_class = DatabaseRegionMigrationDetail
