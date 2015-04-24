# -*- coding:utf-8 -*-
from django.contrib import admin
from ..models import DatabaseRegionMigration, DatabaseRegionMigrationDetail
from .databaseregionmigration import DatabaseRegionMigrationAdmin
from .databaseregionmigrationdetail import DatabaseRegionMigrationDetailAdmin

admin.site.register(DatabaseRegionMigration, DatabaseRegionMigrationAdmin)
admin.site.register(DatabaseRegionMigrationDetail,
                    DatabaseRegionMigrationDetailAdmin)
