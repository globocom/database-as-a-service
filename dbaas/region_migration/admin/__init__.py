# -*- coding:utf-8 -*-
from django.contrib import admin
from ..models import DatabaseRegionMigration
from .databaseregionmigration import DatabaseRegionMigrationAdmin

admin.site.register(DatabaseRegionMigration, DatabaseRegionMigrationAdmin)
