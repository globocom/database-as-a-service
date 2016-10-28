# -*- coding: utf-8 -*-
from django_services import service
from ..models import DatabaseFlipperFoxMigrationDetail


class DatabaseFlipperFoxMigrationDetailService(service.CRUDService):
    model_class = DatabaseFlipperFoxMigrationDetail
